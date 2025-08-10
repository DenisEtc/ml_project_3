from typing import List, Dict, Tuple
import json

from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
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
    # очень простой способ – запросить /users/me через заголовок мы не можем тут,
    # поэтому вытащим имя из JWT и найдём юзера
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
    user = create_user_row(db, username=username, email=email, password=password)
    resp = RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)
    return resp


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
        raise HTTPException(status_code=400, detail="Bad credentials")
    token = create_access_token({"sub": user.username})
    resp = RedirectResponse(url="/web/dashboard", status_code=status.HTTP_302_FOUND)
    # простая cookie (для демо)
    resp.set_cookie("access_token", token, httponly=True, samesite="Lax")
    return resp


@web_router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = current_user_by_cookie(db, request)
    if not user:
        return RedirectResponse("/web/login", status_code=status.HTTP_302_FOUND)
    txs = get_transactions(db, user.id)
    preds = db.query(Prediction).filter(Prediction.user_id == user.id).order_by(Prediction.created_at.desc()).all()
    models = db.query(MLModel).all()
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user, "transactions": txs, "predictions": preds, "models": models},
    )


@web_router.post("/deposit")
def deposit(request: Request, amount: float = Form(...), db: Session = Depends(get_db)):
    user = current_user_by_cookie(db, request)
    if not user:
        return RedirectResponse("/web/login", status_code=status.HTTP_302_FOUND)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    create_transaction(db, user_id=user.id, amount=amount, type="deposit")
    return RedirectResponse("/web/dashboard", status_code=status.HTTP_302_FOUND)


def _split_valid_invalid(records: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    valid, invalid = [], []
    for r in records:
        if isinstance(r, dict) and all(isinstance(v, (int, float)) for v in r.values()):
            valid.append(r)
        else:
            invalid.append(r)
    return valid, invalid


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
        raise HTTPException(status_code=404, detail="Model not found")
    if user.balance < model.price:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    input_data = {"feature1": feature1, "feature2": feature2, "feature3": feature3}
    # В демо отправим в БД сразу предикт и спишем баланс:
    from shared.models.prediction import Prediction
    pred = Prediction(user_id=user.id, model_id=model_id, prediction="0.42", cost=float(model.price))
    db.add(pred)
    user.balance -= float(model.price)
    db.add(user)
    from shared.models.transaction import Transaction
    db.add(Transaction(user_id=user.id, amount=float(model.price), type="withdraw"))
    db.commit()

    txs = get_transactions(db, user.id)
    preds = db.query(Prediction).filter(Prediction.user_id == user.id).order_by(Prediction.created_at.desc()).all()
    models = db.query(MLModel).all()

    result = {"prediction": pred.prediction}
    invalid: List[dict] = []

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "transactions": txs,
            "predictions": preds,
            "models": models,
            "result": result,
            "invalid_records": invalid,
        },
    )
