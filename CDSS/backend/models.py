from sqlalchemy import Column, Integer, String, DateTime, Boolean
import datetime
from database import Base

class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, index=True, nullable=True)   # owner — links record to a user
    name = Column(String, index=True)
    age = Column(String)
    sex = Column(String)
    condition = Column(String)
    status = Column(String)
    time = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
