import logging
import sys
from .config import settings

# Configuração de logging seguro
def setup_logging():
    # Remover handlers padrão
    logging.getLogger().handlers.clear()
    
    # Configurar nível de log baseado no ambiente
    log_level = logging.INFO if settings.environment == "production" else logging.DEBUG
    
    # Formatter que não exibe dados sensíveis
    class SafeFormatter(logging.Formatter):
        def format(self, record):
            # Remover dados sensíveis das mensagens de log
            if hasattr(record, 'getMessage'):
                message = record.getMessage()
                # Sanitizar mensagens que podem conter dados sensíveis
                if 'password' in message.lower() or 'token' in message.lower():
                    message = "[REDACTED SENSITIVE DATA]"
                record.msg = message
            return super().format(record)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(SafeFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Configurar logger raiz
    logging.basicConfig(
        level=log_level,
        handlers=[console_handler]
    )
    
    # Configurar loggers específicos
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)