from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from ..telecom_db import get_db
from ..crud import user_repository
from .. import models
from ..config import settings

###DEPENDÊNCIA PARA AUTENTICAÇÃO DE USUÁRIOS COM JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

###FUNÇÃO PARA OBTER O USUÁRIO ATUAL A PARTIR DO TOKEN JWT
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

        email: str = payload.get("sub")

        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = user_repository.get_user_by_email(db, email)

    if user is None:
        raise credentials_exception

    return user

###FUNÇÃO PARA VERIFICAR SE O USUÁRIO É ADMIN
def get_current_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Requer privilégios de administrador"
        )
    return current_user