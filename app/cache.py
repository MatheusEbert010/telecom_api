import redis
import json
import logging
from typing import Any, Optional
from .config import settings

# Ensure we're using the standard synchronous Redis client
from redis import Redis

logger = logging.getLogger(__name__)

class Cache:
    def __init__(self):
        try:
            self.redis_client = Redis(
                host=settings.redis_host if hasattr(settings, 'redis_host') else 'localhost',
                port=settings.redis_port if hasattr(settings, 'redis_port') else 6379,
                db=settings.redis_db if hasattr(settings, 'redis_db') else 0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info("Redis cache connected successfully")
        except redis.ConnectionError:
            logger.warning("Redis not available, cache disabled")
            self.enabled = False
        except Exception as e:
            logger.warning(f"Redis error: {e}, cache disabled")
            self.enabled = False

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
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
        """Set value in cache with expiration in seconds"""
        if not self.enabled:
            return False

        try:
            return bool(self.redis_client.setex(key, expire, json.dumps(value)))
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.enabled:
            return False

        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear_pattern(self, pattern: str) -> bool:
        """Clear all keys matching pattern"""
        if not self.enabled:
            return False

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                if isinstance(keys, list) and keys:
                    self.redis_client.delete(*keys)
                return True
            return True
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return False

# Instância global do cache
cache = Cache()