from ..crud import user_repository, plan_repository
from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..security import hash_password


### CRIAÇÃO DE USUÁRIO COM HASH DE SENHA
def create_user(db: Session, user):

    # limita tamanho da senha para evitar erro do bcrypt
    password = user.password[:72]

    # verifica se email já existe
    existing_user = user_repository.get_user_by_email(db, user.email)

    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    user_data = {
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "password": hash_password(password)
    }

    return user_repository.create_user(db, user_data)


### REGRA DE ASSINATURA DE PLANO
def subscribe_plan(db: Session, user_id: int, plan_id: int):

    # verifica se usuário existe
    user = user_repository.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # verifica se plano existe
    plan = plan_repository.get_plan_by_id(db, plan_id)

    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    # atualiza plano do usuário usando repository
    return user_repository.update_user_plan(db, user, plan_id)


### LISTAGEM PAGINADA DE USUÁRIOS
def list_users_paginated(db: Session, page: int = 1, limit: int = 10, email: str = None):

    if page < 1:
        page = 1

    if limit > 100:
        limit = 100

    users, total = user_repository.get_users_paginated(db, page, limit, email)

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "data": users
    }