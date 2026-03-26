"""Smoke tests para validar o fluxo de migrations em banco limpo."""

from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, inspect

from alembic import command
from alembic.config import Config


def test_alembic_upgrades_and_downgrades_clean_database():
    """Executa upgrade e downgrade para validar a cadeia completa do Alembic."""
    project_root = Path(__file__).resolve().parents[1]
    temp_dir = project_root / ".test_tmp"
    temp_dir.mkdir(exist_ok=True)

    database_path = temp_dir / f"migration_test_{uuid4().hex}.db"
    database_url = f"sqlite:///{database_path}"

    alembic_config = Config(str((project_root / "alembic.ini").resolve()))
    alembic_config.set_main_option("sqlalchemy.url", database_url)

    engine = create_engine(database_url)

    try:
        command.upgrade(alembic_config, "head")

        inspector = inspect(engine)
        assert "plans" in inspector.get_table_names()
        assert "users" in inspector.get_table_names()
        assert "refresh_tokens" in inspector.get_table_names()

        user_columns = {column["name"] for column in inspector.get_columns("users")}
        refresh_token_columns = {column["name"] for column in inspector.get_columns("refresh_tokens")}
        plan_columns = {column["name"]: column for column in inspector.get_columns("plans")}
        user_indexes = {index["name"] for index in inspector.get_indexes("users")}

        assert {"id", "name", "email", "password", "phone", "plan_id", "role"} <= user_columns
        assert {"id", "token", "user_id", "expires_at", "created_at"} <= refresh_token_columns
        assert plan_columns["speed"]["nullable"] is False
        assert {"ix_users_plan_id", "ix_users_role"} <= user_indexes

        command.downgrade(alembic_config, "base")

        inspector = inspect(engine)
        assert "plans" not in inspector.get_table_names()
        assert "users" not in inspector.get_table_names()
        assert "refresh_tokens" not in inspector.get_table_names()
    finally:
        engine.dispose()
        database_path.unlink(missing_ok=True)
