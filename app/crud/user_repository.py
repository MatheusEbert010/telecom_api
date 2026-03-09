from .. import models, schemas, user_repository, plan_repository
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

###ACESSO AO BANCO DE DADOS PARA USUÁRIOS, INCLUINDO INSCRIÇÃO EM PLANOS
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

###ATUALIZA O PLANO DO USUÁRIO
def update_user_plan(db: Session, user: models.User, plan_id: int):
    user.plan_id = plan_id
    db.commit()
    db.refresh(user)
    return user