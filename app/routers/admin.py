"""Rotas HTTP exclusivas para operacoes administrativas agregadas."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..dependencies.auth_dependency import get_current_admin
from ..services import admin_service
from ..telecom_db import get_db

router = APIRouter(prefix="/admin", tags=["Administracao"])


@router.get("/stats", response_model=schemas.AdminStatsResponse)
def get_admin_stats(
    _: object = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Entrega indicadores resumidos da base para uso administrativo."""
    return admin_service.get_admin_stats(db)
