from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.services.auth_service import authenticate_user, create_access_token, get_current_user, get_db
from app.schemas.auth import Token
from app.services.user_service import create_user
from app.models.user import User

app = FastAPI()


# Авторизация и регистрация
@app.post("/auth/register")
def register(username: str, email: str, password: str, db: Session = Depends(get_db)):
    user = create_user(db, username=username, email=email, password=password)
    return {"message": f"User {user.username} created"}


@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


# Защищённые эндпоинты
@app.post("/deposit")
def deposit(user_id: int, amount: float, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    # Логика пополнения
    return {"message": f"Deposited {amount} credits for user {user_id}"}


@app.post("/withdraw")
def withdraw(user_id: int, amount: float, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    # Логика списания
    return {"message": f"Withdrawn {amount} credits for user {user_id}"}


@app.get("/history/transactions")
def transaction_history(user_id: int, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return {"history": []}


@app.post("/predict")
def predict(user_id: int, model_id: int, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return {"result": "Prediction done"}
