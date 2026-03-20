"""Configuracao da conexao SQLAlchemy e da sessao do banco."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

DATABASE_URL = settings.database_url

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Fornece uma sessao por requisicao e garante o fechamento ao final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
