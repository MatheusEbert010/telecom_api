"""Testes focados em seguranca, contratos de resposta e regras de negocio."""

import logging
from datetime import timedelta

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute
from pydantic import ValidationError

from app import schemas
from app.cache import Cache
from app.config import settings
from app.crud import user_repository
from app.logging_config import RequestIdFilter, SafeFormatter
from app.main import app
from app.models import User
from app.request_context import reset_request_id, set_request_id
from app.routers import plans as plans_router
from app.routers import users as users_router
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_refresh_token,
)
from app.services import plan_service, user_service
from app.time_utils import utc_now_naive


def test_user_create_rejects_role_field():
    """Impede que o cadastro publico envie o campo de papel do usuario."""
    with pytest.raises(ValidationError):
        schemas.UserCreate(
            name="Matheus Ebert",
            email="matheus@example.com",
            phone="11999998888",
            password="Admin123!",
            role="admin",
        )


def test_create_user_defaults_to_user_role(db_session):
    """Garante que o service sempre crie usuarios com papel comum."""
    created_user = user_service.create_user(
        db_session,
        schemas.UserCreate(
            name="Matheus Ebert",
            email="matheus@example.com",
            phone="11999998888",
            password="Admin123!",
        ),
    )

    assert created_user.role == schemas.UserRole.USER.value


def test_update_user_keeps_existing_role(db_session):
    """Confirma que a atualizacao comum nao altera o papel do usuario."""
    created_user = user_service.create_user(
        db_session,
        schemas.UserCreate(
            name="Matheus Ebert",
            email="matheus@example.com",
            phone="11999998888",
            password="Admin123!",
        ),
    )

    updated_user = user_service.update_user(
        db_session,
        created_user.id,
        schemas.UserUpdate(
            name="Matheus de Souza Ebert",
            email="matheus@example.com",
            phone="11999997777",
        ),
    )

    assert updated_user.role == schemas.UserRole.USER.value


def test_admin_role_change_is_explicit(db_session):
    """Valida que a troca de papel acontece apenas pela operacao especifica."""
    created_user = user_service.create_user(
        db_session,
        schemas.UserCreate(
            name="Matheus Ebert",
            email="matheus@example.com",
            phone="11999998888",
            password="Admin123!",
        ),
    )

    updated_user = user_service.change_user_role(
        db_session,
        created_user.id,
        schemas.UserRole.ADMIN,
    )

    assert updated_user.role == schemas.UserRole.ADMIN.value


def test_ensure_admin_user_creates_admin_when_email_does_not_exist(db_session):
    """Permite bootstrap controlado de administrador sem passar pela API publica."""
    admin_user, created = user_service.ensure_admin_user(
        db_session,
        name="Admin Bootstrap",
        email="admin.bootstrap@example.com",
        phone="11999990000",
        password="Admin123!",
    )

    assert created is True
    assert admin_user.role == schemas.UserRole.ADMIN.value
    assert admin_user.email == "admin.bootstrap@example.com"


def test_ensure_admin_user_promotes_existing_user_to_admin(db_session):
    """Promove usuario existente para admin de forma idempotente."""
    created_user = user_service.create_user(
        db_session,
        schemas.UserCreate(
            name="Usuario Comum",
            email="comum@example.com",
            phone="11999998888",
            password="Admin123!",
        ),
    )

    admin_user, created = user_service.ensure_admin_user(
        db_session,
        name="Usuario Promovido",
        email="comum@example.com",
        phone="11999997777",
        password="NovaSenha123!",
    )

    assert created is False
    assert admin_user.id == created_user.id
    assert admin_user.name == "Usuario Promovido"
    assert admin_user.phone == "11999997777"
    assert admin_user.role == schemas.UserRole.ADMIN.value


def test_users_me_route_is_registered_before_user_id_route():
    """Evita conflito de roteamento entre `/me` e `/{user_id}`."""
    user_routes = [
        route.path
        for route in app.routes
        if isinstance(route, APIRoute) and route.path.startswith("/users")
    ]

    assert user_routes.index("/users/me") < user_routes.index("/users/{user_id}")
    assert user_routes.index("/users/me/plan") < user_routes.index("/users/{user_id}")


def test_versioned_users_me_route_is_registered_before_user_id_route():
    """Preserva a ordem segura das rotas tambem na versao `/api/v1`."""
    user_routes = [
        route.path
        for route in app.routes
        if isinstance(route, APIRoute) and route.path.startswith("/api/v1/users")
    ]

    assert user_routes.index("/api/v1/users/me") < user_routes.index("/api/v1/users/{user_id}")
    assert user_routes.index("/api/v1/users/me/plan") < user_routes.index(
        "/api/v1/users/{user_id}"
    )


