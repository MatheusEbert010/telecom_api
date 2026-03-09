from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

###URL DE CONEXÃO COM O BANCO DE DADOS, CONFIGURAÇÃO DO MOTOR, SESSÃO E BASE PARA MODELOS ORM
DATABASE_URL = "mysql+pymysql://root:7090T&tew@localhost/telecom_api"

###CONFIGURAÇÃO DO BANCO DE DADOS COM SQLALCHEMY, INCLUINDO SESSÃO E BASE PARA MODELOS ORM
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

###BASE PARA MODELOS ORM
Base = declarative_base()