from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.user import User
from app.models.ml_model import MLModel
from app.models.ml_task import MLTask
from app.models.transaction import Transaction

app = FastAPI(title="ML Service API", version="1.0")


# Dependency для сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    """
    Получить список всех пользователей.
    """
    users = db.query(User).all()
    return users


@app.get("/models")
def get_models(db: Session = Depends(get_db)):
    """
    Получить список всех ML моделей.
    """
    models = db.query(MLModel).all()
    return models


@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db)):
    """
    Получить список всех ML задач.
    """
    tasks = db.query(MLTask).all()
    return tasks


@app.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    """
    Получить список всех транзакций.
    """
    transactions = db.query(Transaction).all()
    return transactions
