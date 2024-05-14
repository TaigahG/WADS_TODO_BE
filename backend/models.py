from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    firebase_uid = Column(String(255), index=True, nullable=False)
    email = Column(String(255), index=True, nullable=False)
    username = Column(String(255), index=True, nullable=False)

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), index=True, nullable=False)
    completed = Column(Boolean, default=False)
    user_id = Column(Integer, index=True, nullable=False)
