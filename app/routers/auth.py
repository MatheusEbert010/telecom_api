from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..telecom_db import get_db
from ..crud import user_repository
from ..security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

###ROTA PARA LOGIN DE USUÁRIO, GERANDO TOKEN DE ACESSO SE AS CREDENCIAIS FOREM VÁLIDAS
@router.post("/login")
def login(data: schemas.UserLogin, db: Session = Depends(get_db)):

    user = user_repository.get_user_by_email(db, data.email)

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token({"sub": user.email})

    return {
        "access_token": token,
        "token_type": "bearer"
    }
