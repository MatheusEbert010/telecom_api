"""Configuracao de logs com cuidado para nao expor dados sensiveis."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from .config import settings


class SafeFormatter(logging.Formatter):
    """Redige mensagens com senha ou token antes de envia-las ao destino final."""

    def format(self, record):
        """Cria uma copia do registro para nao alterar o objeto original."""
        if not hasattr(record, "getMessage"):
            return super().format(record)

        message = record.getMessage()
        if "password" in message.lower() or "token" in message.lower():
            message = "[REDACTED SENSITIVE DATA]"

        safe_record = logging.makeLogRecord(record.__dict__.copy())
        safe_record.msg = message
        safe_record.args = ()
        return super().format(safe_record)


def setup_logging():
    """Configura o logger raiz, console e arquivo rotativo quando habilitado."""
    logging.getLogger().handlers.clear()

    formatter = SafeFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handlers: list[logging.Handler] = []

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    if settings.log_to_file:
        settings.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            settings.log_file_path,
            maxBytes=1_048_576,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(level=getattr(logging, settings.log_level), handlers=handlers, force=True)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(
        "Logs configurados. gravacao_em_arquivo=%s caminho=%s",
        settings.log_to_file,
        settings.log_file_path,
    )
    return logger
