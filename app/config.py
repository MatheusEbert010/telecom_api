"""Configuracoes centralizadas carregadas de variaveis de ambiente."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Agrupa parametros de seguranca, banco, cache e ambiente."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Seguranca da autenticacao.
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Conexao principal do banco.
    database_url: str

    # Configuracao do Redis.
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # Ambiente de execucao.
    environment: str = "development"


settings = Settings()
