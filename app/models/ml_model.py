from sqlalchemy import Column, Integer, String, Float
from app.db import Base

class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    cost_per_prediction = Column(Float, nullable=False)
