from datetime import datetime
from pydantic import BaseModel

class PredictionRequest(BaseModel):
    user_id: int
    model_id: int
    input_data: dict

class PredictionResponse(BaseModel):
    message: str

class PredictionRecord(BaseModel):
    id: int
    user_id: int
    model_id: int
    prediction: str
    created_at: datetime

    class Config:
        orm_mode = True
