"""Adiciona tabela de refresh tokens

Revision ID: 2877d5724474
Revises: 9bdf7d22c4ec
Create Date: 2026-03-19 19:44:57.938347

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# Identificadores da revisao usados pelo Alembic.
revision: str = "2877d5724474"
down_revision: str | Sequence[str] | None = "9bdf7d22c4ec"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria a tabela usada para persistir refresh tokens."""
    # ### comandos gerados automaticamente pelo Alembic ###
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=500), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(op.f("ix_refresh_tokens_id"), "refresh_tokens", ["id"], unique=False)
    # ### fim dos comandos do Alembic ###


def downgrade() -> None:
    """Remove a tabela de refresh tokens."""
    # ### comandos gerados automaticamente pelo Alembic ###
    op.drop_index(op.f("ix_refresh_tokens_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    # ### fim dos comandos do Alembic ###
