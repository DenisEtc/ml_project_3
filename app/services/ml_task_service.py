from sqlalchemy.orm import Session
from app.models.ml_task import MLTask
from app.models.ml_model import MLModel
from app.models.user import User

def create_ml_task(db: Session, user_id: int, model_id: int, input_data: dict):
    user = db.query(User).filter(User.id == user_id).first()
    model = db.query(MLModel).filter(MLModel.id == model_id).first()
    if not user:
        raise ValueError("User not found")
    if not model:
        raise ValueError("Model not found")
    if user.balance < model.cost_per_prediction:
        raise ValueError("Insufficient balance")

    user.balance -= model.cost_per_prediction
    task = MLTask(user_id=user.id, model_id=model.id, input_data=input_data, status="PENDING")
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def get_prediction_history(db: Session, user_id: int):
    return db.query(MLTask).filter(MLTask.user_id == user_id).all()
