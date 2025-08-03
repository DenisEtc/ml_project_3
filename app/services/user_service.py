from sqlalchemy.orm import Session
from app.models.user import User
from app.services.auth_service import get_password_hash

def create_user(db: Session, username: str, email: str, password: str):
    hashed_password = get_password_hash(password)
    new_user = User(username=username, email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
