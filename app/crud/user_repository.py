"""Operacoes de persistencia relacionadas a usuarios e refresh tokens."""

from sqlalchemy.orm import Session

from .. import models
from ..security import hash_refresh_token


def get_user_by_id(db: Session, user_id: int):
    """Busca um usuario pela chave primaria."""
    return db.query(models.User).filter(models.User.id == user_id).first()


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
    db.delete(user)
    db.commit()
    return user


def update_user_plan(db: Session, user: models.User, plan_id: int):
    """Vincula um plano ao usuario informado."""
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
