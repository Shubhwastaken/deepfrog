from __future__ import annotations

import logging
import smtplib
import uuid
from datetime import datetime, timedelta
from email.message import EmailMessage

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    JWTError,
    create_access_token,
    decode_access_token,
    generate_otp_code,
    hash_secret,
    mask_email,
    verify_secret,
)
from app.db.models import OTPChallenge, User
from app.db.session import get_db_session, get_session_factory

logger = logging.getLogger("customs_brain.auth")
bearer_scheme = HTTPBearer(auto_error=False)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _utcnow() -> datetime:
    return datetime.utcnow()


def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM_EMAIL)


async def ensure_default_user() -> None:
    email = _normalize_email(settings.ADMIN_EMAIL)
    password = settings.ADMIN_PASSWORD
    if not email or not password:
        return

    async with get_session_factory()() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        password_hash = hash_secret(password)

        if user is None:
            session.add(
                User(
                    id=str(uuid.uuid4()),
                    email=email,
                    password_hash=password_hash,
                    is_active=True,
                )
            )
            await session.commit()


async def begin_password_login(email: str, password: str) -> dict:
    normalized_email = _normalize_email(email)

    async with get_session_factory()() as session:
        result = await session.execute(select(User).where(User.email == normalized_email))
        user = result.scalar_one_or_none()

        if user is None or not user.is_active or not verify_secret(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        await session.execute(
            delete(OTPChallenge).where(
                (OTPChallenge.email == normalized_email) & (OTPChallenge.expires_at < _utcnow())
            )
        )

        otp_code = generate_otp_code()
        expires_at = _utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        delivery_channel = "email" if _smtp_configured() else "developer_echo"
        challenge = OTPChallenge(
            id=str(uuid.uuid4()),
            user_id=user.id,
            email=normalized_email,
            code_hash=hash_secret(otp_code),
            delivery_channel=delivery_channel,
            expires_at=expires_at,
        )
        session.add(challenge)
        await session.commit()

    await _deliver_otp(email=normalized_email, otp_code=otp_code, delivery_channel=delivery_channel)

    payload = {
        "challenge_id": challenge.id,
        "otp_required": True,
        "delivery_channel": delivery_channel,
        "masked_destination": mask_email(normalized_email),
        "expires_in_seconds": settings.OTP_EXPIRE_MINUTES * 60,
    }
    if settings.AUTH_DEBUG_OTP_ECHO:
        payload["debug_otp"] = otp_code
    return payload


async def verify_login_otp(challenge_id: str, otp_code: str) -> dict:
    async with get_session_factory()() as session:
        challenge_result = await session.execute(select(OTPChallenge).where(OTPChallenge.id == challenge_id))
        challenge = challenge_result.scalar_one_or_none()

        if challenge is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP challenge")
        if challenge.consumed_at is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OTP has already been used")
        if challenge.expires_at < _utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OTP has expired")
        if not verify_secret(otp_code, challenge.code_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP code")

        user_result = await session.execute(select(User).where(User.id == challenge.user_id))
        user = user_result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is not available")

        challenge.consumed_at = _utcnow()
        await session.commit()

    return {
        "access_token": create_access_token({"sub": user.email, "user_id": user.id}),
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
        },
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from exc

    user_id = payload.get("user_id")
    email = _normalize_email(payload.get("sub", ""))
    if not user_id and not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token payload")

    query = select(User)
    if user_id:
        query = query.where(User.id == user_id)
    else:
        query = query.where(User.email == email)

    result = await session.execute(query)
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


async def _deliver_otp(email: str, otp_code: str, delivery_channel: str) -> None:
    if delivery_channel == "email":
        await _send_otp_email(email=email, otp_code=otp_code)
        return

    logger.info("OTP for %s is %s", email, otp_code)


async def _send_otp_email(email: str, otp_code: str) -> None:
    message = EmailMessage()
    message["Subject"] = "Your Customs Brain login code"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = email
    message.set_content(
        f"Your Customs Brain one-time login code is {otp_code}. "
        f"It expires in {settings.OTP_EXPIRE_MINUTES} minutes."
    )

    def _send() -> None:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)

    import asyncio

    await asyncio.to_thread(_send)
