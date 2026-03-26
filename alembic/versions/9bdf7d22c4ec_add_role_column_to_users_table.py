"""Adiciona coluna de papel na tabela de usuarios

Revision ID: 9bdf7d22c4ec
Revises: cffc3827488b
Create Date: 2026-03-19 18:55:06.161493

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# Identificadores da revisao usados pelo Alembic.
revision: str = "9bdf7d22c4ec"
down_revision: str | Sequence[str] | None = "cffc3827488b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adiciona a coluna de papel para controle de acesso dos usuarios."""
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="user"),
    )


def downgrade() -> None:
    """Remove a coluna de papel adicionada na migration de RBAC."""
    op.drop_column("users", "role")
