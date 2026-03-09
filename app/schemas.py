from pydantic import BaseModel

###SCHEMAS PARA USUÁRIOS E PLANOS
class UserCreate(BaseModel):
    name: str
    email: str
    phone: str
class UserResponse(UserCreate):
    id: int

###CONFIGURAÇÃO PARA USAR MODELOS ORM
class PlanCreate(BaseModel):
    name: str
    price: float
    speed: int
class PlanResponse(PlanCreate):
    id: int
    class Config:
        orm_mode = True

###SCHEMA PARA INSCRIÇÃO DE USUÁRIO EM UM PLANO        
class SubscribePlan(BaseModel):
    plan_id: int