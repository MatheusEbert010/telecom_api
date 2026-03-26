"""Configuracoes centralizadas carregadas de variaveis de ambiente."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]


class Settings(BaseSettings):
    """Agrupa parametros de seguranca, banco, cache e ambiente."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Metadados da aplicacao.
    app_name: str = "Telecom API"
    app_version: str = "1.2.0"

    # Seguranca da autenticacao.
    secret_key: str | None = Field(None, min_length=32)
    secret_key_file: str | None = None
    algorithm: str = "HS256"
    jwt_issuer: str = "telecom-api"
    jwt_audience: str = "telecom-api-clients"
    access_token_expire_minutes: int = Field(30, gt=0)
    refresh_token_expire_days: int = Field(7, gt=0)

    # Conexao principal do banco.
    database_url: str | None = None
    database_url_file: str | None = None

    # Configuracao do Redis.
    redis_host: str = "localhost"
    redis_port: int = Field(6379, ge=1, le=65535)
    redis_db: int = Field(0, ge=0)

    # HTTP / ambiente.
    environment: Environment = "development"
    cors_origins: list[str] = Field(default_factory=list)
    health_expose_version: bool | None = None
    trust_client_request_id: bool | None = None

    # Logging.
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_dir: str = "logs"
    log_file_name: str = "telecom_api.log"
    log_to_file: bool = True

    @model_validator(mode="before")
    @classmethod
    def load_secrets_from_files(cls, data: object):
        """Permite carregar valores sensiveis a partir de caminhos `*_FILE`."""
        if not isinstance(data, dict):
            return data

        values = dict(data)
        file_mappings = {
            "secret_key": "secret_key_file",
            "database_url": "database_url_file",
        }

        for field_name, file_field_name in file_mappings.items():
            file_path = values.get(file_field_name)
            if not file_path:
                continue

            secret_path = Path(str(file_path)).expanduser()
            if not secret_path.is_file():
                raise ValueError(
                    f"{file_field_name.upper()} aponta para um arquivo inexistente: {secret_path}"
                )

            values[field_name] = secret_path.read_text(encoding="utf-8").strip()

        return values

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str | None) -> str:
        """Garante uma chave secreta minimamente forte para JWT."""
        if not value:
            raise ValueError("SECRET_KEY ou SECRET_KEY_FILE deve ser informado")
        if len(value.strip()) < 32:
            raise ValueError("SECRET_KEY deve ter pelo menos 32 caracteres")
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str | None) -> str:
        """Exige a URL do banco por variavel direta ou por arquivo seguro."""
        if not value:
            raise ValueError("DATABASE_URL ou DATABASE_URL_FILE deve ser informado")
        return value.strip()

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
    def should_expose_health_version(self) -> bool:
        """Controla se o endpoint publico de health expoe a versao da API."""
        if self.health_expose_version is not None:
            return self.health_expose_version
        return self.environment != "production"

    @property
    def should_trust_client_request_id(self) -> bool:
        """Controla se o `X-Request-ID` enviado pelo cliente deve ser reaproveitado."""
        if self.trust_client_request_id is not None:
            return self.trust_client_request_id
        return self.environment != "production"

    @property
    def log_file_path(self) -> Path:
        """Resolve o caminho final do arquivo de log da aplicacao."""
        return Path(self.log_dir) / self.log_file_name


settings = Settings()
