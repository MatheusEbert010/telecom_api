from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .telecom_db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    
    plan_id = Column(Integer, ForeignKey("plans.id"))
    
    plan = relationship("Plan", back_populates="users")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    price = Column(Float)
    speed = Column(Integer)

    users = relationship("User", back_populates="plan")