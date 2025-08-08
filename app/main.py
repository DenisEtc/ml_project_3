from datetime import timedelta
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import Token
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.schemas.ml_task import PredictionRequest, PredictionResponse

from app.services.auth_service import (
    authenticate_user, create_access_token,
    get_current_user, get_db
)
from app.services.user_service import create_user as create_user_row
from app.services.transaction_service import create_transaction, get_transactions
from app.services.ml_task_service import send_task_to_queue
from shared.models.user import User

# Для инициализации БД при старте
from shared.db import Base, engine
# Импорты моделей, чтобы Base «увидела» таблицы
from shared.models import user as _m_user, transaction as _m_tx, prediction as _m_pred, ml_model as _m_ml

# Подключаем web-интерфейс (шаблоны)
from app.routes.web_routes import web_router


app = FastAPI(title="ML Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():

    Base.metadata.create_all(bind=engine)


# Подключаем роуты веб-интерфейса
app.include_router(web_router)


# ---- AUTH ----
@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="User with given username/email already exists")

    created = create_user_row(
        db=db,
        username=user.username,
        email=user.email,
        password=user.password
    )
    return created


@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


# ---- TRANSACTIONS ----
@app.post("/transactions", response_model=TransactionResponse)
def create_txn(data: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if data.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    txn = create_transaction(db, data.user_id, data.amount, data.type)
    if not txn:
        raise HTTPException(status_code=400, detail="Unable to create transaction")
    return txn


@app.get("/transactions/{user_id}", response_model=List[TransactionResponse])
def list_txns(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return get_transactions(db, user_id)


# ---- PREDICTION TASK ----
@app.post("/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest, current_user: User = Depends(get_current_user)):
    if req.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    send_task_to_queue(req.user_id, req.model_id, req.input_data)
    return {"message": "Prediction task sent to queue"}