def test_sensitive_user_routes_use_safe_response_models():
    """Garante que respostas de usuario usem schemas sem campos sensiveis."""
    user_routes = {
        route.path: route
        for route in app.routes
        if isinstance(route, APIRoute) and route.path.startswith("/users")
    }

    assert user_routes["/users/"].response_model is schemas.UserListResponse
    assert user_routes["/users/me/plan"].response_model is schemas.UserPlanResponse
    assert user_routes["/users/{user_id}/subscribe"].response_model is schemas.UserSubscriptionResponse


def test_auth_and_plan_routes_use_safe_response_models():
    """Confirma o contrato publico das rotas de auth e planos."""
    routes = {route.path: route for route in app.routes if isinstance(route, APIRoute)}

    assert routes["/admin/stats"].response_model is schemas.AdminStatsResponse
    assert routes["/api/v1/admin/stats"].response_model is schemas.AdminStatsResponse
    assert routes["/auth/login"].response_model is schemas.TokenResponse
    assert routes["/api/v1/auth/login"].response_model is schemas.TokenResponse
    assert routes["/auth/refresh"].response_model is schemas.TokenResponse
    assert routes["/auth/logout"].response_model is schemas.MessageResponse
    assert routes["/plans/"].response_model is schemas.PlanListResponse
    assert routes["/api/v1/plans/"].response_model is schemas.PlanListResponse
    assert "/plans/{user_id}/subscribe" not in routes


