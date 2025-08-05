from pydantic import BaseModel
from typing import Dict

class PredictionRequest(BaseModel):
    user_id: int
    model_id: int
    input_data: Dict[str, float]
