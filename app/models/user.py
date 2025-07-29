from sqlalchemy import Column, Integer, String, Enum, Float, DateTime
from datetime import datetime
import enum
from app.db import Base

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
