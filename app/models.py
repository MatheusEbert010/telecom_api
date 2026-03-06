from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .telecom_db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)