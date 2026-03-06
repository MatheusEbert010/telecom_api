from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud_completo
from ..telecom_db import SessionLocal

router = APIRouter(prefix="/users", tags=["Users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud_completo.create_user(db, user)


@router.get("/")
def list_users(db: Session = Depends(get_db)):
    return crud_completo.get_users(db)


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud_completo.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = crud_completo.delete_user(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted"}


@router.put("/{user_id}")
def update_user(user_id: int, user: schemas.UserCreate, db: Session = Depends(get_db)):
    updated_user = crud_completo.update_user(db, user_id, user)

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return updated_user