def test_cancel_subscription_requires_existing_plan(db_session):
    """Evita cancelamento redundante quando o usuario ainda nao possui plano."""
    created_user = user_service.create_user(
        db_session,
        schemas.UserCreate(
            name="Matheus Ebert",
            email="matheus@example.com",
            phone="11999998888",
            password="Admin123!",
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        user_service.cancel_plan_subscription(db_session, created_user.id)

    assert exc_info.value.status_code == 400
    assert "nao possui plano" in exc_info.value.detail


def test_get_user_plan_requires_existing_subscription(db_session):
    """Explicita que o endpoint dedicado falha quando nao ha plano assinado."""
    created_user = user_service.create_user(
        db_session,
        schemas.UserCreate(
            name="Matheus Ebert",
            email="matheus@example.com",
            phone="11999998888",
            password="Admin123!",
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        user_service.get_user_plan(db_session, created_user.id)

    assert exc_info.value.status_code == 404
    assert "nao possui plano" in exc_info.value.detail


def test_admin_cannot_delete_own_account():
    """Bloqueia exclusao da propria conta por um administrador autenticado."""
    admin_user = User(
        id=10,
        name="Admin User",
        email="admin@example.com",
        password="hashed-password",
        role=schemas.UserRole.ADMIN.value,
    )

    with pytest.raises(HTTPException) as exc_info:
        users_router.delete_user(user_id=10, current_user=admin_user, db=None)

    assert exc_info.value.status_code == 400
    assert "propria conta" in exc_info.value.detail


def test_refresh_tokens_are_stored_hashed_and_support_lookup(db_session):
    """Confirma que refresh tokens sao persistidos apenas na forma de hash."""
    created_user = user_service.create_user(
        db_session,
        schemas.UserCreate(
            name="Matheus Ebert",
            email="matheus@example.com",
            phone="11999998888",
            password="Admin123!",
        ),
    )

    raw_token = "sample-refresh-token-very-secure"
    user_repository.create_refresh_token(
        db_session,
        {
            "token": raw_token,
            "user_id": created_user.id,
            "expires_at": utc_now_naive() + timedelta(days=1),
        },
    )

    stored_token = db_session.query(user_repository.models.RefreshToken).first()

    assert stored_token is not None
    assert stored_token.token == hash_refresh_token(raw_token)
    assert stored_token.token != raw_token
    assert user_repository.get_refresh_token(db_session, raw_token) is not None


def test_access_and_refresh_tokens_include_claims_de_seguranca():
    """Inclui `iss`, `aud` e `token_type` para endurecer o contrato do JWT."""
    access_token = create_access_token({"sub": "admin@example.com"})
    refresh_token = create_refresh_token({"sub": "admin@example.com"})

    access_payload = decode_token(access_token)
    refresh_payload = decode_token(refresh_token)

    assert access_payload["iss"] == settings.jwt_issuer
    assert access_payload["aud"] == settings.jwt_audience
    assert access_payload["token_type"] == "access"
    assert refresh_payload["iss"] == settings.jwt_issuer
    assert refresh_payload["aud"] == settings.jwt_audience
    assert refresh_payload["token_type"] == "refresh"


def test_delete_refresh_token_accepts_raw_token(db_session):
    """Mantem compatibilidade com remocao por token bruto no fluxo legado."""
    created_user = user_service.create_user(
        db_session,
        schemas.UserCreate(
            name="Matheus Ebert",
            email="matheus@example.com",
            phone="11999998888",
            password="Admin123!",
        ),
    )

    raw_token = "sample-refresh-token-very-secure"
    user_repository.create_refresh_token(
        db_session,
        {
            "token": raw_token,
            "user_id": created_user.id,
            "expires_at": utc_now_naive() + timedelta(days=1),
        },
    )

    deleted = user_repository.delete_refresh_token(db_session, raw_token)

    assert deleted is not None
    assert user_repository.get_refresh_token(db_session, raw_token) is None


def test_delete_user_also_removes_refresh_tokens(db_session):
    """Evita tokens orfaos ao remover usuario em bancos relacionais como MySQL."""
    created_user = user_service.create_user(
        db_session,
        schemas.UserCreate(
            name="Matheus Ebert",
            email="matheus@example.com",
            phone="11999998888",
            password="Admin123!",
        ),
    )

    raw_token = "sample-refresh-token-very-secure"
    user_repository.create_refresh_token(
        db_session,
        {
            "token": raw_token,
            "user_id": created_user.id,
            "expires_at": utc_now_naive() + timedelta(days=1),
        },
    )

    deleted_user = user_service.delete_user(db_session, created_user.id)

    assert deleted_user is not None
    assert user_repository.get_refresh_token(db_session, raw_token) is None


def test_plan_filters_reject_invalid_ranges():
    """Impede ranges inconsistentes de preco e velocidade na listagem."""
    with pytest.raises(HTTPException) as speed_exc:
        plans_router.list_plans(
            search=None,
            min_speed=500,
            max_speed=100,
            min_price=None,
            max_price=None,
            sort_by="price",
            sort_order="asc",
            db=None,
        )

    assert speed_exc.value.status_code == 400
    assert "min_speed" in speed_exc.value.detail

    with pytest.raises(HTTPException) as price_exc:
        plans_router.list_plans(
            search=None,
            min_speed=None,
            max_speed=None,
            min_price=300,
            max_price=100,
            sort_by="price",
            sort_order="asc",
            db=None,
        )

    assert price_exc.value.status_code == 400
    assert "min_price" in price_exc.value.detail


def test_create_plan_rejects_duplicate_name(db_session):
    """Bloqueia a criacao de planos com nomes repetidos."""
    plan = schemas.PlanCreate(name="Fibra 500", price=99.9, speed=500)

    plan_service.create_plan(db_session, plan)

    with pytest.raises(HTTPException) as exc_info:
        plan_service.create_plan(db_session, plan)

    assert exc_info.value.status_code == 400
    assert "Ja existe um plano" in exc_info.value.detail


def test_cache_serializes_sqlalchemy_models():
    """Garante que o cache converta modelos ORM em JSON valido."""

    class DummyRedis:
        """Duble minimo do Redis para inspecionar o valor gravado."""

        def __init__(self):
            self.last_value = None

        def setex(self, key, expire, value):
            self.last_value = value
            return True

    cache_instance = Cache.__new__(Cache)
    cache_instance.enabled = True
    cache_instance.redis_client = DummyRedis()

    user = User(
        id=1,
        name="Matheus Ebert",
        email="matheus@example.com",
        password="hashed-password",
        role=schemas.UserRole.USER.value,
    )

    result = cache_instance.set("users:list:1", {"total": 1, "data": [user]}, expire=60)

    assert result is True
    assert '"email": "matheus@example.com"' in cache_instance.redis_client.last_value


def test_cache_clear_pattern_uses_scan_iter():
    """Evita o uso de KEYS para limpar cache em ambiente maior."""

    class DummyRedis:
        """Duble minimo do Redis para capturar a estrategia de limpeza."""

        def __init__(self):
            self.deleted_keys = ()

        def scan_iter(self, match):
            assert match == "users:list:*"
            yield "users:list:1"
            yield "users:list:2"

        def delete(self, *keys):
            self.deleted_keys = keys
            return len(keys)

    cache_instance = Cache.__new__(Cache)
    cache_instance.enabled = True
    cache_instance.redis_client = DummyRedis()

    result = cache_instance.clear_pattern("users:list:*")

    assert result is True
    assert cache_instance.redis_client.deleted_keys == ("users:list:1", "users:list:2")


def test_logging_inclui_request_id_e_redige_campos_sensiveis():
    """Mantem rastreabilidade e evita vazar credenciais em mensagens de log."""
    token = set_request_id("req-teste-log")

    try:
        record = logging.makeLogRecord(
            {
                "name": "app.tests",
                "levelno": logging.INFO,
                "levelname": "INFO",
                "msg": "Authorization=Bearer123 password=abc123",
            }
        )

        filtro = RequestIdFilter()
        formatter = SafeFormatter("%(request_id)s %(message)s")

        assert filtro.filter(record) is True
        rendered = formatter.format(record)
    finally:
        reset_request_id(token)

    assert rendered.startswith("req-teste-log ")
    assert "Bearer123" not in rendered
    assert "abc123" not in rendered
    assert "DADO_SENSIVEL_REDACTED" in rendered
