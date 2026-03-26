"""Rotas HTTP relacionadas ao catalogo e assinatura de planos."""

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..dependencies.auth_dependency import get_current_admin
from ..services import plan_service
from ..telecom_db import get_db

router = APIRouter(prefix="/plans", tags=["Planos"])


@router.post("/", response_model=schemas.PlanResponse, status_code=201)
def create_plan(
    plan: schemas.PlanCreate,
    current_user: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Cria um novo plano e restringe a operacao a administradores."""
    return plan_service.create_plan(db, plan)


@router.get("/", response_model=schemas.PlanListResponse)
def list_plans(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, min_length=2, max_length=100),
    min_speed: int | None = Query(None, gt=0),
    max_speed: int | None = Query(None, gt=0),
    min_price: Decimal | None = Query(None, gt=0),
    max_price: Decimal | None = Query(None, gt=0),
    sort_by: Literal["name", "price", "speed"] = "price",
    sort_order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
):
    """Lista planos com validacao de filtros antes de consultar a base."""
    if min_speed is not None and max_speed is not None and min_speed > max_speed:
        raise HTTPException(status_code=400, detail="min_speed nao pode ser maior que max_speed")

    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=400, detail="min_price nao pode ser maior que max_price")

    return plan_service.list_plans_advanced(
        db=db,
        page=page,
        limit=limit,
        search=search,
        min_speed=min_speed,
        max_speed=max_speed,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_order=sort_order,
    )
