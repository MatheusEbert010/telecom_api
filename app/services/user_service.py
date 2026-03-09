from ..crud import user_repository, plan_repository
from fastapi import HTTPException

###REGRA AS FUNÇÕES DE NEGÓCIO RELACIONADAS AOS USUÁRIOS, COMO INSCRIÇÃO EM PLANOS
def subscribe_plan(db, user_id, plan_id):

    user = user_repository.get_user(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    plan = plan_repository.get_plan(db, plan_id)

    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    return user_repository.update_user_plan(db, user, plan_id)