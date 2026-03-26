"""Regras de negocio relacionadas ao ciclo de vida dos usuarios."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..cache import cache
from ..crud import plan_repository, user_repository
from ..security import hash_password


def _hash_password(password: str) -> str:
    """Converte o hash de senha para string antes de persistir no banco."""
    hashed_password = hash_password(password)
    return hashed_password.decode("utf-8") if isinstance(hashed_password, bytes) else hashed_password


def create_user(db: Session, user: schemas.UserCreate):
    """Cria um usuario comum com email unico e senha protegida por hash."""
    existing_user = user_repository.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email ja cadastrado")

    user_data = {
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "password": _hash_password(user.password),
        "role": schemas.UserRole.USER.value,
    }

    created_user = user_repository.create_user(db, user_data)
    cache.clear_pattern("users:list:*")
    return created_user


def ensure_admin_user(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    phone: str | None = None,
):
    """Cria ou promove um usuario para administrador de forma idempotente."""
    validated_user = schemas.UserCreate(
        name=name,
        email=email,
        phone=phone,
        password=password,
    )

    existing_user = user_repository.get_user_by_email(db, validated_user.email)
    if existing_user:
        existing_user.name = validated_user.name
        existing_user.phone = validated_user.phone
        existing_user.password = _hash_password(validated_user.password)
        existing_user.role = schemas.UserRole.ADMIN.value
        db.commit()
        db.refresh(existing_user)
        cache.clear_pattern("users:list:*")
        return existing_user, False

    user_data = {
        "name": validated_user.name,
        "email": validated_user.email,
        "phone": validated_user.phone,
        "password": _hash_password(validated_user.password),
        "role": schemas.UserRole.ADMIN.value,
    }
    created_user = user_repository.create_user(db, user_data)
    cache.clear_pattern("users:list:*")
    return created_user, True


def update_user(db: Session, user_id: int, user_data: schemas.UserUpdate):
    """Atualiza dados do usuario sem permitir elevacao implicita de privilegio."""
    user = user_repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    existing_user = user_repository.get_user_by_email(db, user_data.email)
    if existing_user and existing_user.id != user_id:
        raise HTTPException(status_code=400, detail="Email ja cadastrado")

    user.name = user_data.name
    user.email = user_data.email
    user.phone = user_data.phone

    if user_data.password:
        user.password = _hash_password(user_data.password)

    db.commit()
    db.refresh(user)
    cache.clear_pattern("users:list:*")
    return user


def change_user_role(db: Session, user_id: int, role: schemas.UserRole):
    """Troca explicitamente o papel de um usuario existente."""
    user = user_repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    user.role = role.value
    db.commit()
    db.refresh(user)
    cache.clear_pattern("users:list:*")
    return user


def get_user_by_id(db: Session, user_id: int):
    """Encapsula a leitura de um usuario por id."""
    return user_repository.get_user_by_id(db, user_id)


def delete_user(db: Session, user_id: int):
    """Remove um usuario e invalida caches dependentes."""
    user = user_repository.get_user_by_id(db, user_id)
    if not user:
        return None

    deleted_user = user_repository.delete_user(db, user)
    cache.clear_pattern("users:list:*")
    return deleted_user


def subscribe_plan(db: Session, user_id: int, plan_id: int):
    """Vincula um usuario a um plano existente."""
    user = user_repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    plan = plan_repository.get_plan_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano nao encontrado")

    updated_user = user_repository.update_user_plan(db, user, plan_id)
    cache.clear_pattern("users:list:*")
    return updated_user


def cancel_plan_subscription(db: Session, user_id: int):
    """Remove o plano atualmente associado ao usuario."""
    user = user_repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    if user.plan_id is None:
        raise HTTPException(status_code=400, detail="Usuario nao possui plano assinado")

    updated_user = user_repository.update_user_plan(db, user, None)
    cache.clear_pattern("users:list:*")
    return updated_user


def get_user_plan(db: Session, user_id: int):
    """Retorna o plano ativo do usuario quando existir."""
    user = user_repository.get_user_by_id_with_plan(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    if user.plan is None:
        raise HTTPException(status_code=404, detail="Usuario nao possui plano assinado")

    return {"user_id": user.id, "plan": user.plan}


def list_users_paginated(
    db: Session,
    page: int = 1,
    limit: int = 10,
    email: str | None = None,
):
    """Mantem uma listagem simples de usuarios para compatibilidade."""
    if page < 1:
        page = 1

    if limit > 100:
        limit = 100

    users, total = user_repository.get_users_paginated(db, page, limit, email)
    return {"page": page, "limit": limit, "total": total, "data": users}


def list_users_advanced(
    db: Session,
    page: int = 1,
    limit: int = 10,
    search: str | None = None,
    role: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    """Lista usuarios com busca, filtros, ordenacao e cache de leitura."""
    cache_key = f"users:list:{page}:{limit}:{search}:{role}:{sort_by}:{sort_order}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 10

    valid_sort_fields = ["name", "email", "created_at", "role"]
    if sort_by not in valid_sort_fields:
        sort_by = "created_at"
    if sort_order not in ["asc", "desc"]:
        sort_order = "desc"

    users, total = user_repository.get_users_advanced(
        db=db,
        page=page,
        limit=limit,
        search=search,
        role=role,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    result = {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": (total + limit - 1) // limit,
        "data": users,
        "filters": {
            "search": search,
            "role": role,
            "sort_by": sort_by,
            "sort_order": sort_order,
        },
    }

    cache.set(cache_key, result, expire=300)
    return result
