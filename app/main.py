from fastapi import FastAPI
from .routers import users
from .telecom_db import engine
from .routers import plans
from . import models


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users.router)
app.include_router(plans.router)