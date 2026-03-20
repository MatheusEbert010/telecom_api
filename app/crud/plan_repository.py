"""Operacoes de persistencia relacionadas ao catalogo de planos."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas


def create_plan(db: Session, plan: schemas.PlanCreate):
    """Persiste um novo plano apos a validacao da camada de servico."""
    db_plan = models.Plan(name=plan.name, price=plan.price, speed=plan.speed)
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


def get_plans(db: Session):
    """Retorna todos os planos cadastrados."""
    return db.query(models.Plan).all()


def get_plan_by_id(db: Session, plan_id: int):
    """Busca um plano pela chave primaria."""
    return db.query(models.Plan).filter(models.Plan.id == plan_id).first()


def get_plan_by_name(db: Session, name: str):
    """Busca um plano ignorando diferencas entre maiusculas e minusculas."""
    normalized_name = name.strip().lower()
    return db.query(models.Plan).filter(func.lower(models.Plan.name) == normalized_name).first()
