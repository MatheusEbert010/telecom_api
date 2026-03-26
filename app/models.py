"""Modelos ORM que representam as tabelas principais do sistema."""

from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from .telecom_db import Base
from .time_utils import utc_now_naive


class UserRole(str, Enum):
    """Valores permitidos para o papel de um usuario no sistema."""

    ADMIN = "admin"
    USER = "user"


class User(Base):
    """Tabela de usuarios com dados cadastrais, papel e plano contratado."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    phone = Column(String(20))
    role = Column(String(20), default=UserRole.USER, nullable=False, index=True)
    # Mantem compatibilidade com colunas sem timezone explicito.
    created_at = Column(DateTime, default=utc_now_naive)
    plan_id = Column(Integer, ForeignKey("plans.id"), index=True)
    plan = relationship("Plan", back_populates="users")
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Plan(Base):
    """Tabela de planos comercializados pela operadora."""

    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    speed = Column(Integer, nullable=False)
    users = relationship("User", back_populates="plan")


class RefreshToken(Base):
    """Tabela de refresh tokens persistidos para renovacao de sessao."""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    # Mantem compatibilidade com colunas sem timezone explicito.
    created_at = Column(DateTime, default=utc_now_naive)
    user = relationship("User", back_populates="refresh_tokens")
