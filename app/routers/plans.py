from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud_completo
from ..telecom_db import SessionLocal

router = APIRouter(prefix="/plans", tags=["Plans"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def create_plan(plan: schemas.PlanCreate, db: Session = Depends(get_db)):
    return crud_completo.create_plan(db, plan)


@router.get("/")
def list_plans(db: Session = Depends(get_db)):
    return crud_completo.get_plans(db)