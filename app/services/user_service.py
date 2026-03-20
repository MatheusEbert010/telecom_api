from ..crud import user_repository, plan_repository
from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..security import hash_password
from ..cache import cache
import json


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
        "password": hash_password(password),
        "role": user.role
    }

    created_user = user_repository.create_user(db, user_data)

    # Invalidar cache de usuários
    cache.clear_pattern("users:list:*")

    return created_user


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


### LISTAGEM AVANÇADA DE USUÁRIOS COM FILTROS E BUSCA
def list_users_advanced(
    db: Session,
    page: int = 1,
    limit: int = 10,
    search: str = None,
    role: str = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    # Criar chave de cache baseada nos parâmetros
    cache_key = f"users:list:{page}:{limit}:{search}:{role}:{sort_by}:{sort_order}"

    # Tentar obter do cache
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    from sqlalchemy import or_, and_, desc, asc

    # Validações
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 10

    # Campos válidos para ordenação
    valid_sort_fields = ["name", "email", "created_at", "role"]
    if sort_by not in valid_sort_fields:
        sort_by = "created_at"

    if sort_order not in ["asc", "desc"]:
        sort_order = "desc"

    # Construir query base
    query = db.query(user_repository.models.User)

    # Aplicar filtros
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                user_repository.models.User.name.ilike(search_term),
                user_repository.models.User.email.ilike(search_term)
            )
        )

    if role:
        query = query.filter(user_repository.models.User.role == role)

    # Aplicar ordenação
    if sort_order == "desc":
        query = query.order_by(desc(getattr(user_repository.models.User, sort_by)))
    else:
        query = query.order_by(asc(getattr(user_repository.models.User, sort_by)))

    # Paginação
    offset = (page - 1) * limit
    total = query.count()
    users = query.offset(offset).limit(limit).all()

    result = {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": (total + limit - 1) // limit,  # Ceiling division
        "data": users,
        "filters": {
            "search": search,
            "role": role,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
    }

    # Cache por 5 minutos
    cache.set(cache_key, result, expire=300)

    return result