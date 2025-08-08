from pydantic import BaseModel

class PredictionRequest(BaseModel):
    user_id: int
    model_id: int
    input_data: dict

class PredictionResponse(BaseModel):
    message: str
