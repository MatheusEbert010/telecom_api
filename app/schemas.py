"""Schemas Pydantic usados para entrada, saida e validacao da API."""

from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator


class UserRole(str, Enum):
    """Papeis aceitos pela API para controle de acesso."""

    ADMIN = "admin"
    USER = "user"


class StrictSchema(BaseModel):
    """Schema base que rejeita campos extras enviados pelo cliente."""

    model_config = ConfigDict(extra="forbid")


class UserBase(StrictSchema):
    """Campos compartilhados entre criacao e atualizacao de usuario."""

    name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    phone: str | None = Field(None, min_length=10, max_length=20)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Impede nomes com numeros e remove espacos excedentes."""
        if any(char.isdigit() for char in value):
            raise ValueError("Nome nao pode conter numeros")
        return value.strip()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        """Aceita apenas caracteres comuns de telefone."""
        if value:
            allowed_chars = set("0123456789 -()")
            if not all(char in allowed_chars for char in value):
                raise ValueError("Telefone deve conter apenas numeros e caracteres validos")
        return value


class UserCreate(UserBase):
    """Payload publico de cadastro de usuario."""

    password: str = Field(..., min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Exige senha forte e bloqueia combinacoes muito comuns."""
        if not any(char.isupper() for char in value):
            raise ValueError("Senha deve ter pelo menos 1 letra maiuscula")
        if not any(char.islower() for char in value):
            raise ValueError("Senha deve ter pelo menos 1 letra minuscula")
        if not any(char.isdigit() for char in value):
            raise ValueError("Senha deve ter pelo menos 1 numero")
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in value):
            raise ValueError("Senha deve ter pelo menos 1 caractere especial")

        common_passwords = ["password", "123456", "admin", "qwerty"]
        if value.lower() in common_passwords:
            raise ValueError("Senha muito comum, escolha uma mais forte")

        return value


class UserUpdate(UserBase):
    """Payload de atualizacao de usuario sem permitir troca de papel."""

    password: str | None = Field(None, min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_optional_password(cls, value: str | None) -> str | None:
        """Aplica as mesmas regras de senha apenas quando houver troca."""
        if value is None:
            return value

        if not any(char.isupper() for char in value):
            raise ValueError("Senha deve ter pelo menos 1 letra maiuscula")
        if not any(char.islower() for char in value):
            raise ValueError("Senha deve ter pelo menos 1 letra minuscula")
        if not any(char.isdigit() for char in value):
            raise ValueError("Senha deve ter pelo menos 1 numero")
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in value):
            raise ValueError("Senha deve ter pelo menos 1 caractere especial")

        common_passwords = ["password", "123456", "admin", "qwerty"]
        if value.lower() in common_passwords:
            raise ValueError("Senha muito comum, escolha uma mais forte")

        return value


class UserRoleUpdate(StrictSchema):
    """Payload exclusivo para troca explicita de papel de usuario."""

    role: UserRole


class UserLogin(BaseModel):
    """Credenciais usadas no fluxo de login."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)


class UserResponse(StrictSchema):
    """Resposta publica de usuario sem campos sensiveis."""

    id: int
    name: str
    email: EmailStr
    phone: str | None
    role: UserRole
    plan_id: int | None

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class PlanCreate(StrictSchema):
    """Payload de criacao de plano."""

    name: str = Field(..., min_length=3, max_length=100)
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    speed: int = Field(..., gt=0)

    @field_serializer("price")
    def serialize_price(self, value: Decimal) -> float:
        """Mantem preco como numero na resposta JSON."""
        return float(value)


class PlanResponse(PlanCreate):
    """Resposta publica de um plano cadastrado."""

    id: int

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class PlanListFilters(StrictSchema):
    """Conjunto de filtros aceitos na listagem de planos."""

    search: str | None = None
    min_speed: int | None = None
    max_speed: int | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    sort_by: Literal["name", "price", "speed"]
    sort_order: Literal["asc", "desc"]

    @field_serializer("min_price", "max_price")
    def serialize_optional_prices(self, value: Decimal | None) -> float | None:
        """Evita que Decimal saia como string nos filtros ecoados pela API."""
        return float(value) if value is not None else None


class PlanListResponse(StrictSchema):
    """Resposta paginada simplificada para listagem de planos."""

    page: int
    limit: int
    total: int
    total_pages: int
    data: list[PlanResponse]
    filters: PlanListFilters


class UserListFilters(StrictSchema):
    """Conjunto de filtros aceitos na listagem de usuarios."""

    search: str | None = None
    role: UserRole | None = None
    sort_by: Literal["name", "email", "created_at", "role"]
    sort_order: Literal["asc", "desc"]


class UserListResponse(StrictSchema):
    """Resposta da listagem administrativa de usuarios."""

    page: int
    limit: int
    total: int
    total_pages: int
    data: list[UserResponse]
    filters: UserListFilters


class MessageResponse(StrictSchema):
    """Resposta padrao para operacoes simples com mensagem."""

    message: str


class UserSubscriptionResponse(StrictSchema):
    """Resposta de vinculo entre usuario e plano."""

    message: str
    user: UserResponse


class UserPlanResponse(StrictSchema):
    """Resposta dedicada ao plano atualmente associado ao usuario autenticado."""

    user_id: int
    plan: PlanResponse


class AdminStatsResponse(StrictSchema):
    """Resumo administrativo com metricas basicas da base."""

    total_users: int
    total_admins: int
    total_plans: int
    users_with_plan: int
    users_without_plan: int


class TokenResponse(StrictSchema):
    """Resposta de autenticacao com access e refresh token."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(StrictSchema):
    """Payload para refresh e logout."""

    refresh_token: str = Field(..., min_length=20)


class SubscribePlan(StrictSchema):
    """Payload usado para assinar um plano existente."""

    plan_id: int = Field(..., gt=0)
