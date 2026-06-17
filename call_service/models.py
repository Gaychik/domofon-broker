from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
