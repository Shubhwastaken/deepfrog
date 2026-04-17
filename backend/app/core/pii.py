"""Deterministic encryption helpers for PII stored in the database."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from functools import lru_cache

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESSIV
from sqlalchemy.types import String, Text, TypeDecorator


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

    def is_encrypted(self, value: str | None) -> bool:
        return bool(value and value.startswith(self._prefix))


@lru_cache(maxsize=1)
def get_pii_codec() -> PIICodec:
    secret = os.getenv("PII_ENCRYPTION_KEY") or os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError("PII_ENCRYPTION_KEY or SECRET_KEY must be set in the environment.")
    return PIICodec(secret)


@lru_cache(maxsize=1)
def get_legacy_pii_codecs() -> tuple[PIICodec, ...]:
    raw_value = os.getenv("PII_ENCRYPTION_LEGACY_KEYS", "")
    secrets = [secret.strip() for secret in raw_value.split(",") if secret.strip()]
    return tuple(PIICodec(secret) for secret in secrets)


def decrypt_pii_value(value: str) -> str:
    """Decrypt a stored value using the primary key, then any configured legacy keys."""

    if not get_pii_codec().is_encrypted(value):
        return value

    codecs = (get_pii_codec(), *get_legacy_pii_codecs())
    last_error: Exception | None = None
    for codec in codecs:
        try:
            return codec.decrypt(value)
        except InvalidTag as exc:
            last_error = exc
            continue

    if last_error is not None:
        raise last_error
    return value


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
        return decrypt_pii_value(value)


class EncryptedJSON(TypeDecorator):
    """SQLAlchemy JSON-like type stored as encrypted text at rest."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):  # type: ignore[no-untyped-def]
        if value is None:
            return None
        if isinstance(value, str) and get_pii_codec().is_encrypted(value):
            return value

        serialized = json.dumps(value)
        return get_pii_codec().encrypt(serialized)

    def process_result_value(self, value, dialect):  # type: ignore[no-untyped-def]
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value

        decrypted = decrypt_pii_value(value)
        return json.loads(decrypted)
