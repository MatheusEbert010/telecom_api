# Importações necessárias do SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from enum import Enum

# Importa a base do banco configurada no projeto
from .telecom_db import Base

# Importa datetime para registrar data de criação
from datetime import datetime

# Enum para roles de usuário
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

# ==========================================================
# MODELO ORM: USER
# Representa a tabela de usuários no banco de dados
# ==========================================================
class User(Base):
    __tablename__ = "users"

    # ID único do usuário
    id = Column(Integer, primary_key=True, index=True)

    # Nome do usuário
    name = Column(String(100), nullable=False)

    # Email do usuário (único no sistema)
    email = Column(String(150), unique=True, nullable=False)

    # Senha criptografada do usuário
    # 255 é um tamanho seguro para armazenar hashes (bcrypt)
    password = Column(String(255), nullable=False)

    # Telefone do usuário
    phone = Column(String(20))

    # Role do usuário (admin ou user)
    role = Column(String(20), default=UserRole.USER, nullable=False)

    # Data de criação do registro
    created_at = Column(DateTime, default=datetime.utcnow)

    # Chave estrangeira para o plano associado ao usuário
    plan_id = Column(Integer, ForeignKey("plans.id"))

    # Relacionamento ORM com o modelo Plan
    # Permite acessar user.plan diretamente
    plan = relationship("Plan", back_populates="users")


# ==========================================================
# MODELO ORM: PLAN
# Representa os planos de telecom disponíveis
# ==========================================================
class Plan(Base):
    __tablename__ = "plans"

    # ID único do plano
    id = Column(Integer, primary_key=True, index=True)

    # Nome do plano
    name = Column(String(100), nullable=False)

    # Preço do plano
    price = Column(Float, nullable=False)

    # Velocidade do plano (ex: 300 Mbps)
    speed = Column(Integer)

    # Relacionamento com usuários
    # Permite acessar plan.users
    users = relationship("User", back_populates="plan")


# ==========================================================
# MODELO ORM: REFRESH TOKEN
# Representa os tokens de refresh para autenticação
# ==========================================================
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    # ID único do token
    id = Column(Integer, primary_key=True, index=True)

    # Token de refresh (único)
    token = Column(String(500), unique=True, nullable=False)

    # ID do usuário associado
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Data de expiração
    expires_at = Column(DateTime, nullable=False)

    # Data de criação
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamento com usuário
    user = relationship("User")