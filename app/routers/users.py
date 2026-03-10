from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..crud import crud_completo
from ..services import user_service
from .. import schemas
from ..telecom_db import SessionLocal

###ROTA PARA GERENCIAR USUÁRIOS, INCLUINDO INSCRIÇÃO EM PLANOS
router = APIRouter(prefix="/users", tags=["Users"])

###DEPENDÊNCIA PARA OBTER A SESSÃO DO BANCO DE DADOS
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

###ROTAS PARA GERENCIAR USUÁRIOS
@router.post("/")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud_completo.create_user(db, user)

###LISTAR USUÁRIOS DE FORMA PAGINADA, COM VALIDAÇÃO DE PARÂMETROS DE PAGINAÇÃO
@router.get("/")
def get_users(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    return user_service.list_users_paginated(db, page, limit)

###ROTAS PARA GERENCIAR USUÁRIOS POR ID
@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud_completo.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return user

####ROTAS PARA DELETAR E ATUALIZAR USUÁRIOS
@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = crud_completo.delete_user(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {"message": "Usuário deletado com sucesso"}


####ROTA PARA ATUALIZAR USUÁRIO
@router.put("/{user_id}")
def update_user(user_id: int, user: schemas.UserCreate, db: Session = Depends(get_db)):
    updated_user = crud_completo.update_user(db, user_id, user)

    if not updated_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return updated_user

###ROTA PARA INSCRIÇÃO DE USUÁRIO EM UM PLANO
@router.post("/{user_id}/subscribe")
def subscribe_plan(user_id: int, data: schemas.SubscribePlan, db: Session = Depends(get_db)):

    result = crud_completo.subscribe_user_to_plan(db, user_id, data.plan_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if result == "Plano não encontrado":
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    return {
        "message": "Plano assinado com sucesso",
        "user": result
    }