"""Contexto compartilhado por requisicao para correlacao e observabilidade."""

from __future__ import annotations

from contextvars import ContextVar

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


def set_request_id(request_id: str):
    """Armazena o identificador atual da requisicao no contexto."""
    return request_id_context.set(request_id)


def get_request_id() -> str:
    """Retorna o identificador atual da requisicao para logs e respostas."""
    return request_id_context.get()


def reset_request_id(token) -> None:
    """Restaura o contexto anterior ao fim do processamento da requisicao."""
    request_id_context.reset(token)
