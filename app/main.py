from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.auth_service import authenticate_user, create_access_token, get_current_user, get_db
from app.services.user_service import create_user, get_user_by_id
from app.services.transaction_service import create_transaction, get_transactions
from app.services.ml_task_service import send_task_to_queue
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import Token
from app.schemas.ml_task import PredictionRequest
from app.schemas.transaction import TransactionResponse
from typing import List
from datetime import timedelta

app = FastAPI(title="ML Service API")

# --- AUTH ---
@app.post("/auth/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    user = create_user(db, user_data.username, user_data.email, user_data.password)
    return user

@app.post("/auth/login", response_model=Token)
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}

# --- USER INFO ---
@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user=Depends(get_current_user)):
    return current_user

# --- BALANCE OPERATIONS ---
@app.post("/deposit", response_model=TransactionResponse)
def deposit(user_id: int, amount: float, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    transaction = create_transaction(db, user_id, amount, "deposit")
    if not transaction:
        raise HTTPException(status_code=400, detail="User not found")
    return transaction

@app.get("/transactions", response_model=List[TransactionResponse])
def get_user_transactions(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    transactions = get_transactions(db, user_id)
    return transactions

# --- PREDICTION TASK ---
@app.post("/predict")
def predict(request: PredictionRequest, current_user=Depends(get_current_user)):
    task = {
        "user_id": request.user_id,
        "model_id": request.model_id,
        "input_data": request.input_data
    }
    send_task_to_queue(task)
    return {"message": "Prediction task sent to queue"}
