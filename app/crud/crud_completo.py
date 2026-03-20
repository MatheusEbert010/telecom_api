from sqlalchemy.orm import Session
from .. import models, schemas
from ..cache import cache
from ..security import hash_password
import json
from typing import Optional

###CRIAÇÃO DE USUÁRIOS E PLANOS, INCLUINDO INSCRIÇÃO DE USUÁRIOS EM PLANOS, COM ACESSO AO BANCO DE DADOS
def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        name=user.name,
        email=user.email,
        phone=user.phone,
        password=hash_password(user.password),
        role=user.role
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Invalidar cache de usuários
    cache.clear_pattern("users:list:*")

    return db_user

###ACESSO AO BANCO DE DADOS PARA USUÁRIOS, INCLUINDO INSCRIÇÃO EM PLANOS
def get_users(db: Session):
    return db.query(models.User).all()

###ACESSO AO BANCO DE DADOS PARA USUÁRIOS POR ID
def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

###DELETA USUÁRIO DO BANCO DE DADOS
def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user:
        db.delete(user)
        db.commit()
        # Invalidar cache de usuários
        cache.clear_pattern("users:list:*")

    return user

###ATUALIZA USUÁRIO NO BANCO DE DADOS
def update_user(db: Session, user_id: int, user_data: schemas.UserCreate):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        return None

    user.name = user_data.name  # type: ignore
    user.email = user_data.email  # type: ignore
    user.phone = user_data.phone if user_data.phone else None  # type: ignore
    password_hash = hash_password(user_data.password)
    user.password = password_hash.decode('utf-8') if isinstance(password_hash, bytes) else password_hash  # type: ignore
    user.role = user_data.role  # type: ignore

    db.commit()
    db.refresh(user)

    # Invalidar cache de usuários
    cache.clear_pattern("users:list:*")

    return user

###CRIAÇÃO DE PLANOS, INCLUINDO INSCRIÇÃO DE USUÁRIOS EM PLANOS, COM ACESSO AO BANCO DE DADOS
def create_plan(db: Session, plan: schemas.PlanCreate):
    db_plan = models.Plan(
        name=plan.name,
        price=plan.price,
        speed=plan.speed
    )

    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)

    # Invalidar cache de planos
    cache.clear_pattern("plans:list:*")

    return db_plan

###ACESSO AO BANCO DE DADOS PARA PLANOS
def get_plans(db: Session):
    return db.query(models.Plan).all()


### LISTAGEM AVANÇADA DE PLANOS COM FILTROS
def get_plans_advanced(
    db: Session,
    search: Optional[str] = None,
    min_speed: Optional[int] = None,
    max_speed: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: str = "price",
    sort_order: str = "asc"
):
    # Criar chave de cache baseada nos parâmetros
    cache_key = f"plans:list:{search}:{min_speed}:{max_speed}:{min_price}:{max_price}:{sort_by}:{sort_order}"

    # Tentar obter do cache
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    from sqlalchemy import or_, and_, desc, asc

    # Campos válidos para ordenação
    valid_sort_fields = ["name", "price", "speed"]
    if sort_by not in valid_sort_fields:
        sort_by = "price"

    if sort_order not in ["asc", "desc"]:
        sort_order = "asc"

    # Construir query base
    query = db.query(models.Plan)

    # Aplicar filtros
    if search:
        search_term = f"%{search}%"
        query = query.filter(models.Plan.name.ilike(search_term))

    if min_speed is not None:
        query = query.filter(models.Plan.speed >= min_speed)

    if max_speed is not None:
        query = query.filter(models.Plan.speed <= max_speed)

    if min_price is not None:
        query = query.filter(models.Plan.price >= min_price)

    if max_price is not None:
        query = query.filter(models.Plan.price <= max_price)

    # Aplicar ordenação
    if sort_order == "desc":
        query = query.order_by(desc(getattr(models.Plan, sort_by)))
    else:
        query = query.order_by(asc(getattr(models.Plan, sort_by)))

    plans = query.all()

    result = {
        "total": len(plans),
        "data": plans,
        "filters": {
            "search": search,
            "min_speed": min_speed,
            "max_speed": max_speed,
            "min_price": min_price,
            "max_price": max_price,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
    }

    # Cache por 10 minutos (planos mudam menos frequentemente)
    cache.set(cache_key, result, expire=600)

    return result


###ACESSO AO BANCO DE DADOS PARA INSCRIÇÃO DE USUÁRIO EM UM PLANO
def subscribe_user_to_plan(db: Session, user_id: int, plan_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        return None

    plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()

    if not plan:
        return None

    user.plan_id = plan_id  # type: ignore

    db.commit()
    db.refresh(user)

    # Invalidar cache de usuários
    cache.clear_pattern("users:list:*")

    return user