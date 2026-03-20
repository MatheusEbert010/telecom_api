from datetime import datetime, timedelta
import bcrypt
from jose import jwt
from .config import settings

# Limite do bcrypt: 72 bytes
BCRYPT_MAX_LENGTH = 72

###CRIA HASH DA SENHA
def hash_password(password: str) -> bytes:
    if isinstance(password, str):
        password_bytes = password.encode('utf-8')
    else:
        password_bytes = password

    if len(password_bytes) > BCRYPT_MAX_LENGTH:
        password_bytes = password_bytes[:BCRYPT_MAX_LENGTH]

    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed

###VERIFICA SENHA PLANA COM HASH
def verify_password(plain_password, hashed_password) -> bool:
    if isinstance(plain_password, str):
        plain_bytes = plain_password.encode('utf-8')
    else:
        plain_bytes = plain_password

    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')

    if len(plain_bytes) > BCRYPT_MAX_LENGTH:
        plain_bytes = plain_bytes[:BCRYPT_MAX_LENGTH]

    return bcrypt.checkpw(plain_bytes, hashed_password)

###CRIA TOKEN DE ACESSO COM EXPIRAÇÃO
def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return encoded_jwt

###CRIA TOKEN DE REFRESH COM EXPIRAÇÃO MAIS LONGA
def create_refresh_token(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return encoded_jwt