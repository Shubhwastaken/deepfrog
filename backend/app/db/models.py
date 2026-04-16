from sqlalchemy import Column, String, DateTime, JSON, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)                       # UUID
    status = Column(String, default="queued")                    # queued | processing | completed | failed
    invoice_path = Column(String, nullable=False)
    bol_path = Column(String, nullable=False)
    file_hash = Column(String, unique=True, index=True)         # SHA-256 for idempotency
    result = Column(JSON, nullable=True)                        # Pipeline output
    retries = Column(Integer, default=0)                        # Max 2 retries
    error_message = Column(Text, nullable=True)                 # Failure reason
    queued_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email_obfuscated = Column(String, nullable=False) # Fernet encrypted PII
    email_hash = Column(String, unique=True, index=True, nullable=False) # Blind index for search
    password_hash = Column(String, nullable=False)  # Hashed with PBKDF2/Bcrypt
    name_obfuscated = Column(String, nullable=True)   # Fernet encrypted PII
    created_at = Column(DateTime, default=datetime.utcnow)
