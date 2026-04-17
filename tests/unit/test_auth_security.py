import asyncio
import base64
import sys
import time
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from jose import jwt as jose_jwt

sys.path.insert(0, str(Path("backend").resolve()))

from app.core.pii import EncryptedJSON, PIICodec, decrypt_pii_value, get_legacy_pii_codecs, get_pii_codec
from app.core.security import JWTError, create_access_token, create_refresh_token, decode_access_token, decode_refresh_token
from app.services import auth_service


def test_access_and_refresh_tokens_are_strictly_typed():
    access_token = create_access_token({"sub": "user-123", "role": "general_user"})
    refresh_token = create_refresh_token({"sub": "user-123", "role": "general_user"})

    assert decode_access_token(access_token)["sub"] == "user-123"
    assert decode_refresh_token(refresh_token)["sub"] == "user-123"

    with pytest.raises(JWTError):
        decode_access_token(refresh_token)

    with pytest.raises(JWTError):
        decode_refresh_token(access_token)


def test_pii_codec_encrypts_and_supports_plaintext_backcompat():
    codec = PIICodec("unit-test-secret")
    plaintext = "user@example.com"

    encrypted = codec.encrypt(plaintext)

    assert encrypted.startswith("enc::")
    assert encrypted != plaintext
    assert codec.decrypt(encrypted) == plaintext
    assert codec.decrypt("legacy@example.com") == "legacy@example.com"


def test_encrypted_json_round_trips_and_supports_plaintext_backcompat(monkeypatch):
    monkeypatch.setenv("PII_ENCRYPTION_KEY", "unit-test-secret")
    get_pii_codec.cache_clear()

    encrypted_json = EncryptedJSON()
    payload = {
        "product_description": "Customer laptop order",
        "destination_country": "United States",
        "contact_email": "buyer@example.com",
    }

    stored_value = encrypted_json.process_bind_param(payload, dialect=None)

    assert isinstance(stored_value, str)
    assert stored_value.startswith("enc::")
    assert encrypted_json.process_result_value(stored_value, dialect=None) == payload

    plaintext_json = '{"contact_email":"legacy@example.com"}'
    assert encrypted_json.process_result_value(plaintext_json, dialect=None) == {
        "contact_email": "legacy@example.com"
    }


def test_decrypt_pii_value_supports_legacy_keys(monkeypatch):
    legacy_codec = PIICodec("legacy-secret")
    encrypted = legacy_codec.encrypt("legacy@example.com")

    monkeypatch.setenv("PII_ENCRYPTION_KEY", "current-secret")
    monkeypatch.setenv("PII_ENCRYPTION_LEGACY_KEYS", "legacy-secret")
    get_pii_codec.cache_clear()
    get_legacy_pii_codecs.cache_clear()

    assert decrypt_pii_value(encrypted) == "legacy@example.com"


def test_google_provider_status_reflects_configuration(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "GOOGLE_CLIENT_ID", "client-123")

    providers = auth_service.get_auth_provider_status()

    assert providers["password_otp_enabled"] is True
    assert providers["google"]["enabled"] is True
    assert providers["google"]["client_id"] == "client-123"


def test_verify_google_id_token_accepts_valid_token(monkeypatch):
    token, jwks = _build_google_token(
        {
            "iss": "https://accounts.google.com",
            "aud": "unit-google-client",
            "sub": "google-user-123",
            "email": "judge@example.com",
            "email_verified": True,
            "exp": int(time.time()) + 600,
        }
    )

    async def _fake_get_google_jwks():
        return jwks

    monkeypatch.setattr(auth_service.settings, "GOOGLE_CLIENT_ID", "unit-google-client")
    monkeypatch.setattr(auth_service.settings, "GOOGLE_ALLOWED_DOMAIN", "")
    monkeypatch.setattr(auth_service, "_get_google_jwks", _fake_get_google_jwks)

    claims = asyncio.run(auth_service._verify_google_id_token(token))

    assert claims["sub"] == "google-user-123"
    assert claims["email"] == "judge@example.com"


def test_verify_google_id_token_rejects_wrong_hosted_domain(monkeypatch):
    token, jwks = _build_google_token(
        {
            "iss": "https://accounts.google.com",
            "aud": "unit-google-client",
            "sub": "google-user-123",
            "email": "judge@example.com",
            "email_verified": True,
            "hd": "other.example",
            "exp": int(time.time()) + 600,
        }
    )

    async def _fake_get_google_jwks():
        return jwks

    monkeypatch.setattr(auth_service.settings, "GOOGLE_CLIENT_ID", "unit-google-client")
    monkeypatch.setattr(auth_service.settings, "GOOGLE_ALLOWED_DOMAIN", "srmist.edu.in")
    monkeypatch.setattr(auth_service, "_get_google_jwks", _fake_get_google_jwks)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(auth_service._verify_google_id_token(token))

    assert exc_info.value.status_code == 403


def _build_google_token(claims: dict) -> tuple[str, dict]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_numbers = private_key.public_key().public_numbers()
    kid = "unit-test-kid"
    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "alg": "RS256",
                "use": "sig",
                "kid": kid,
                "n": _b64url_uint(public_numbers.n),
                "e": _b64url_uint(public_numbers.e),
            }
        ]
    }
    token = jose_jwt.encode(claims, private_pem, algorithm="RS256", headers={"kid": kid})
    return token, jwks


def _b64url_uint(value: int) -> str:
    width = (value.bit_length() + 7) // 8
    payload = value.to_bytes(width, "big")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
