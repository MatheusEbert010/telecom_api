from .. import models
from sqlalchemy.orm import Session

###ACESSO AO BANCO DE DADOS PARA USUÁRIOS, INCLUINDO INSCRIÇÃO EM PLANOS
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

###ATUALIZA O PLANO DO USUÁRIO
def update_user_plan(db: Session, user: models.User, plan_id: int):
    user.plan_id = plan_id
    db.commit()
    db.refresh(user)
    return user

###USUÁRIOS PAGINADOS, COM LIMITAÇÃO DE REGISTROS POR PÁGINA E DESLOCAMENTO PARA NAVEGAÇÃO ENTRE AS PÁGINAS
def get_users_paginated(db: Session, page: int = 1, limit: int = 10, email: str = None):

    offset = (page - 1) * limit

    query = db.query(models.User)

    if email:
        query = query.filter(models.User.email == email)

    users = query.offset(offset).limit(limit).all()

    total = query.count()

    return users, total