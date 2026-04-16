"""Deterministic encryption helpers for PII stored in the database."""

from __future__ import annotations

import base64
import hashlib
import os
from functools import lru_cache

from cryptography.hazmat.primitives.ciphers.aead import AESSIV
from sqlalchemy.types import String, TypeDecorator


class PIICodec:
    """Encrypt/decrypt strings using deterministic authenticated encryption."""

    _prefix = "enc::"

    def __init__(self, secret: str) -> None:
        key_material = hashlib.sha512(secret.encode("utf-8")).digest()
        self._cipher = AESSIV(key_material)

    def encrypt(self, value: str) -> str:
        if value.startswith(self._prefix):
            return value
        ciphertext = self._cipher.encrypt(value.encode("utf-8"), [b"customs-brain-pii"])
        return f"{self._prefix}{base64.urlsafe_b64encode(ciphertext).decode('ascii')}"

    def decrypt(self, value: str) -> str:
        if not value.startswith(self._prefix):
            return value
        payload = base64.urlsafe_b64decode(value[len(self._prefix):].encode("ascii"))
        plaintext = self._cipher.decrypt(payload, [b"customs-brain-pii"])
        return plaintext.decode("utf-8")


@lru_cache(maxsize=1)
def get_pii_codec() -> PIICodec:
    secret = os.getenv("PII_ENCRYPTION_KEY") or os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError("PII_ENCRYPTION_KEY or SECRET_KEY must be set in the environment.")
    return PIICodec(secret)


class EncryptedString(TypeDecorator):
    """SQLAlchemy string type that encrypts PII at rest while preserving reads."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:  # type: ignore[no-untyped-def]
        if value is None:
            return None
        return get_pii_codec().encrypt(value)

    def process_result_value(self, value: str | None, dialect) -> str | None:  # type: ignore[no-untyped-def]
        if value is None:
            return None
        return get_pii_codec().decrypt(value)
