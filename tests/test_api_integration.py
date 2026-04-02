"""Testes de integracao cobrindo os fluxos HTTP principais da API."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import schemas
from app.cache import cache
from app.main import app
from app.routers import auth as auth_router
from app.services import user_service
from app.telecom_db import get_db


def test_health_endpoint(client):
    """Garante que o endpoint de health responda com o formato esperado."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["service"] == "telecom-api"
    assert payload["version"] == "1.2.0"


def test_versioned_health_endpoint(client):
    """Mantem o endpoint de saude tambem sob o prefixo versionado."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["version"] == "1.2.0"


def test_readiness_endpoint_reports_database_and_cache_status(client):
    """Explicita o readiness das dependencias sem expor detalhes sensiveis."""
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["checks"]["database"] == "ok"
    assert payload["checks"]["cache"] == "desabilitado"


def test_login_refresh_and_logout_flow(client, regular_user):
    """Valida o fluxo completo de login, refresh token e logout."""
    login_response = client.post(
        "/auth/login",
        json={"email": regular_user.email, "password": "Admin123!"},
    )

    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert "access_token" in login_payload
    assert "refresh_token" in login_payload

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": login_payload["refresh_token"]},
    )

    assert refresh_response.status_code == 200
    refresh_payload = refresh_response.json()
    assert refresh_payload["access_token"] != login_payload["access_token"]
    assert refresh_payload["refresh_token"] != login_payload["refresh_token"]

    logout_response = client.post(
        "/auth/logout",
        json={"refresh_token": refresh_payload["refresh_token"]},
    )

    assert logout_response.status_code == 200
    assert logout_response.json() == {"message": "Logout realizado com sucesso"}

    reused_refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_payload["refresh_token"]},
    )

    assert reused_refresh_response.status_code == 401

    assert login_response.headers["cache-control"] == "no-store"
    assert refresh_response.headers["cache-control"] == "no-store"
    assert logout_response.headers["cache-control"] == "no-store"
    assert login_response.headers["pragma"] == "no-cache"


def test_refresh_rejeita_access_token_no_fluxo_de_renovacao(client, regular_user):
    """Impede que access token seja reutilizado no endpoint de refresh."""
    login_response = client.post(
        "/auth/login",
        json={"email": regular_user.email, "password": "Admin123!"},
    )

    assert login_response.status_code == 200

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": login_response.json()["access_token"]},
    )

    assert refresh_response.status_code == 401
    assert refresh_response.json()["code"] == "nao_autorizado"


def test_versioned_login_and_stats_flow(client, admin_user):
    """Valida o uso das rotas preferenciais em `/api/v1`."""
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "Admin123!"},
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    stats_response = client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert stats_response.status_code == 200
    payload = stats_response.json()
    assert payload["total_users"] >= 1
    assert payload["total_admins"] >= 1


def test_users_me_returns_authenticated_user(client, user_token, regular_user):
    """Confirma que `/users/me` devolve o proprio usuario autenticado."""
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == regular_user.email


def test_users_me_rejeita_refresh_token_como_credencial(client, regular_user):
    """Bloqueia refresh token em rotas que exigem access token valido."""
    login_response = client.post(
        "/auth/login",
        json={"email": regular_user.email, "password": "Admin123!"},
    )

    assert login_response.status_code == 200

    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {login_response.json()['refresh_token']}"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "nao_autorizado"


def test_users_me_plan_returns_active_plan(client, admin_token, user_token, regular_user):
    """Entrega um endpoint dedicado ao plano do usuario autenticado."""
    create_plan_response = client.post(
        "/plans/",
        json={"name": "Fibra 800", "price": 179.9, "speed": 800},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_plan_response.status_code == 201
    plan_id = create_plan_response.json()["id"]

    subscribe_response = client.post(
        f"/users/{regular_user.id}/subscribe",
        json={"plan_id": plan_id},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert subscribe_response.status_code == 200

    response = client.get(
        "/users/me/plan",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == regular_user.id
    assert payload["plan"]["id"] == plan_id
    assert payload["plan"]["speed"] == 800


def test_regular_user_cannot_list_users(client, user_token):
    """Impede que usuario comum acesse listagem administrativa de usuarios."""
    response = client.get(
        "/users/",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "acesso_negado"


def test_admin_can_list_users_with_filters(client, admin_token, admin_user, regular_user):
    """Permite ao admin listar usuarios usando filtros e ordenacao."""
    response = client.get(
        "/users/",
        params={"search": "user", "sort_by": "email", "sort_order": "asc"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert payload["filters"]["search"] == "user"
    returned_emails = [user["email"] for user in payload["data"]]
    assert regular_user.email in returned_emails
    assert all("password" not in user for user in payload["data"])


def test_cors_allows_patch_preflight_for_role_update(client):
    """Garante preflight valido para consumidores web da API."""
    response = client.options(
        "/users/1/role",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "PATCH",
        },
    )

    assert response.status_code == 200
    assert "PATCH" in response.headers["access-control-allow-methods"]


def test_admin_can_change_user_role(client, admin_token, regular_user):
    """Permite a troca explicita de papel apenas pelo fluxo administrativo."""
    response = client.patch(
        f"/users/{regular_user.id}/role",
        json={"role": schemas.UserRole.ADMIN.value},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == schemas.UserRole.ADMIN.value


def test_user_cannot_access_another_user_profile(client, user_token, admin_user):
    """Bloqueia acesso de um usuario comum ao perfil de outro usuario."""
    response = client.get(
        f"/users/{admin_user.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 403


def test_admin_can_create_plan_and_user_can_list_it(client, admin_token):
    """Valida criacao administrativa de plano e leitura publica na listagem."""
    create_response = client.post(
        "/plans/",
        json={"name": "Fibra 600", "price": 129.9, "speed": 600},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert create_response.status_code == 201
    created_plan = create_response.json()
    assert created_plan["name"] == "Fibra 600"

    list_response = client.get("/plans/", params={"search": "Fibra"})

    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["page"] == 1
    assert payload["limit"] == 10
    assert payload["total"] >= 1
    assert payload["total_pages"] >= 1
    assert any(plan["name"] == "Fibra 600" for plan in payload["data"])


def test_user_can_subscribe_to_plan(client, admin_token, user_token, regular_user):
    """Garante que um usuario autenticado consiga assinar um plano valido."""
    create_plan_response = client.post(
        "/plans/",
        json={"name": "Fibra 700", "price": 149.9, "speed": 700},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_plan_response.status_code == 201
    plan_id = create_plan_response.json()["id"]

    subscribe_response = client.post(
        f"/users/{regular_user.id}/subscribe",
        json={"plan_id": plan_id},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert subscribe_response.status_code == 200
    payload = subscribe_response.json()
    assert payload["message"] == "Plano assinado com sucesso"
    assert payload["user"]["plan_id"] == plan_id


def test_user_can_cancel_subscription(client, admin_token, user_token, regular_user):
    """Permite cancelar o plano ja vinculado ao usuario autenticado."""
    create_plan_response = client.post(
        "/plans/",
        json={"name": "Fibra 900", "price": 199.9, "speed": 900},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_plan_response.status_code == 201
    plan_id = create_plan_response.json()["id"]

    subscribe_response = client.post(
        f"/users/{regular_user.id}/subscribe",
        json={"plan_id": plan_id},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert subscribe_response.status_code == 200

    cancel_response = client.delete(
        f"/users/{regular_user.id}/subscribe",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert cancel_response.status_code == 200
    payload = cancel_response.json()
    assert payload["message"] == "Plano cancelado com sucesso"
    assert payload["user"]["plan_id"] is None


def test_admin_can_view_stats(client, admin_token, admin_user, regular_user):
    """Expone metricas administrativas consolidadas da base."""
    response = client.get(
        "/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_users"] >= 2
    assert payload["total_admins"] >= 1
    assert payload["users_without_plan"] >= 1


def test_invalid_plan_filter_range_returns_400(client):
    """Rejeita filtros incoerentes antes de consultar o banco."""
    response = client.get("/plans/", params={"min_price": 200, "max_price": 100})

    assert response.status_code == 400
    assert response.json()["code"] == "requisicao_invalida"


def test_validation_errors_return_code_and_error_list(client):
    """Padroniza erros de validacao com codigo legivel para clientes da API."""
    response = client.post(
        "/users/",
        json={"name": "A", "email": "invalido", "phone": "123", "password": "fraca"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "erro_validacao"
    assert payload["detail"] == "Dados de entrada invalidos"
    assert payload["request_id"] == response.headers["x-request-id"]
    assert isinstance(payload["errors"], list)


def test_create_user_duplicate_email_returns_generic_error(client, regular_user):
    """Mantem o cadastro publico sem confirmar se um email ja existe na base."""
    response = client.post(
        "/users/",
        json={
            "name": "Outro Usuario",
            "email": regular_user.email,
            "phone": "11999997777",
            "password": "Admin123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Nao foi possivel concluir o cadastro com os dados informados"


def test_create_user_duplicate_email_is_case_insensitive(client, regular_user):
    """Evita burlar duplicidade apenas trocando a capitalizacao do email."""
    response = client.post(
        "/users/",
        json={
            "name": "Outro Usuario",
            "email": regular_user.email.upper(),
            "phone": "11999997777",
            "password": "Admin123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Nao foi possivel concluir o cadastro com os dados informados"


def test_create_user_rejects_password_above_bcrypt_utf8_limit(client):
    """Falha cedo quando a senha ultrapassa 72 bytes reais em UTF-8."""
    response = client.post(
        "/users/",
        json={
            "name": "Usuario Unicode",
            "email": "unicode@example.com",
            "phone": "11999998888",
            "password": "A" + ("á" * 36) + "1!",
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "erro_validacao"


def test_login_rate_limit_returns_429_when_enabled():
    """Exercita o limiter real no endpoint de login."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    from app.models import Base

    Base.metadata.create_all(bind=engine)
    db_session = session_local()
    cache.enabled = False
    auth_router.limiter.enabled = True
    auth_router.limiter.reset()

    user_service.create_user(
        db_session,
        schemas.UserCreate(
            name="Rate Limit User",
            email="ratelimit@example.com",
            phone="11999990009",
            password="Admin123!",
        ),
    )

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app, raise_server_exceptions=False) as rate_limited_client:
            last_response = None
            for _ in range(6):
                last_response = rate_limited_client.post(
                    "/auth/login",
                    json={"email": "ratelimit@example.com", "password": "Admin123!"},
                )
    finally:
        app.dependency_overrides.clear()
        auth_router.limiter.reset()
        db_session.close()
        Base.metadata.drop_all(bind=engine)

    assert last_response is not None
    assert last_response.status_code == 429


def test_api_preserva_request_id_informado_pelo_cliente(client):
    """Devolve o mesmo identificador enviado pelo cliente para facilitar rastreio."""
    response = client.get(
        "/health",
        headers={"X-Request-ID": "req-cliente-123"},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-cliente-123"


def test_api_ignora_request_id_invalido_enviado_pelo_cliente(client):
    """Evita reaproveitar cabecalhos malformados como identificador de correlacao."""
    response = client.get(
        "/health",
        headers={"X-Request-ID": "id com espaco"},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] != "id com espaco"


def test_versioned_users_me_plan_returns_not_found_without_subscription(client, user_token):
    """Replica o contrato do endpoint dedicado tambem sob `/api/v1`."""
    response = client.get(
        "/api/v1/users/me/plan",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 404
    payload = response.json()
    assert payload["code"] == "recurso_nao_encontrado"
