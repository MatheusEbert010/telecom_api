from sqlalchemy.orm import Session
from . import models, schemas


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        name=user.name,
        email=user.email,
        phone=user.phone
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def get_users(db: Session):
    return db.query(models.User).all()


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user:
        db.delete(user)
        db.commit()

    return user


def update_user(db: Session, user_id: int, user_data: schemas.UserCreate):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        return None

    user.name = user_data.name
    user.email = user_data.email
    user.phone = user_data.phone

    db.commit()
    db.refresh(user)

    return user

def create_plan(db: Session, plan: schemas.PlanCreate):
    db_plan = models.Plan(
        name=plan.name,
        price=plan.price,
        speed=plan.speed
    )

    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)

    return db_plan


def get_plans(db: Session):
    return db.query(models.Plan).all()