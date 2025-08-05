from sqlalchemy.orm import Session
from shared.models.user import User
from app.services.auth_service import get_password_hash

def create_user(db: Session, username: str, email: str, password: str):
    user = User(username=username, email=email, password_hash=get_password_hash(password), balance=0.0)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()
