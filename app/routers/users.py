"""Rotas HTTP relacionadas ao gerenciamento de usuarios."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..dependencies.auth_dependency import get_current_admin, get_current_user
from ..services import user_service
from ..telecom_db import get_db

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.post("/", response_model=schemas.UserResponse, status_code=201)
def create_user(
    user: schemas.AdminUserCreate,
    current_user: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Cadastra uma nova conta sob responsabilidade de um administrador."""
    return user_service.create_user(db, user)


@router.get("/", response_model=schemas.UserListResponse)
def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, min_length=2, max_length=100),
    role: schemas.UserRole | None = None,
    sort_by: Literal["name", "email", "created_at", "role"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    current_user: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Lista usuarios para administradores com filtros e ordenacao."""
    return user_service.list_users_advanced(
        db=db,
        page=page,
        limit=limit,
        search=search,
        role=role.value if role else None,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Retorna os dados do usuario autenticado."""
    return current_user


@router.get("/me/plan", response_model=schemas.UserPlanResponse)
def get_my_plan(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna o plano atualmente associado ao usuario autenticado."""
    return user_service.get_user_plan(db, current_user.id)


@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: int = Path(..., gt=0),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna um usuario especifico respeitando regra de acesso por dono ou admin."""
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")

    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    return user


@router.patch("/{user_id}/role", response_model=schemas.UserResponse)
def change_user_role(
    data: schemas.UserRoleUpdate,
    user_id: int = Path(..., gt=0),
    current_user: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Permite ao administrador alterar explicitamente o papel de um usuario."""
    return user_service.change_user_role(db, user_id, data.role)


@router.patch("/{user_id}/address", response_model=schemas.UserResponse)
def update_user_address(
    data: schemas.UserAddressUpdate,
    user_id: int = Path(..., gt=0),
    current_user: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Permite ao administrador atualizar o endereco de qualquer conta."""
    return user_service.update_user_address(db, user_id, data)


@router.delete("/{user_id}", response_model=schemas.MessageResponse)
def delete_user(
    user_id: int = Path(..., gt=0),
    current_user: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Remove um usuario, exceto quando o admin tenta excluir a propria conta."""
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Um administrador nao pode deletar a propria conta",
        )

    user = user_service.delete_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    return {"message": "Usuario deletado com sucesso"}


@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user: schemas.UserUpdate,
    user_id: int = Path(..., gt=0),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Atualiza um usuario respeitando a regra de dono ou administrador."""
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")

    return user_service.update_user(db, user_id, user)


@router.post("/{user_id}/subscribe", response_model=schemas.UserSubscriptionResponse)
def subscribe_plan(
    data: schemas.SubscribePlan,
    user_id: int = Path(..., gt=0),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Assina um plano para o proprio usuario ou para outro usuario via admin."""
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")

    result = user_service.subscribe_plan(db, user_id, data.plan_id)
    return {"message": "Plano assinado com sucesso", "user": result}


@router.delete("/{user_id}/subscribe", response_model=schemas.UserSubscriptionResponse)
def cancel_subscription(
    user_id: int = Path(..., gt=0),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancela o plano do proprio usuario ou de outro usuario via admin."""
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")

    result = user_service.cancel_plan_subscription(db, user_id)
    return {"message": "Plano cancelado com sucesso", "user": result}
