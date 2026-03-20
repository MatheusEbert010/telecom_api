"""Helpers de data e hora para manter o projeto consistente em UTC."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Retorna o horario atual com timezone UTC."""
    return datetime.now(UTC)


def utc_now_naive() -> datetime:
    """Retorna UTC sem timezone para compatibilidade com colunas legadas."""
    return utc_now().replace(tzinfo=None)


def ensure_utc(value: datetime) -> datetime:
    """Normaliza um datetime qualquer para UTC timezone-aware."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
