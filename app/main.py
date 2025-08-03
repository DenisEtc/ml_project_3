from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.services.user_service import create_user
from app.services.auth_service import authenticate_user, create_access_token
from app.services.transaction_service import deposit, withdraw, get_transaction_history
from app.services.ml_task_service import create_ml_task, get_prediction_history
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserResponse
from app.schemas.transaction import TransactionResponse
from app.schemas.ml_task import PredictRequest, PredictionHistoryResponse

app = FastAPI(title="ML Service API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/auth/register", response_model=UserResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = create_user(db, data.username, data.email, data.password)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/deposit", response_model=TransactionResponse)
def deposit_money(user_id: int, amount: float, db: Session = Depends(get_db)):
    return deposit(db, user_id, amount)

@app.post("/withdraw", response_model=TransactionResponse)
def withdraw_money(user_id: int, amount: float, db: Session = Depends(get_db)):
    return withdraw(db, user_id, amount)

@app.get("/history/transactions", response_model=list[TransactionResponse])
def transaction_history(user_id: int, db: Session = Depends(get_db)):
    return get_transaction_history(db, user_id)

@app.post("/predict", response_model=PredictionHistoryResponse)
def predict(data: PredictRequest, user_id: int, db: Session = Depends(get_db)):
    return create_ml_task(db, user_id, data.model_id, data.input_data)

@app.get("/history/predictions", response_model=list[PredictionHistoryResponse])
def predictions_history(user_id: int, db: Session = Depends(get_db)):
    return get_prediction_history(db, user_id)
