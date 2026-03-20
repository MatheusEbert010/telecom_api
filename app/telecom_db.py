from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

###URL DE CONEXÃO COM O BANCO DE DADOS, CONFIGURAÇÃO DO MOTOR, SESSÃO E BASE PARA MODELOS ORM
DATABASE_URL = settings.database_url

###CONFIGURAÇÃO DO BANCO DE DADOS COM SQLALCHEMY, INCLUINDO SESSÃO E BASE PARA MODELOS ORM
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

###BASE PARA MODELOS ORM
Base = declarative_base()

###DEPENDÊNCIA PARA OBTER A SESSÃO DO BANCO DE DADOS, GARANTINDO QUE A SESSÃO SEJA FECHADA APÓS O USO
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()