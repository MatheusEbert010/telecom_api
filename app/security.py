"""Utilitarios de senha e token usados pela camada de autenticacao."""

import hashlib
from datetime import timedelta
from uuid import uuid4

import bcrypt
from jose import jwt

from .config import settings
from .time_utils import utc_now

# O bcrypt considera apenas os primeiros 72 bytes da senha.
BCRYPT_MAX_LENGTH = 72
# Hash fixo para reduzir diferenca de tempo entre usuarios validos e invalidos.
DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt())


def hash_password(password: str) -> bytes:
    """Gera o hash bcrypt de uma senha respeitando o limite do algoritmo."""
    if isinstance(password, str):
        password_bytes = password.encode("utf-8")
    else:
        password_bytes = password

    if len(password_bytes) > BCRYPT_MAX_LENGTH:
        password_bytes = password_bytes[:BCRYPT_MAX_LENGTH]

    return bcrypt.hashpw(password_bytes, bcrypt.gensalt())


def verify_password(plain_password, hashed_password) -> bool:
    """Compara senha em texto puro com o hash persistido no banco."""
    if isinstance(plain_password, str):
        plain_bytes = plain_password.encode("utf-8")
    else:
        plain_bytes = plain_password

    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode("utf-8")

    if len(plain_bytes) > BCRYPT_MAX_LENGTH:
        plain_bytes = plain_bytes[:BCRYPT_MAX_LENGTH]

    return bcrypt.checkpw(plain_bytes, hashed_password)


def hash_refresh_token(token: str) -> str:
    """Gera um hash SHA-256 para nao persistir o refresh token em texto puro."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_token(token: str) -> dict:
    """Decodifica um JWT usando a chave secreta configurada."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


def create_access_token(data: dict):
    """Cria um access token curto com `exp`, `iat` e `jti`."""
    to_encode = data.copy()

    issued_at = utc_now()
    expire = issued_at + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "iat": issued_at, "jti": uuid4().hex})

    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict):
    """Cria um refresh token com expiracao mais longa para renovacao de sessao."""
    to_encode = data.copy()

    issued_at = utc_now()
    expire = issued_at + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "iat": issued_at, "jti": uuid4().hex})

    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
