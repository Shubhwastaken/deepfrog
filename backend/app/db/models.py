from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, JSON, String, Text
from sqlalchemy.orm import declarative_base
from app.core.pii import EncryptedString

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(EncryptedString(512), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class OTPChallenge(Base):
    __tablename__ = "otp_challenges"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    email = Column(EncryptedString(512), nullable=False, index=True)
    code_hash = Column(String, nullable=False)
    delivery_channel = Column(String, nullable=False, default="email")
    expires_at = Column(DateTime, nullable=False)
    consumed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    owner_email = Column(EncryptedString(512), nullable=True, index=True)
    invoice_path = Column(EncryptedString(1024), nullable=False)
    bill_of_lading_path = Column(EncryptedString(1024), nullable=False)
    status = Column(String, default="queued")
    results = Column(JSON, nullable=True)
    report_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
