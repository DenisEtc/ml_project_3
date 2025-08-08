from datetime import datetime
from pydantic import BaseModel

class TransactionBase(BaseModel):
    amount: float
    type: str  # 'deposit' или 'withdraw'

class TransactionCreate(TransactionBase):
    user_id: int

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
