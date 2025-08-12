from typing import Dict, Tuple
import os

from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.services.auth_service import get_db, authenticate_user, create_access_token
from app.services.user_service import create_user as create_user_row
from app.services.transaction_service import get_transactions, create_transaction
from app.services.ml_task_service import send_task_to_queue
from shared.models.user import User
from shared.models.prediction import Prediction
from shared.models.transaction import Transaction
from shared.models.ml_model import MLModel

templates = Jinja2Templates(directory="app/templates")
web_router = APIRouter()

# ---------------- helpers ----------------

def current_user_by_cookie(db: Session, request: Request) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    from jose import jwt, JWTError
    from app.services.auth_service import SECRET_KEY, ALGORITHM
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return None
        return db.query(User).filter(User.username == username).first()
    except JWTError:
        return None


def _render_dashboard(request: Request, db: Session, user: User, **extra):
    txs = get_transactions(db, user.id)
    preds = (
        db.query(Prediction)
        .filter(Prediction.user_id == user.id)
        .order_by(Prediction.created_at.desc())
        .all()
    )
    models = db.query(MLModel).all()
    ctx = {"request": request, "user": user, "transactions": txs, "predictions": preds, "models": models}
    ctx.update(extra)
    return templates.TemplateResponse("dashboard.html", ctx)


def _split_valid_invalid(records: Dict):
    valid, invalid = {}, {}
    for k, v in records.items():
        if isinstance(v, (int, float)):
            valid[k] = float(v)
        else:
            invalid[k] = v
    return valid, invalid

# локальная линейная «модель» для TEST_MODE=1
FEATURE_ORDER = [s.strip() for s in os.getenv("FEATURE_ORDER", "feature1,feature2,feature3").split(",") if s.strip()]
try:
    WEIGHTS = [float(s.strip()) for s in os.getenv("WEIGHTS", "0.7,0.2,0.1").split(",") if s.strip()]
except ValueError:
    WEIGHTS = [0.7, 0.2, 0.1]
BIAS = float(os.getenv("BIAS", "0.0"))
if len(WEIGHTS) < len(FEATURE_ORDER):
    WEIGHTS = WEIGHTS + [0.0] * (len(FEATURE_ORDER) - len(WEIGHTS))
elif len(WEIGHTS) > len(FEATURE_ORDER):
    WEIGHTS = WEIGHTS[: len(FEATURE_ORDER)]


def _linear_predict(valid_input: Dict[str, float]) -> float:
    total = BIAS
    for name, w in zip(FEATURE_ORDER, WEIGHTS):
        total += float(valid_input.get(name, 0.0)) * w
    return total

# ---------------- routes ----------------

@web_router.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@web_router.get("/register")
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@web_router.post("/register")
def register(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    create_user_row(db, username=username, email=email, password=password)
    return RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)

@web_router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@web_router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error_message": "Неверные логин или пароль"}, status_code=400)
    token = create_access_token({"sub": user.username})
    resp = RedirectResponse(url="/web/dashboard", status_code=status.HTTP_302_FOUND)
    resp.set_cookie("access_token", token, httponly=True, samesite="Lax")
    return resp

@web_router.get("/logout")
def logout():
    """Удаляем cookie авторизации и отправляем на форму входа."""
    resp = RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)
    resp.delete_cookie("access_token")
    return resp

@web_router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = current_user_by_cookie(db, request)
    if not user:
        return RedirectResponse("/web/login", status_code=status.HTTP_302_FOUND)
    return _render_dashboard(request, db, user)

@web_router.post("/deposit")
def deposit(request: Request, amount: float = Form(...), db: Session = Depends(get_db)):
    user = current_user_by_cookie(db, request)
    if not user:
        return RedirectResponse("/web/login", status_code=status.HTTP_302_FOUND)
    if amount <= 0:
        return _render_dashboard(request, db, user, error_message="Сумма пополнения должна быть больше нуля")
    create_transaction(db, user_id=user.id, amount=amount, type="deposit")
    return _render_dashboard(request, db, user, info_message="Баланс успешно пополнен")

