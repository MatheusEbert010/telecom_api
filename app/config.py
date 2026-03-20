from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Segurança
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Banco de dados
    database_url: str

    # Cache Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # Ambiente
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False

# Instância global das configurações
settings = Settings()