"""Fixtures compartilhadas para testes unitarios e de integracao."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "test-secret-key-with-minimum-32chars")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_bootstrap.db")
os.environ.setdefault("ENVIRONMENT", "test")

from app import schemas
from app.cache import cache
from app.main import app
from app.models import Base
from app.routers import auth as auth_router
from app.services import user_service
from app.telecom_db import get_db


@pytest.fixture
def db_session():
    """Cria uma sessao isolada em SQLite em memoria para cada teste."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    session = session_local()
    cache.enabled = False

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Cria um TestClient com override do banco e rate limit desativado."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    previous_limiter_state = auth_router.limiter.enabled
    auth_router.limiter.enabled = False

    with TestClient(app) as test_client:
        yield test_client

    auth_router.limiter.enabled = previous_limiter_state
    app.dependency_overrides.clear()


@pytest.fixture
def create_user_factory(db_session):
    """Fabrica helper para criar usuarios comuns ou admins nos testes."""

    def _create_user(
        *,
        name: str,
        email: str,
        phone: str,
        password: str = "Admin123!",
        role: schemas.UserRole = schemas.UserRole.USER,
    ):
        created_user = user_service.create_user(
            db_session,
            schemas.UserCreate(
                name=name,
                email=email,
                phone=phone,
                password=password,
            ),
        )

        if role != schemas.UserRole.USER:
            created_user = user_service.change_user_role(db_session, created_user.id, role)

        return created_user

    return _create_user


@pytest.fixture
def admin_user(create_user_factory):
    """Entrega um usuario administrador valido para testes de RBAC."""
    return create_user_factory(
        name="Admin User",
        email="admin@example.com",
        phone="11999990001",
        role=schemas.UserRole.ADMIN,
    )


@pytest.fixture
def regular_user(create_user_factory):
    """Entrega um usuario comum valido para testes autenticados."""
    return create_user_factory(
        name="Regular User",
        email="user@example.com",
        phone="11999990002",
    )


@pytest.fixture
def admin_token(client, admin_user):
    """Gera um access token de administrador pela rota real de login."""
    response = client.post(
        "/auth/login",
        json={"email": admin_user.email, "password": "Admin123!"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def user_token(client, regular_user):
    """Gera um access token de usuario comum pela rota real de login."""
    response = client.post(
        "/auth/login",
        json={"email": regular_user.email, "password": "Admin123!"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]
