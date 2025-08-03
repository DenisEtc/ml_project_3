from pydantic import BaseModel

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    balance: float

    class Config:
        orm_mode = True
