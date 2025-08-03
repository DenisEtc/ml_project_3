from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.services.auth_service import hash_password

def create_user(db: Session, username: str, email: str, password: str, role: UserRole = UserRole.USER):
    existing_user = db.query(User).filter((User.email == email) | (User.username == username)).first()
    if existing_user:
        raise ValueError("User with this email or username already exists")

    user = User(username=username, email=email, password_hash=hash_password(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()
