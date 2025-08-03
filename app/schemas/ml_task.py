from pydantic import BaseModel
from typing import Any, Dict
from datetime import datetime

class PredictRequest(BaseModel):
    model_id: int
    input_data: Dict[str, Any]

class PredictionHistoryResponse(BaseModel):
    id: int
    model_id: int
    input_data: Dict[str, Any]
    result_data: Dict[str, Any] | None
    status: str
    created_at: datetime

    class Config:
        orm_mode = True
