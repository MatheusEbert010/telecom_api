"""Regras de negocio relacionadas ao catalogo e consulta de planos."""

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


def list_plans_advanced(
    db: Session,
    search: str | None = None,
    min_speed: int | None = None,
    max_speed: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort_by: str = "price",
    sort_order: str = "asc",
):
    """Lista planos com filtros de busca, preco, velocidade e ordenacao."""
    cache_key = (
        f"plans:list:{search}:{min_speed}:{max_speed}:{min_price}:{max_price}:{sort_by}:{sort_order}"
    )

    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

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

    plans = query.all()
    result = {
        "total": len(plans),
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
