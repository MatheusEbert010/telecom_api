"""Torna velocidade obrigatoria e adiciona indices frequentes em usuarios

Revision ID: 7f6e7d8c9a10
Revises: b9d6f4a1c2e3
Create Date: 2026-03-26 10:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# Identificadores da revisao usados pelo Alembic.
revision: str = "7f6e7d8c9a10"
down_revision: str | Sequence[str] | None = "b9d6f4a1c2e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Fortalece o schema de planos e melhora filtros frequentes de usuarios."""
    op.execute(sa.text("UPDATE plans SET speed = 1 WHERE speed IS NULL"))

    with op.batch_alter_table("plans") as batch_op:
        batch_op.alter_column(
            "speed",
            existing_type=sa.Integer(),
            nullable=False,
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.create_index(batch_op.f("ix_users_plan_id"), ["plan_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_users_role"), ["role"], unique=False)


def downgrade() -> None:
    """Reverte os indices adicionados e volta a aceitar velocidade nula."""
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_role"))
        batch_op.drop_index(batch_op.f("ix_users_plan_id"))

    with op.batch_alter_table("plans") as batch_op:
        batch_op.alter_column(
            "speed",
            existing_type=sa.Integer(),
            nullable=True,
        )
