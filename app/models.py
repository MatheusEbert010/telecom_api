# Importações necessárias do SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship

# Importa a base do banco configurada no projeto
from .telecom_db import Base

# Importa datetime para registrar data de criação
from datetime import datetime

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