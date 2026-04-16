from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from jose import JWTError, jwt

from app.core.config import settings

PASSWORD_HASH_ITERATIONS = 390000


def _create_token(data: dict, *, expires_delta: timedelta, token_type: str) -> str:
    expire = datetime.utcnow() + expires_delta
    return jwt.encode(
        {**data, "exp": expire, "token_type": token_type},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_access_token(data: dict) -> str:
    return _create_token(
        data,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
    )


def create_refresh_token(data: dict) -> str:
    return _create_token(
        data,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    if payload.get("token_type") != "access":
        raise JWTError("Expected an access token.")
    return payload


def decode_refresh_token(token: str) -> dict:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    if payload.get("token_type") != "refresh":
        raise JWTError("Expected a refresh token.")
    return payload


def hash_secret(secret: str) -> str:
    salt = secrets.token_hex(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        secret.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_HASH_ITERATIONS,
    )
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${salt}${derived_key.hex()}"


def verify_secret(secret: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected_hash = stored_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        secret.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
        )
    return hmac.compare_digest(derived_key.hex(), expected_hash)


def generate_otp_code(length: int | None = None) -> str:
    otp_length = length or settings.OTP_LENGTH
    return "".join(str(secrets.randbelow(10)) for _ in range(otp_length))


def mask_email(email: str) -> str:
    local_part, _, domain = email.partition("@")
    if not domain:
        return email
    if len(local_part) <= 2:
        masked_local = f"{local_part[0]}*" if local_part else "*"
    else:
        masked_local = f"{local_part[0]}{'*' * (len(local_part) - 2)}{local_part[-1]}"
    return f"{masked_local}@{domain}"


__all__ = [
    "JWTError",
    "create_access_token",
    "create_refresh_token",
    "decode_refresh_token",
    "decode_access_token",
    "generate_otp_code",
    "hash_secret",
    "mask_email",
    "verify_secret",
]
