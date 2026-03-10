from sqlalchemy.orm import Session
from .. import models, schemas

###ACESSO AO BANCO DE DADOS PARA PLANOS, INCLUINDO CRIAÇÃO E CONSULTA
def create_plan(db: Session, plan: schemas.PlanCreate):

    db_plan = models.Plan(
        name=plan.name,
        price=plan.price,
        speed=plan.speed
    )

    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)

    return db_plan

###CONSULTA DE PLANOS, INCLUINDO LISTAGEM E CONSULTA POR ID
def get_plans(db: Session):

    return db.query(models.Plan).all()

###CONSULTA DE PLANO POR ID
def get_plan_by_id(db: Session, plan_id: int):

    return db.query(models.Plan).filter(models.Plan.id == plan_id).first()