from ..crud import user_repository, plan_repository
from fastapi import HTTPException
from sqlalchemy.orm import Session

###REGRA AS FUNÇÕES DE NEGÓCIO RELACIONADAS AOS USUÁRIOS, COMO INSCRIÇÃO EM PLANOS
def subscribe_plan(db: Session, user_id: int, plan_id: int):

    # Verifica se usuário existe
    user = user_repository.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Verifica se plano existe
    plan = plan_repository.get_plan_by_id(db, plan_id)

    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    # Associa plano ao usuário
    user.plan_id = plan_id

    db.commit()
    db.refresh(user)

    return {
        "message": "Plano associado ao usuário com sucesso",
        "user": user
    }

###FUNÇÃO PARA LISTAR USUÁRIOS DE FORMA PAGINADA, COM VALIDAÇÃO DE PARÂMETROS DE PAGINAÇÃO
def list_users_paginated(db, page: int = 1, limit: int = 10):

    if page < 1:
        page = 1

    if limit > 100:
        limit = 100

    return user_repository.get_users_paginated(db, page, limit)