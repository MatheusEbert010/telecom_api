"""Regras de negocio voltadas a funcionalidades administrativas."""

from sqlalchemy.orm import Session

from ..crud import user_repository


def get_admin_stats(db: Session):
    """Retorna metricas consolidadas para acompanhamento administrativo."""
    return user_repository.get_admin_stats(db)
