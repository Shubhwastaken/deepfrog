import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path("backend").resolve()))

from app.core.pii import PIICodec
from app.core.security import JWTError, create_access_token, create_refresh_token, decode_access_token, decode_refresh_token


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
