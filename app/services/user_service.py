from sqlalchemy.orm import Session
from app.models.user import User, UserRole
import hashlib

def create_user(db: Session, username: str, email: str, password: str, role: UserRole = UserRole.USER):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    user = User(username=username, email=email, password_hash=hashed_password, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()
