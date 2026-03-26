"""Testes de integracao com MySQL real para fluxos criticos da aplicacao."""

from __future__ import annotations

import os
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import schemas
from app.crud import user_repository
from app.models import Plan, RefreshToken, User
from app.security import hash_refresh_token
from app.services import plan_service, user_service
from app.time_utils import utc_now_naive

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_MYSQL_INTEGRATION_TESTS") != "1",
    reason="Testes de MySQL executam apenas quando explicitamente habilitados",
)


@pytest.fixture
def mysql_db_session():
    """Abre uma sessao dedicada ao banco MySQL configurado para a pipeline."""
    database_url = os.environ["DATABASE_URL"]
    engine = create_engine(database_url, pool_pre_ping=True, future=True)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_local()
    test_prefix = f"mysql-integration-{uuid4().hex[:8]}"

    try:
        yield session, test_prefix
    finally:
        session.rollback()
        created_users = session.query(User).filter(User.email.like(f"{test_prefix}%")).all()
        created_user_ids = [user.id for user in created_users]

        if created_user_ids:
            session.query(RefreshToken).filter(RefreshToken.user_id.in_(created_user_ids)).delete(
                synchronize_session=False
            )
            session.query(User).filter(User.id.in_(created_user_ids)).delete(
                synchronize_session=False
            )

        session.query(Plan).filter(Plan.name.like(f"{test_prefix}%")).delete(
            synchronize_session=False
        )
        session.commit()
        session.close()
        engine.dispose()


def test_mysql_fluxo_principal_de_usuario_e_plano(mysql_db_session):
    """Valida criacao, assinatura, consulta dedicada e cancelamento em MySQL real."""
    db_session, test_prefix = mysql_db_session

    admin_user, _ = user_service.ensure_admin_user(
        db_session,
        name="Administrador CI",
        email=f"{test_prefix}-admin@example.com",
        phone="11999990001",
        password="Admin123!",
    )
    regular_user = user_service.create_user(
        db_session,
        schemas.UserCreate(
            name="Usuario Integracao",
            email=f"{test_prefix}-user@example.com",
            phone="11999990002",
            password="Admin123!",
        ),
    )
    created_plan = plan_service.create_plan(
        db_session,
        schemas.PlanCreate(
            name=f"{test_prefix}-fibra-1000",
            price="199.90",
            speed=1000,
        ),
    )

    subscribed_user = user_service.subscribe_plan(db_session, regular_user.id, created_plan.id)
    current_plan = user_service.get_user_plan(db_session, regular_user.id)
    assert subscribed_user.plan_id == created_plan.id
    assert current_plan["plan"].speed == 1000

    updated_user = user_service.cancel_plan_subscription(db_session, regular_user.id)
    admin_stats = user_repository.get_admin_stats(db_session)

    assert admin_user.role == schemas.UserRole.ADMIN.value
    assert updated_user.plan_id is None
    assert admin_stats["total_admins"] >= 1
    assert admin_stats["total_plans"] >= 1


def test_mysql_refresh_token_permanece_hashado(mysql_db_session):
    """Confirma persistencia hashada e limpeza de refresh token no MySQL real."""
    db_session, test_prefix = mysql_db_session

    created_user = user_service.create_user(
        db_session,
        schemas.UserCreate(
            name="Usuario Token",
            email=f"{test_prefix}-token@example.com",
            phone="11999990003",
            password="Admin123!",
        ),
    )

    raw_token = f"refresh-token-{uuid4().hex}-valido"
    user_repository.create_refresh_token(
        db_session,
        {
            "token": raw_token,
            "user_id": created_user.id,
            "expires_at": utc_now_naive() + timedelta(days=1),
        },
    )

    stored_token = (
        db_session.query(RefreshToken)
        .filter(RefreshToken.user_id == created_user.id)
        .order_by(RefreshToken.id.desc())
        .first()
    )

    assert stored_token is not None
    assert stored_token.token == hash_refresh_token(raw_token)
    assert user_repository.get_refresh_token(db_session, raw_token) is not None

    user_service.delete_user(db_session, created_user.id)

    assert user_repository.get_refresh_token(db_session, raw_token) is None
