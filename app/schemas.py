from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str
    phone: str


class UserResponse(UserCreate):
    id: int

class PlanCreate(BaseModel):
    name: str
    price: float
    speed: int


class PlanResponse(PlanCreate):
    id: int

    class Config:
        orm_mode = True