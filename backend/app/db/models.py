from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    file_path = Column(String)
    status = Column(String, default="queued")
    results = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
