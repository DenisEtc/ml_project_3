from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from sqlalchemy.orm import Session

from app.services.auth_service import get_current_user, get_db
from app.services.transaction_service import create_transaction, get_transactions
from app.services.ml_task_service import send_task_to_queue
from shared.models.user import User

templates = Jinja2Templates(directory="app/templates")
web_router = APIRouter()

@web_router.get("/")
def home(request: Request):

    return templates.TemplateResponse("index.html", {"request": request})

@web_router.get("/dashboard")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    txs = get_transactions(db, current_user.id)
    last_prediction = request.cookies.get("last_prediction")
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "transactions": txs,
        "last_prediction": last_prediction
    })

@web_router.post("/deposit")
def deposit(
    amount: float = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    create_transaction(db, current_user.id, amount, "deposit")
    return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)

@web_router.post("/withdraw")
def withdraw(
    amount: float = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    txn = create_transaction(db, current_user.id, amount, "withdraw")
    if not txn:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)

@web_router.post("/predict-form")
def predict_form(
    feature1: float = Form(...),
    feature2: float = Form(...),
    feature3: float = Form(...),
    current_user: User = Depends(get_current_user)
):

    input_data = {
        "feature1": feature1,
        "feature2": feature2,
        "feature3": feature3
    }

    send_task_to_queue(user_id=current_user.id, model_id=1, input_data=input_data)
    resp = RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)
    resp.set_cookie(key="last_prediction", value="task_enqueued")
    return resp
