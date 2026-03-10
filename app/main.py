from fastapi import FastAPI
from .routers import users
from .telecom_db import engine
from .routers import plans
from . import models
from .routers import auth

####CRIAÇÃO DAS TABELAS NO BANCO DE DADOS
models.Base.metadata.create_all(bind=engine)

####CRIAÇÃO DA INSTÂNCIA DO FASTAPI E INCLUSÃO DAS ROTAS DOS USUÁRIOS E PLANOS
app = FastAPI()

####ROTA PARA GERENCIAR USUÁRIOS, INCLUINDO INSCRIÇÃO EM PLANOS
app.include_router(users.router)
app.include_router(plans.router)
app.include_router(auth.router)