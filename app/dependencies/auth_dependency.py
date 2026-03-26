"""Dependencias compartilhadas para autenticacao e autorizacao."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from .. import models
from ..crud import user_repository
from ..security import decode_token_by_type
from ..telecom_db import get_db

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """Resolve o usuario autenticado a partir do JWT enviado na requisicao."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de acesso invalido ou ausente",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise credentials_exception

    try:
        payload = decode_token_by_type(credentials.credentials, expected_token_type="access")
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError as exc:
        raise credentials_exception from exc

    user = user_repository.get_user_by_email(db, email)
    if user is None:
        raise credentials_exception

    return user


def get_current_admin(current_user: models.User = Depends(get_current_user)):
    """Garante que a rota seja acessada apenas por administradores."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Requer privilegios de administrador",
        )
    return current_user
