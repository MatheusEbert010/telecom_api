"""Adiciona campos de endereco na tabela de usuarios

Revision ID: c2a4b8e1d9f0
Revises: 7f6e7d8c9a10
Create Date: 2026-03-31 11:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c2a4b8e1d9f0"
down_revision: str | Sequence[str] | None = "7f6e7d8c9a10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Inclui colunas opcionais de endereco para qualquer tipo de usuario."""
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("street", sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column("neighborhood", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("address_number", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("address_complement", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("cep", sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Remove as colunas de endereco adicionadas nesta revisao."""
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("cep")
        batch_op.drop_column("address_complement")
        batch_op.drop_column("address_number")
        batch_op.drop_column("neighborhood")
        batch_op.drop_column("street")
