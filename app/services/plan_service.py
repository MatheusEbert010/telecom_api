"""Regras de negocio relacionadas ao catalogo e consulta de planos."""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from .. import models, schemas
from ..cache import cache
from ..crud import plan_repository


def create_plan(db: Session, plan: schemas.PlanCreate):
    """Cria um plano novo impedindo duplicidade de nome."""
    existing_plan = plan_repository.get_plan_by_name(db, plan.name)
    if existing_plan:
        raise HTTPException(status_code=400, detail="Ja existe um plano com esse nome")

    created_plan = plan_repository.create_plan(db, plan)
    cache.clear_pattern("plans:list:*")
    return created_plan


def delete_plan(db: Session, plan_id: int):
    """Remove um plano e limpa assinaturas que apontavam para ele."""
    plan = plan_repository.get_plan_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano nao encontrado")

    deleted_plan = plan_repository.delete_plan(db, plan)
    cache.clear_pattern("plans:list:*")
    cache.clear_pattern("users:list:*")
    return deleted_plan


def update_plan(db: Session, plan_id: int, payload: schemas.PlanCreate):
    """Atualiza um plano mantendo a regra de nome unico."""
    plan = plan_repository.get_plan_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano nao encontrado")

    existing_plan = plan_repository.get_plan_by_name(db, payload.name)
    if existing_plan and existing_plan.id != plan_id:
        raise HTTPException(status_code=400, detail="Ja existe um plano com esse nome")

    updated_plan = plan_repository.update_plan(db, plan, payload)
    cache.clear_pattern("plans:list:*")
    cache.clear_pattern("users:list:*")
    return updated_plan


def list_plans_advanced(
    db: Session,
    page: int = 1,
    limit: int = 10,
    search: str | None = None,
    min_speed: int | None = None,
    max_speed: int | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    sort_by: str = "price",
    sort_order: str = "asc",
):
    """Lista planos com filtros de busca, preco, velocidade e ordenacao."""
    cache_key = (
        "plans:list:"
        f"{page}:{limit}:{search}:{min_speed}:{max_speed}:{min_price}:{max_price}:{sort_by}:{sort_order}"
    )

    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 10

    query = db.query(models.Plan)

    if search:
        query = query.filter(models.Plan.name.ilike(f"%{search}%"))
    if min_speed is not None:
        query = query.filter(models.Plan.speed >= min_speed)
    if max_speed is not None:
        query = query.filter(models.Plan.speed <= max_speed)
    if min_price is not None:
        query = query.filter(models.Plan.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Plan.price <= max_price)

    sort_column = getattr(models.Plan, sort_by)
    query = query.order_by(desc(sort_column) if sort_order == "desc" else asc(sort_column))

    offset = (page - 1) * limit
    total = query.count()
    plans = query.offset(offset).limit(limit).all()
    result = {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": (total + limit - 1) // limit,
        "data": plans,
        "filters": {
            "search": search,
            "min_speed": min_speed,
            "max_speed": max_speed,
            "min_price": min_price,
            "max_price": max_price,
            "sort_by": sort_by,
            "sort_order": sort_order,
        },
    }

    cache.set(cache_key, result, expire=600)
    return result
