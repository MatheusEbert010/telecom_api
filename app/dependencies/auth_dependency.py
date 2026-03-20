"""Dependencias compartilhadas para autenticacao e autorizacao."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from ..crud import user_repository
from ..telecom_db import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Resolve o usuario autenticado a partir do JWT enviado na requisicao."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError as exc:
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
