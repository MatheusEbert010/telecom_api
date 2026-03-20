from sqlalchemy.orm import Session
from .. import models


### BUSCAR USUÁRIO POR ID
def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


### BUSCAR USUÁRIO POR EMAIL
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


### CRIAR USUÁRIO
def create_user(db: Session, user_data: dict):

    db_user = models.User(**user_data)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


### ATUALIZAR PLANO DO USUÁRIO
def update_user_plan(db: Session, user: models.User, plan_id: int):

    user.plan_id = plan_id

    db.commit()
    db.refresh(user)

    return user


### LISTAR USUÁRIOS COM PAGINAÇÃO
def get_users_paginated(db: Session, page: int = 1, limit: int = 10, email: str | None = None):

    offset = (page - 1) * limit

    query = db.query(models.User)

    if email:
        query = query.filter(models.User.email == email)

    total = query.count()

    users = query.offset(offset).limit(limit).all()

    return users, total


### CRIAR TOKEN DE REFRESH
def create_refresh_token(db: Session, token_data: dict):

    db_token = models.RefreshToken(**token_data)

    db.add(db_token)
    db.commit()
    db.refresh(db_token)

    return db_token


### BUSCAR TOKEN DE REFRESH POR TOKEN
def get_refresh_token(db: Session, token: str):
    return db.query(models.RefreshToken).filter(models.RefreshToken.token == token).first()


### DELETAR TOKEN DE REFRESH
def delete_refresh_token(db: Session, token: str):

    db_token = db.query(models.RefreshToken).filter(models.RefreshToken.token == token).first()

    if db_token:
        db.delete(db_token)
        db.commit()

    return db_token