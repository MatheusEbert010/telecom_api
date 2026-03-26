"""Camada simples de cache para leituras repetidas da API."""

import json
import logging
from typing import Any

import redis
from fastapi.encoders import jsonable_encoder
from redis import Redis

from .config import settings

logger = logging.getLogger(__name__)


class Cache:
    """Encapsula operacoes de cache com fallback seguro quando o Redis falha."""

    def __init__(self):
        """Inicializa o cliente Redis e desabilita o cache se nao houver conexao."""
        try:
            self.redis_client = Redis(
                host=settings.redis_host if hasattr(settings, "redis_host") else "localhost",
                port=settings.redis_port if hasattr(settings, "redis_port") else 6379,
                db=settings.redis_db if hasattr(settings, "redis_db") else 0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            self.redis_client.ping()
            self.enabled = True
            logger.info("Redis cache connected successfully")
        except redis.ConnectionError:
            logger.warning("Redis not available, cache disabled")
            self.enabled = False
        except Exception as e:
            logger.warning(f"Redis error: {e}, cache disabled")
            self.enabled = False

    def get(self, key: str) -> Any | None:
        """Busca um valor serializado no cache."""
        if not self.enabled:
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(str(value))
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """Salva um valor JSON-serializavel com tempo de expiracao em segundos."""
        if not self.enabled:
            return False

        try:
            # Converte objetos ORM e schemas em estruturas seguras para JSON.
            encoded_value = jsonable_encoder(value, exclude_none=True)
            return bool(self.redis_client.setex(key, expire, json.dumps(encoded_value)))
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Remove uma chave especifica do cache."""
        if not self.enabled:
            return False

        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear_pattern(self, pattern: str) -> bool:
        """Remove todas as chaves que seguem um padrao comum."""
        if not self.enabled:
            return False

        try:
            keys = list(self.redis_client.scan_iter(match=pattern))
            if keys:
                self.redis_client.delete(*keys)
                return True
            return True
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return False


cache = Cache()