@web_router.post("/predict")
def predict_from_form(request: Request, model_id: int = Form(...), feature1: float = Form(...), feature2: float = Form(...), feature3: float = Form(...), db: Session = Depends(get_db)):
    """
    Если запрос пришёл из JS (Accept: application/json или ?ajax=1) — возвращаем JSON.
    Иначе ведём себя как раньше: рендерим дашборд.
    """
    user = current_user_by_cookie(db, request)
    if not user:
        if request.headers.get("accept") == "application/json" or request.query_params.get("ajax") == "1":
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        return RedirectResponse("/web/login", status_code=status.HTTP_302_FOUND)

    model = db.query(MLModel).filter(MLModel.id == model_id).first()
    if not model:
        if request.headers.get("accept") == "application/json" or request.query_params.get("ajax") == "1":
            return JSONResponse({"detail": "Модель не найдена"}, status_code=404)
        return _render_dashboard(request, db, user, error_message="Модель не найдена")

    price = float(model.price or 0.0)
    if user.balance < price:
        if request.headers.get("accept") == "application/json" or request.query_params.get("ajax") == "1":
            return JSONResponse({"detail": "Недостаточно кредитов для предсказания"}, status_code=400)
        return _render_dashboard(request, db, user, error_message="Недостаточно кредитов для предсказания")

    input_data = {"feature1": float(feature1), "feature2": float(feature2), "feature3": float(feature3)}
    valid, invalid = _split_valid_invalid(input_data)

    test_mode = os.getenv("TEST_MODE", "0") == "1"
    is_ajax = request.headers.get("accept") == "application/json" or request.query_params.get("ajax") == "1"

    if test_mode:
        # синхронный расчёт — вернём результат сразу
        y = _linear_predict(valid)
        prediction_value = f"{y:.4f}"
        user.balance -= price
        db.add(Transaction(user_id=user.id, amount=price, type="withdraw"))
        db.add(Prediction(user_id=user.id, model_id=model_id, prediction=prediction_value, cost=price))
        db.commit()
        if is_ajax:
            return JSONResponse({"status": "ok", "mode": "test", "prediction": prediction_value, "invalid": invalid or None, "balance": float(user.balance)})
        return _render_dashboard(request, db, user, info_message="Предсказание выполнено (TEST_MODE)", result={"prediction": prediction_value}, invalid_records=invalid or None)

    # асинхронно — ставим задачу в очередь и отвечаем, что приняли
    send_task_to_queue(user_id=user.id, model_id=model_id, input_data=valid, price=price)
    if is_ajax:
        return JSONResponse({"status": "accepted", "mode": "async"})
    return _render_dashboard(request, db, user, info_message="Задача отправлена на обработку. Результат появится в истории предсказаний.", invalid_records=invalid or None)

# -------- polling endpoint used ТОЛЬКО после отправки формы --------
@web_router.get("/poll")
def poll(request: Request, db: Session = Depends(get_db)):
    user = current_user_by_cookie(db, request)
    if not user:
        return JSONResponse({"authenticated": False}, status_code=401)

    last_pred = (
        db.query(Prediction)
        .filter(Prediction.user_id == user.id)
        .order_by(Prediction.id.desc())
        .first()
    )
    last_tx = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id)
        .order_by(Transaction.id.desc())
        .first()
    )
    # отдадим короткое резюме и данные для «без‑reload» вставки новой строки
    return JSONResponse({
        "authenticated": True,
        "balance": float(user.balance or 0.0),
        "last_prediction": {
            "id": int(last_pred.id) if last_pred else 0,
            "model_id": int(last_pred.model_id) if last_pred else None,
            "prediction": str(last_pred.prediction) if last_pred else None,
            "cost": float(last_pred.cost) if last_pred else None,
            "created_at": str(last_pred.created_at) if last_pred else None,
        } if last_pred else None,
        "last_transaction": {
            "id": int(last_tx.id) if last_tx else 0,
            "type": str(last_tx.type) if last_tx else None,
            "amount": float(last_tx.amount) if last_tx else None,
            "created_at": str(last_tx.created_at) if last_tx else None,
        } if last_tx else None,
    })
