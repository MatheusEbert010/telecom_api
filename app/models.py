"""Modelos ORM que representam as tabelas principais do sistema."""

from enum import Enum

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
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
    role = Column(String(20), default=UserRole.USER, nullable=False)
    # Mantem compatibilidade com colunas sem timezone explicito.
    created_at = Column(DateTime, default=utc_now_naive)
    plan_id = Column(Integer, ForeignKey("plans.id"))
    plan = relationship("Plan", back_populates="users")


class Plan(Base):
    """Tabela de planos comercializados pela operadora."""

    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    speed = Column(Integer)
    users = relationship("User", back_populates="plan")


class RefreshToken(Base):
    """Tabela de refresh tokens persistidos para renovacao de sessao."""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    # Mantem compatibilidade com colunas sem timezone explicito.
    created_at = Column(DateTime, default=utc_now_naive)
    user = relationship("User")
