from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import status
import requests

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

API_URL = "http://ml_app:8000"  # Для взаимодействия с API внутри контейнеров


# Если тестируешь локально, поставь http://localhost:8000

@router.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/register")
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
def register_user(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    response = requests.post(f"{API_URL}/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    return RedirectResponse("/register", status_code=status.HTTP_302_FOUND)


@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    response = requests.post(f"{API_URL}/auth/login", params={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        token = response.json()["access_token"]
        response = RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="access_token", value=token)
        return response
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)


@router.get("/dashboard")
def dashboard(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/login")

    headers = {"Authorization": f"Bearer {token}"}
    user_response = requests.get(f"{API_URL}/users/me", headers=headers)
    transactions_response = requests.get(f"{API_URL}/transactions?user_id={user_response.json()['id']}",
                                         headers=headers)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user_response.json(),
        "transactions": transactions_response.json()
    })


@router.post("/deposit")
def deposit(request: Request, amount: float = Form(...)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/login")

    headers = {"Authorization": f"Bearer {token}"}
    user_response = requests.get(f"{API_URL}/users/me", headers=headers)
    requests.post(f"{API_URL}/deposit", params={
        "user_id": user_response.json()["id"],
        "amount": amount
    }, headers=headers)

    return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)


@router.post("/predict")
def predict(request: Request, feature1: float = Form(...), feature2: float = Form(...), feature3: float = Form(...)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/login")

    headers = {"Authorization": f"Bearer {token}"}
    user_response = requests.get(f"{API_URL}/users/me", headers=headers)

    requests.post(f"{API_URL}/predict", json={
        "user_id": user_response.json()["id"],
        "model_id": 1,
        "input_data": {
            "feature1": feature1,
            "feature2": feature2,
            "feature3": feature3
        }
    }, headers=headers)

    return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)
