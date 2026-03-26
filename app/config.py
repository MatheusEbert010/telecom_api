"""Configuracoes centralizadas carregadas de variaveis de ambiente."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]


class Settings(BaseSettings):
    """Agrupa parametros de seguranca, banco, cache e ambiente."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Metadados da aplicacao.
    app_name: str = "Telecom API"
    app_version: str = "1.2.0"

    # Seguranca da autenticacao.
    secret_key: str = Field(..., min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(30, gt=0)
    refresh_token_expire_days: int = Field(7, gt=0)

    # Conexao principal do banco.
    database_url: str

    # Configuracao do Redis.
    redis_host: str = "localhost"
    redis_port: int = Field(6379, ge=1, le=65535)
    redis_db: int = Field(0, ge=0)

    # HTTP / ambiente.
    environment: Environment = "development"
    cors_origins: list[str] = Field(default_factory=list)

    # Logging.
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_dir: str = "logs"
    log_file_name: str = "telecom_api.log"
    log_to_file: bool = True

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        """Garante uma chave secreta minimamente forte para JWT."""
        if len(value.strip()) < 32:
            raise ValueError("SECRET_KEY deve ter pelo menos 32 caracteres")
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        """Aceita CORS_ORIGINS como lista, JSON ou CSV simples."""
        if value in (None, ""):
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                parsed = json.loads(stripped)
                if not isinstance(parsed, list):
                    raise ValueError("CORS_ORIGINS JSON deve ser uma lista")
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in stripped.split(",") if item.strip()]
        raise ValueError("Formato invalido para CORS_ORIGINS")

    @property
    def effective_cors_origins(self) -> list[str]:
        """Entrega origens padrao uteis em desenvolvimento e teste."""
        if self.cors_origins:
            return self.cors_origins
        if self.environment in {"development", "test"}:
            return [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:8080",
            ]
        return []

    @property
    def docs_enabled(self) -> bool:
        """Desabilita docs publicas em producao por padrao."""
        return self.environment != "production"

    @property
    def log_file_path(self) -> Path:
        """Resolve o caminho final do arquivo de log da aplicacao."""
        return Path(self.log_dir) / self.log_file_name


settings = Settings()
