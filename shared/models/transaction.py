from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, func
from shared.db import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # "deposit" or "withdraw"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
