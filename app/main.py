from fastapi import FastAPI
from .routers import users
from .telecom_db import engine
from . import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Nossa API de Telecom está funcionando!"}

app.include_router(users.router)