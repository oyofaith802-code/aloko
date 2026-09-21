from __future__ import annotations

import hashlib
import hmac
import os
import secrets


ENV_KEY = "ALOKO_PORTAL_API_KEY"


def generate_api_key() -> str:
    return "aloko_" + secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def verify_api_key(api_key: str, expected_hash: str) -> bool:
    if not api_key or not expected_hash:
        return False

    provided_hash = hash_api_key(api_key)

    return hmac.compare_digest(
        provided_hash,
        expected_hash,
    )


def get_server_api_key_hash() -> str | None:
    return os.getenv(ENV_KEY)