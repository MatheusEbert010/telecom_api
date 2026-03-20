from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime, timedelta
import logging
from .. import schemas
from ..telecom_db import get_db
from ..crud import user_repository
from ..security import verify_password, create_access_token, create_refresh_token
from ..config import settings

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Configurar logger
logger = logging.getLogger(__name__)

# Limite de taxa de login (5 requisições por minuto por IP)
limiter = Limiter(key_func=get_remote_address)

###ROTA PARA LOGIN DE USUÁRIO, GERANDO TOKEN DE ACESSO SE AS CREDENCIAIS FOREM VÁLIDAS
@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, data: schemas.UserLogin, db: Session = Depends(get_db)):

    user = user_repository.get_user_by_email(db, data.email)

    # Proteção contra timing attacks: sempre executar verify mesmo se user for None
    is_valid = user and verify_password(data.password, user.password or "")

    if not is_valid:
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(f"Tentativa de login falhada para email: {data.email} do IP: {client_ip}")
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas"
        )

    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Login bem-sucedido para usuário: {user.email} do IP: {client_ip}")  # type: ignore
    
    # Criar tokens
    access_token = create_access_token({"sub": user.email})  # type: ignore
    refresh_token = create_refresh_token({"sub": user.email})  # type: ignore

    # Salvar refresh token no banco
    expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    user_repository.create_refresh_token(db, {
        "token": refresh_token,
        "user_id": user.id,  # type: ignore
        "expires_at": expires_at
    })

    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

###ROTA PARA REFRESH DE TOKEN
@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh_token(data: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):

    # Verificar se o refresh token existe e não expirou
    db_token = user_repository.get_refresh_token(db, data.refresh_token)

    if not db_token:
        raise HTTPException(
            status_code=401,
            detail="Token de refresh inválido ou expirado"
        )
    
    current_time = datetime.utcnow()
    if db_token.expires_at < current_time:  # type: ignore
        raise HTTPException(
            status_code=401,
            detail="Token de refresh inválido ou expirado"
        )

    # Criar novo access token
    access_token = create_access_token({"sub": db_token.user.email})

    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=data.refresh_token  # Retornar o mesmo refresh token
    )

###ROTA PARA LOGOUT (INVALIDAR REFRESH TOKEN)
@router.post("/logout")
def logout(data: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):

    # Deletar o refresh token
    deleted_token = user_repository.delete_refresh_token(db, data.refresh_token)

    if not deleted_token:
        raise HTTPException(
            status_code=400,
            detail="Token de refresh inválido"
        )

    return {"message": "Logout realizado com sucesso"}
