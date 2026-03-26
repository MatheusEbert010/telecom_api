"""Rotas HTTP relacionadas a login, refresh e logout."""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jwt import InvalidTokenError
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from .. import schemas
from ..config import settings
from ..crud import user_repository
from ..security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    decode_token_by_type,
    verify_password,
)
from ..telecom_db import get_db
from ..time_utils import ensure_utc, utc_now, utc_now_naive

router = APIRouter(prefix="/auth", tags=["Autenticacao"])
logger = logging.getLogger(__name__)

# Limita tentativas de login por IP para reduzir abuso de credenciais.
limiter = Limiter(key_func=get_remote_address)


def _mask_email(email: str) -> str:
    """Oculta parte do email antes de enviar a informacao para logs."""
    local, _, domain = email.partition("@")
    if not domain:
        return "***"
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = f"{local[0]}***{local[-1]}"
    return f"{masked_local}@{domain}"


@router.post("/login", response_model=schemas.TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, data: schemas.UserLogin, db: Session = Depends(get_db)):
    """Autentica o usuario e emite access token e refresh token."""
    user = user_repository.get_user_by_email(db, data.email)

    # Mantem tempo de processamento parecido mesmo quando o email nao existe.
    stored_password = user.password if user and user.password else DUMMY_PASSWORD_HASH
    is_valid = verify_password(data.password, stored_password)

    if not user or not is_valid:
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(
            "Tentativa de login falhada para %s do IP %s",
            _mask_email(data.email),
            client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
        )

    client_ip = request.client.host if request.client else "unknown"
    logger.info("Login bem-sucedido para %s do IP %s", _mask_email(user.email), client_ip)

    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    expires_at = utc_now_naive() + timedelta(days=settings.refresh_token_expire_days)
    user_repository.create_refresh_token(
        db,
        {"token": refresh_token, "user_id": user.id, "expires_at": expires_at},
    )

    return schemas.TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh_token(data: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):
    """Valida e rotaciona o refresh token antes de emitir novos tokens."""
    try:
        payload = decode_token_by_type(data.refresh_token, expected_token_type="refresh")
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh invalido ou expirado",
        ) from exc

    db_token = user_repository.get_refresh_token(db, data.refresh_token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh invalido ou expirado",
        )

    current_time = utc_now()
    if ensure_utc(db_token.expires_at) < current_time:
        user_repository.delete_refresh_token(db, data.refresh_token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh invalido ou expirado",
        )

    token_subject = payload.get("sub")
    if token_subject is None or token_subject != db_token.user.email:
        user_repository.delete_refresh_token(db, data.refresh_token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh invalido ou expirado",
        )

    user_email = db_token.user.email
    user_id = db_token.user_id
    user_repository.delete_refresh_token(db, data.refresh_token)

    access_token = create_access_token({"sub": user_email})
    new_refresh_token = create_refresh_token({"sub": user_email})

    expires_at = utc_now_naive() + timedelta(days=settings.refresh_token_expire_days)
    user_repository.create_refresh_token(
        db,
        {"token": new_refresh_token, "user_id": user_id, "expires_at": expires_at},
    )

    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.post("/logout", response_model=schemas.MessageResponse)
def logout(data: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):
    """Invalida o refresh token informado sem revelar se ele existia ou nao."""
    user_repository.delete_refresh_token(db, data.refresh_token)
    return {"message": "Logout realizado com sucesso"}
