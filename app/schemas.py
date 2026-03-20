from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from enum import Enum

# Enum para roles
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

###SCHEMAS PARA USUÁRIOS E PLANOS
class UserCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.USER

    @validator("password")
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Senha deve ter pelo menos 1 letra maiúscula")
        if not any(c.islower() for c in v):
            raise ValueError("Senha deve ter pelo menos 1 letra minúscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("Senha deve ter pelo menos 1 número")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Senha deve ter pelo menos 1 caractere especial")
        # Verificar senhas comuns
        common_passwords = ["password", "123456", "admin", "qwerty"]
        if v.lower() in common_passwords:
            raise ValueError("Senha muito comum, escolha uma mais forte")
        return v

    @validator("name")
    def validate_name(cls, v):
        if any(char.isdigit() for char in v):
            raise ValueError("Nome não pode conter números")
        return v.strip()

    @validator("phone")
    def validate_phone(cls, v):
        if v:
            # Permitir apenas números, espaços, hífens e parênteses
            allowed_chars = set("0123456789 -()")
            if not all(c in allowed_chars for c in v):
                raise ValueError("Telefone deve conter apenas números e caracteres válidos")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str]
    role: UserRole
    plan_id: Optional[int]

    class Config:
        from_attributes = True
        extra = "forbid"

###CONFIGURAÇÃO PARA USAR MODELOS ORM
class PlanCreate(BaseModel):
    name: str
    price: float
    speed: int
class PlanResponse(PlanCreate):
    id: int

    class Config:
        from_attributes = True
        extra = "forbid"

###SCHEMAS PARA TOKENS
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

###SCHEMA PARA INSCRIÇÃO DE USUÁRIO EM UM PLANO        
class SubscribePlan(BaseModel):
    plan_id: int