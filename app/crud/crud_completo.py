from sqlalchemy.orm import Session
from .. import models, schemas

###CRIAÇÃO DE USUÁRIOS E PLANOS, INCLUINDO INSCRIÇÃO DE USUÁRIOS EM PLANOS, COM ACESSO AO BANCO DE DADOS
def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        name=user.name,
        email=user.email,
        phone=user.phone
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

###ACESSO AO BANCO DE DADOS PARA USUÁRIOS, INCLUINDO INSCRIÇÃO EM PLANOS
def get_users(db: Session):
    return db.query(models.User).all()

###ACESSO AO BANCO DE DADOS PARA USUÁRIOS POR ID
def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

###DELETA USUÁRIO DO BANCO DE DADOS
def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user:
        db.delete(user)
        db.commit()

    return user

###ATUALIZA USUÁRIO NO BANCO DE DADOS
def update_user(db: Session, user_id: int, user_data: schemas.UserCreate):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        return None

    user.name = user_data.name
    user.email = user_data.email
    user.phone = user_data.phone

    db.commit()
    db.refresh(user)

    return user

###CRIAÇÃO DE PLANOS, INCLUINDO INSCRIÇÃO DE USUÁRIOS EM PLANOS, COM ACESSO AO BANCO DE DADOS
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

###ACESSO AO BANCO DE DADOS PARA PLANOS
def get_plans(db: Session):
    return db.query(models.Plan).all()

###ACESSO AO BANCO DE DADOS PARA INSCRIÇÃO DE USUÁRIO EM UM PLANO
def subscribe_user_to_plan(db: Session, user_id: int, plan_id: int):

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        return None

    plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()

    if not plan:
        return "Plano indisponível no momento."

    user.plan_id = plan_id

    db.commit()
    db.refresh(user)

    return user