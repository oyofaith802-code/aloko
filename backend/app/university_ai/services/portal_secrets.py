from __future__ import annotations

import os

from cryptography.fernet import Fernet, InvalidToken


ENV_KEY = "PORTAL_CREDENTIAL_ENCRYPTION_KEY"


def _get_fernet() -> Fernet:
    key = os.getenv(ENV_KEY)

    if not key:
        raise RuntimeError(
            f"{ENV_KEY} is not configured."
        )

    try:
        return Fernet(key.encode("utf-8"))
    except Exception as exc:
        raise RuntimeError(
            f"{ENV_KEY} is invalid. Generate a valid Fernet key."
        ) from exc


def encrypt_secret(value: str | None) -> str | None:
    if value is None:
        return None

    value = str(value)

    if not value:
        return value

    return _get_fernet().encrypt(
        value.encode("utf-8")
    ).decode("utf-8")


def decrypt_secret(value: str | None) -> str | None:
    if value is None:
        return None

    value = str(value)

    if not value:
        return value

    try:
        return _get_fernet().decrypt(
            value.encode("utf-8")
        ).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError(
            "Portal credential could not be decrypted. "
            "Check PORTAL_CREDENTIAL_ENCRYPTION_KEY."
        ) from exc


def is_encrypted(value: str | None) -> bool:
    if not value:
        return False

    try:
        _get_fernet().decrypt(
            value.encode("utf-8")
        )
        return True
    except Exception:
        return False