from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..crud import crud_completo
from ..schemas import UserCreate
from ..services import user_service
from .. import schemas
from ..dependencies.auth_dependency import get_current_user, get_current_admin
from .. import models
from ..telecom_db import get_db

###ROTA PARA GERENCIAR USUÁRIOS, INCLUINDO INSCRIÇÃO EM PLANOS
router = APIRouter(prefix="/users", tags=["Usuários"])

###ROTAS PARA GERENCIAR USUÁRIOS
@router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, user)

###LISTAR USUÁRIOS COM FILTROS AVANÇADOS E BUSCA
@router.get("/")
def get_users(
    page: int = 1,
    limit: int = 10,
    search: str | None = None,  # Busca por nome ou email
    role: str | None = None,     # Filtro por role (admin/user)
    sort_by: str = "created_at", # Ordenação: name, email, created_at
    sort_order: str = "desc",    # asc ou desc
    current_user: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return user_service.list_users_advanced(
        db=db,
        page=page,
        limit=limit,
        search=search,
        role=role,
        sort_by=sort_by,
        sort_order=sort_order
    )

###ROTAS PARA GERENCIAR USUÁRIOS POR ID
@router.get("/{user_id}")
def get_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Usuário pode ver seus próprios dados ou admin pode ver qualquer um
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")

    user = crud_completo.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return user

####ROTAS PARA DELETAR E ATUALIZAR USUÁRIOS
@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: models.User = Depends(get_current_admin),  # Apenas admin pode deletar
    db: Session = Depends(get_db)
):
    user = crud_completo.delete_user(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {"message": "Usuário deletado com sucesso"}

####ROTA PARA ATUALIZAR USUÁRIO
@router.put("/{user_id}")
def update_user(
    user_id: int,
    user: schemas.UserCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Usuário pode atualizar seus próprios dados ou admin pode atualizar qualquer um
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")

    updated_user = crud_completo.update_user(db, user_id, user)

    if not updated_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return updated_user

###ROTA PARA INSCRIÇÃO DE USUÁRIO EM UM PLANO
@router.post("/{user_id}/subscribe")
def subscribe_plan(
    user_id: int,
    data: schemas.SubscribePlan,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Usuário pode se inscrever ou admin pode inscrever qualquer um
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")

    result = crud_completo.subscribe_user_to_plan(db, user_id, data.plan_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if result == "Plano não encontrado":
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    return {
        "message": "Plano assinado com sucesso",
        "user": result
    }

###ROTA PARA OBTER INFORMAÇÕES DO USUÁRIO AUTENTICADO
@router.get("/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user