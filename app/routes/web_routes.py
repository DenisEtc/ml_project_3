from typing import List, Dict, Tuple
from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.services.auth_service import get_db, authenticate_user, create_access_token
from app.services.user_service import create_user as create_user_row
from app.services.transaction_service import create_transaction, get_transactions
from shared.models.user import User
from shared.models.prediction import Prediction
from shared.models.ml_model import MLModel

templates = Jinja2Templates(directory="app/templates")
web_router = APIRouter()


def current_user_by_cookie(db: Session, request: Request) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    # простая дешифровка JWT без запроса к API
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


def _render_dashboard(request: Request, db: Session, user: User, **extra_context):
    txs = get_transactions(db, user.id)
    preds = (
        db.query(Prediction)
        .filter(Prediction.user_id == user.id)
        .order_by(Prediction.created_at.desc())
        .all()
    )
    models = db.query(MLModel).all()
    context = {
        "request": request,
        "user": user,
        "transactions": txs,
        "predictions": preds,
        "models": models,
    }
    context.update(extra_context)
    return templates.TemplateResponse("dashboard.html", context)


@web_router.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@web_router.get("/register")
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@web_router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    create_user_row(db, username=username, email=email, password=password)
    return RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)


@web_router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@web_router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, username, password)
    if not user:
        # мягкая ошибка: возвращаем форму логина с сообщением
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error_message": "Неверные логин или пароль"},
            status_code=400,
        )
    token = create_access_token({"sub": user.username})
    resp = RedirectResponse(url="/web/dashboard", status_code=status.HTTP_302_FOUND)
    resp.set_cookie("access_token", token, httponly=True, samesite="Lax")
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
        return _render_dashboard(
            request, db, user, error_message="Сумма пополнения должна быть больше нуля"
        )

    create_transaction(db, user_id=user.id, amount=amount, type="deposit")
    return _render_dashboard(
        request, db, user, info_message="Баланс успешно пополнен"
    )


# предикт из простой формы
@web_router.post("/predict")
def predict_from_form(
    request: Request,
    model_id: int = Form(...),
    feature1: float = Form(...),
    feature2: float = Form(...),
    feature3: float = Form(...),
    db: Session = Depends(get_db),
):
    user = current_user_by_cookie(db, request)
    if not user:
        return RedirectResponse("/web/login", status_code=status.HTTP_302_FOUND)

    model = db.query(MLModel).filter(MLModel.id == model_id).first()
    if not model:
        return _render_dashboard(request, db, user, error_message="Модель не найдена")

    price = float(model.price or 0.0)
    if user.balance < price:
        # КЛЮЧЕВАЯ ПРАВКА: вместо HTTPException — мягкое сообщение на дашборде
        return _render_dashboard(
            request, db, user, error_message="Недостаточно кредитов для предсказания"
        )

    # Выполним «предсказание» и списание (демо-логика)
    pred = Prediction(user_id=user.id, model_id=model_id, prediction="0.42", cost=price)
    db.add(pred)

    user.balance -= price
    db.add(user)

    from shared.models.transaction import Transaction
    db.add(Transaction(user_id=user.id, amount=price, type="withdraw"))
    db.commit()

    return _render_dashboard(
        request, db, user, info_message="Предсказание выполнено", result={"prediction": pred.prediction}
    )
