from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class TransactionType(str, Enum):
    deposit = "deposit"
    withdraw = "withdraw"

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    type: TransactionType
    created_at: datetime

    class Config:
        orm_mode = True
