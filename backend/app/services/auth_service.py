from __future__ import annotations

import smtplib
import uuid
from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    JWTError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    generate_otp_code,
    hash_secret,
    mask_email,
    verify_secret,
)
from app.db.models import OTPChallenge, User
from app.db.session import get_db_session, get_session_factory
from shared.utils.logger import get_logger

logger = get_logger("customs_brain.auth")
bearer_scheme = HTTPBearer(auto_error=False)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _utcnow() -> datetime:
    return datetime.utcnow()


def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM_EMAIL)


def get_user_role(user: User) -> str:
    return "admin" if _normalize_email(user.email) == _normalize_email(settings.ADMIN_EMAIL) else "general_user"


async def ensure_default_user() -> None:
    async with get_session_factory()() as session:
        admin_created = await _ensure_user(
            session,
            email=_normalize_email(settings.ADMIN_EMAIL),
            password=settings.ADMIN_PASSWORD,
        )
        general_created = await _ensure_user(
            session,
            email=_normalize_email(settings.GENERAL_USER_EMAIL),
            password=settings.GENERAL_USER_PASSWORD,
        )
        if admin_created or general_created:
            await session.commit()


async def begin_password_login(email: str, password: str) -> dict:
    normalized_email = _normalize_email(email)

    async with get_session_factory()() as session:
        user = await _find_user_by_email(session, normalized_email)

        if user is None or not user.is_active or not verify_secret(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        await session.execute(delete(OTPChallenge).where(OTPChallenge.expires_at < _utcnow()))

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

    return _build_auth_response(user)


async def refresh_login_token(refresh_token: str) -> dict:
    try:
        payload = decode_refresh_token(refresh_token)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    async with get_session_factory()() as session:
        user = await _find_user_by_identity(
            session,
            user_id=payload.get("user_id") or payload.get("sub"),
            email=_normalize_email(payload.get("email", "")),
        )

    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return _build_auth_response(user)


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

    user_id = payload.get("user_id") or payload.get("sub")
    email = _normalize_email(payload.get("email", ""))
    if not user_id and not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token payload")

    user = await _find_user_by_identity(session, user_id=user_id, email=email)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def require_role(required_role: str) -> Callable:
    async def _role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if get_user_role(current_user) != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this resource")
        return current_user

    return _role_dependency


require_admin = require_role("admin")


async def _find_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User))
    for user in result.scalars():
        if _normalize_email(user.email) == email:
            return user
    return None


async def _find_user_by_identity(session: AsyncSession, *, user_id: str | None, email: str | None) -> User | None:
    if user_id:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is not None:
            return user

    if email:
        return await _find_user_by_email(session, email)
    return None


async def _ensure_user(session: AsyncSession, *, email: str, password: str) -> bool:
    if not email or not password:
        return False

    user = await _find_user_by_email(session, email)
    if user is not None:
        return False

    session.add(
        User(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=hash_secret(password),
            is_active=True,
        )
    )
    logger.info("Created seeded user %s", mask_email(email))
    return True


def _build_auth_response(user: User) -> dict:
    role = get_user_role(user)
    token_payload = {"sub": user.id, "user_id": user.id, "role": role}
    return {
        "access_token": create_access_token(token_payload),
        "refresh_token": create_refresh_token(token_payload),
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": role,
        },
    }


async def _deliver_otp(email: str, otp_code: str, delivery_channel: str) -> None:
    if delivery_channel == "email":
        await _send_otp_email(email=email, otp_code=otp_code)
        return

    logger.info("Developer OTP generated for %s", mask_email(email))
    if settings.AUTH_DEBUG_OTP_ECHO:
        logger.warning("Developer OTP echo is enabled for %s", mask_email(email))


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
