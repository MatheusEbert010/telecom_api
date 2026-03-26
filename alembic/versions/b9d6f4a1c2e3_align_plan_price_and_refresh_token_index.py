"""Alinha tipo de preco do plano e indice de refresh token

Revision ID: b9d6f4a1c2e3
Revises: 2877d5724474
Create Date: 2026-03-25 23:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# Identificadores da revisao usados pelo Alembic.
revision: str = "b9d6f4a1c2e3"
down_revision: str | Sequence[str] | None = "2877d5724474"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Converte preco para decimal e indexa refresh tokens por usuario."""
    with op.batch_alter_table("plans") as batch_op:
        batch_op.alter_column(
            "price",
            existing_type=sa.Float(),
            type_=sa.Numeric(10, 2),
            existing_nullable=False,
        )

    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.create_index(batch_op.f("ix_refresh_tokens_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    """Restaura o tipo antigo de preco e remove o indice adicional."""
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.drop_index(batch_op.f("ix_refresh_tokens_user_id"))

    with op.batch_alter_table("plans") as batch_op:
        batch_op.alter_column(
            "price",
            existing_type=sa.Numeric(10, 2),
            type_=sa.Float(),
            existing_nullable=False,
        )
