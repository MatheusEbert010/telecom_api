"""Script para criar ou promover um usuario administrador."""

from __future__ import annotations

import argparse

from app.services import user_service
from app.telecom_db import SessionLocal


def build_parser() -> argparse.ArgumentParser:
    """Define os argumentos aceitos para bootstrap controlado de admin."""
    parser = argparse.ArgumentParser(
        description="Cria ou promove um usuario administrador de forma idempotente.",
    )
    parser.add_argument("--nome", required=True, help="Nome do usuario administrador.")
    parser.add_argument("--email", required=True, help="Email do usuario administrador.")
    parser.add_argument("--senha", required=True, help="Senha do usuario administrador.")
    parser.add_argument(
        "--telefone",
        default=None,
        help="Telefone opcional do usuario administrador.",
    )
    return parser


def main() -> int:
    """Executa o fluxo de criacao ou promocao de administrador."""
    parser = build_parser()
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user, created = user_service.ensure_admin_user(
            db,
            name=args.nome,
            email=args.email,
            password=args.senha,
            phone=args.telefone,
        )
    finally:
        db.close()

    if created:
        print(
            f"Administrador criado com sucesso. id={user.id} email={user.email} papel={user.role}",
        )
    else:
        print(
            f"Administrador atualizado com sucesso. id={user.id} email={user.email} papel={user.role}",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
