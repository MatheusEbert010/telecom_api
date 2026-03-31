"""Limpa os dados operacionais e recria um conjunto inicial para demonstracao."""

from __future__ import annotations

from decimal import Decimal

from app import models, schemas
from app.services import plan_service, user_service
from app.telecom_db import SessionLocal

ADMIN_NAME = "Matheus Atlas"
ADMIN_EMAIL = "matheus.admin@telecomdemo.com"
ADMIN_PHONE = "11983214567"
ADMIN_PASSWORD = "MatheusAdmin@2026!"
ADMIN_STREET = "Rua das Palmeiras"
ADMIN_NEIGHBORHOOD = "Centro"
ADMIN_ADDRESS_NUMBER = "145"
ADMIN_ADDRESS_COMPLEMENT = "Sala 4"
ADMIN_CEP = "01000-000"

DEFAULT_PLANS = [
    {"name": "Fibra Essencial", "price": Decimal("89.90"), "speed": 300},
    {"name": "Fibra Prime", "price": Decimal("129.90"), "speed": 600},
    {"name": "Fibra Ultra", "price": Decimal("189.90"), "speed": 1000},
]


def reset_database() -> None:
    """Apaga usuarios, tokens e planos para recomecar a base de demonstracao."""
    db = SessionLocal()
    try:
        db.query(models.RefreshToken).delete()
        db.query(models.User).delete()
        db.query(models.Plan).delete()
        db.commit()
    finally:
        db.close()


def seed_database() -> None:
    """Cria o admin inicial e um catalogo minimo de planos."""
    db = SessionLocal()
    try:
        admin_user, created = user_service.ensure_admin_user(
            db,
            name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            phone=ADMIN_PHONE,
        )
        admin_user.street = ADMIN_STREET
        admin_user.neighborhood = ADMIN_NEIGHBORHOOD
        admin_user.address_number = ADMIN_ADDRESS_NUMBER
        admin_user.address_complement = ADMIN_ADDRESS_COMPLEMENT
        admin_user.cep = ADMIN_CEP
        db.commit()
        db.refresh(admin_user)
        admin_summary = {
            "name": admin_user.name,
            "email": admin_user.email,
        }

        created_plans: list[str] = []
        for raw_plan in DEFAULT_PLANS:
            plan = schemas.PlanCreate(**raw_plan)
            created_plan = plan_service.create_plan(db, plan)
            created_plans.append(f"{created_plan.name} ({created_plan.speed} Mbps)")
    finally:
        db.close()

    action = "criado" if created else "atualizado"
    print("Base redefinida com sucesso.")
    print(f"Administrador {action}: {admin_summary['name']} <{admin_summary['email']}>")
    print(f"Senha inicial: {ADMIN_PASSWORD}")
    print("Planos criados:")
    for plan_name in created_plans:
        print(f"- {plan_name}")


def main() -> int:
    """Executa o reset e o seed da base de demonstracao."""
    reset_database()
    seed_database()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
