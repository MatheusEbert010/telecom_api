"""Operacoes de persistencia relacionadas a usuarios e refresh tokens."""

from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from .. import models
from ..security import hash_refresh_token


def get_user_by_id(db: Session, user_id: int):
    """Busca um usuario pela chave primaria."""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_id_with_plan(db: Session, user_id: int):
    """Busca um usuario com o relacionamento de plano carregado."""
    return (
        db.query(models.User)
        .options(joinedload(models.User.plan))
        .filter(models.User.id == user_id)
        .first()
    )


def get_user_by_email(db: Session, email: str):
    """Busca um usuario pelo email unico."""
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user_data: dict):
    """Persiste um novo usuario ja validado pela camada de servico."""
    db_user = models.User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user: models.User):
    """Remove um usuario existente do banco."""
    delete_refresh_tokens_by_user_id(db, user.id)
    db.delete(user)
    db.commit()
    return user


def update_user_plan(db: Session, user: models.User, plan_id: int | None):
    """Atualiza o plano vinculado ao usuario, inclusive para cancelamento."""
    user.plan_id = plan_id
    db.commit()
    db.refresh(user)
    return user


def get_users_paginated(
    db: Session,
    page: int = 1,
    limit: int = 10,
    email: str | None = None,
):
    """Lista usuarios com filtro opcional por email e metrica de total."""
    offset = (page - 1) * limit
    query = db.query(models.User)

    if email:
        query = query.filter(models.User.email == email)

    total = query.count()
    users = query.offset(offset).limit(limit).all()
    return users, total


def get_users_advanced(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    role: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    """Lista usuarios com filtros e ordenacao encapsulados no repository."""
    query = db.query(models.User)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.User.name.ilike(search_term),
                models.User.email.ilike(search_term),
            )
        )

    if role:
        query = query.filter(models.User.role == role)

    sort_column = getattr(models.User, sort_by)
    sort_function = desc if sort_order == "desc" else asc
    query = query.order_by(sort_function(sort_column))

    offset = (page - 1) * limit
    total = query.count()
    users = query.offset(offset).limit(limit).all()
    return users, total


def get_admin_stats(db: Session) -> dict[str, int]:
    """Calcula metricas agregadas para o painel administrativo."""
    total_users = db.query(func.count(models.User.id)).scalar() or 0
    total_admins = (
        db.query(func.count(models.User.id))
        .filter(models.User.role == models.UserRole.ADMIN.value)
        .scalar()
        or 0
    )
    total_plans = db.query(func.count(models.Plan.id)).scalar() or 0
    users_with_plan = (
        db.query(func.count(models.User.id)).filter(models.User.plan_id.is_not(None)).scalar() or 0
    )

    return {
        "total_users": int(total_users),
        "total_admins": int(total_admins),
        "total_plans": int(total_plans),
        "users_with_plan": int(users_with_plan),
        "users_without_plan": int(total_users - users_with_plan),
    }


def create_refresh_token(db: Session, token_data: dict):
    """Persiste o refresh token armazenando apenas seu hash."""
    payload = token_data.copy()
    payload["token"] = hash_refresh_token(payload["token"])

    db_token = models.RefreshToken(**payload)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def get_refresh_token(db: Session, token: str):
    """Busca um refresh token por hash, com compatibilidade para dados legados."""
    hashed_token = hash_refresh_token(token)
    db_token = db.query(models.RefreshToken).filter(models.RefreshToken.token == hashed_token).first()

    if db_token:
        return db_token

    return db.query(models.RefreshToken).filter(models.RefreshToken.token == token).first()


def delete_refresh_token(db: Session, token: str):
    """Remove um refresh token por hash ou por valor legado em texto puro."""
    hashed_token = hash_refresh_token(token)
    db_token = db.query(models.RefreshToken).filter(models.RefreshToken.token == hashed_token).first()

    if not db_token:
        db_token = db.query(models.RefreshToken).filter(models.RefreshToken.token == token).first()

    if db_token:
        db.delete(db_token)
        db.commit()

    return db_token


def delete_refresh_tokens_by_user_id(db: Session, user_id: int) -> int:
    """Remove todos os refresh tokens associados a um usuario."""
    deleted_rows = (
        db.query(models.RefreshToken).filter(models.RefreshToken.user_id == user_id).delete()
    )
    db.commit()
    return int(deleted_rows)
