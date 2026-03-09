from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..crud import crud_completo
from .. import schemas
from ..services import user_service
from ..telecom_db import SessionLocal

router = APIRouter(prefix="/plans", tags=["Plans"])

###DEPENDÊNCIA PARA OBTER A SESSÃO DO BANCO DE DADOS
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

###ROTAS PARA GERENCIAR PLANOS
@router.post("/")
def create_plan(plan: schemas.PlanCreate, db: Session = Depends(get_db)):
    return crud_completo.create_plan(db, plan)

@router.get("/")
def list_plans(db: Session = Depends(get_db)):
    return crud_completo.get_plans(db)

###ROTA PARA INSCRIÇÃO DE USUÁRIO EM UM PLANO
@router.post("/{user_id}/subscribe")
def subscribe_plan(user_id: int, data: schemas.SubscribePlan, db: Session = Depends(get_db)):
    return user_service.subscribe_plan(db, user_id, data.plan_id)