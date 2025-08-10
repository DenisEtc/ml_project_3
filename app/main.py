import os
from datetime import timedelta
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from shared.db import get_db, Base, engine
from shared.models.user import User
from shared.models.transaction import Transaction
from shared.models.ml_model import MLModel
from shared.models.prediction import Prediction

from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import Token
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.schemas.ml_task import PredictionRequest, PredictionResponse, PredictionRecord
from app.services.user_service import create_user as create_user_row
from app.services.transaction_service import create_transaction, get_transactions
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)
from app.services.ml_task_service import send_task_to_queue
from app.routes.web_routes import web_router

# Создание таблиц (на случай, если init не был вызван)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ML Service")

app.include_router(web_router, prefix="/web", tags=["web"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- AUTH ---------
@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter((User.username == user.username) | (User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    row = create_user_row(db=db, username=user.username, email=user.email, password=user.password)
    return UserResponse.from_orm(row)


@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=60))
    return Token(access_token=access)


@app.get("/users/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse.from_orm(current_user)

# --------- TRANSACTIONS ---------
@app.post("/transactions/deposit", response_model=TransactionResponse)
def deposit(tx: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if tx.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if tx.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    tr = create_transaction(db, user_id=tx.user_id, amount=tx.amount, type="deposit")
    if not tr:
        raise HTTPException(status_code=400, detail="Transaction failed")
    return TransactionResponse.from_orm(tr)


@app.get("/transactions/{user_id}", response_model=List[TransactionResponse])
def list_transactions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    rows = get_transactions(db, user_id)
    return [TransactionResponse.from_orm(r) for r in rows]

# --------- PREDICTIONS ---------
def _get_model_price(db: Session, model_id: int) -> float:
    model = db.query(MLModel).filter(MLModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return float(model.price or 0.0)


@app.post("/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    price = _get_model_price(db, req.model_id)

    # Проверка баланса перед постановкой задачи
    user = db.query(User).filter(User.id == req.user_id).with_for_update(read=False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.balance < price:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # TEST_MODE: имитируем мгновенный предикт и списание
    if os.getenv("TEST_MODE", "0") == "1":
        pred = Prediction(user_id=req.user_id, model_id=req.model_id, prediction="0.42", cost=price)
        db.add(pred)

        # списание
        user.balance -= price
        tx = Transaction(user_id=req.user_id, amount=price, type="withdraw")
        db.add(tx)

        db.commit()
        return PredictionResponse(message="Prediction completed (TEST_MODE)")

    # боевой путь — отправляем задачу в очередь
    send_task_to_queue(user_id=req.user_id, model_id=req.model_id, input_data=req.input_data, price=price)
    return PredictionResponse(message="Task accepted")

@app.get("/predictions/{user_id}", response_model=List[PredictionRecord])
def predictions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    rows = (
        db.query(Prediction)
        .filter(Prediction.user_id == user_id)
        .order_by(Prediction.created_at.desc())
        .all()
    )
    return [PredictionRecord.from_orm(r) for r in rows]
