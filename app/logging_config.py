"""Configuracao de logs com cuidado para nao expor dados sensiveis."""

import logging
import sys

from .config import settings


def setup_logging():
    """Configura o logger raiz e mascara mensagens sensiveis."""
    logging.getLogger().handlers.clear()

    log_level = logging.INFO if settings.environment == "production" else logging.DEBUG

    class SafeFormatter(logging.Formatter):
        """Redige mensagens com senha ou token antes de envia-las ao console."""

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

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        SafeFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    logging.basicConfig(level=log_level, handlers=[console_handler])
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    return logging.getLogger(__name__)
