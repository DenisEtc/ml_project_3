from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from app.db import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_id = Column(Integer, nullable=False)
    prediction = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
