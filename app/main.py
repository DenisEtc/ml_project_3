from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.services.user_service import create_user, get_user
from app.services.transaction_service import deposit, withdraw, get_transaction_history
from app.models.user import UserRole

app = FastAPI(title="ML Service API", version="1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/users")
def create_new_user(username: str, email: str, password: str, db: Session = Depends(get_db)):
    user = create_user(db, username=username, email=email, password=password)
    return {"id": user.id, "username": user.username, "balance": user.balance}

@app.post("/deposit")
def deposit_money(user_id: int, amount: float, db: Session = Depends(get_db)):
    try:
        transaction = deposit(db, user_id, amount)
        return {"status": "success", "transaction_id": transaction.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/withdraw")
def withdraw_money(user_id: int, amount: float, db: Session = Depends(get_db)):
    try:
        transaction = withdraw(db, user_id, amount)
        return {"status": "success", "transaction_id": transaction.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/transactions")
def get_user_transactions(user_id: int, db: Session = Depends(get_db)):
    return get_transaction_history(db, user_id)
