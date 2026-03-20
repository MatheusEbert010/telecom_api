from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..crud import crud_completo
from .. import schemas
from ..services import user_service
from ..telecom_db import get_db

router = APIRouter(prefix="/plans", tags=["Planos"])

###ROTAS PARA GERENCIAR PLANOS
@router.post("/")
def create_plan(plan: schemas.PlanCreate, db: Session = Depends(get_db)):
    return crud_completo.create_plan(db, plan)

@router.get("/")
def list_plans(
    search: str | None = None,        # Busca por nome
    min_speed: int | None = None,     # Velocidade mínima
    max_speed: int | None = None,     # Velocidade máxima
    min_price: float | None = None,   # Preço mínimo
    max_price: float | None = None,   # Preço máximo
    sort_by: str = "price",           # Ordenação: name, price, speed
    sort_order: str = "asc",          # asc ou desc
    db: Session = Depends(get_db)
):
    return crud_completo.get_plans_advanced(
        db=db,
        search=search,
        min_speed=min_speed,
        max_speed=max_speed,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_order=sort_order
    )

###ROTA PARA INSCRIÇÃO DE USUÁRIO EM UM PLANO
@router.post("/{user_id}/subscribe")
def subscribe_plan(user_id: int, data: schemas.SubscribePlan, db: Session = Depends(get_db)):
    return user_service.subscribe_plan(db, user_id, data.plan_id)