"""Encryption utilities for sensitive data (miner passwords)."""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def _get_fernet() -> Fernet:
    """Get Fernet instance from SECRET_KEY env."""
    secret = os.getenv("SECRET_KEY", "change-me-in-production-secret-key")
    # Derive a valid Fernet key (32 url-safe base64-encoded bytes)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"miner-agent-salt",
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
    return Fernet(key)


def encrypt_password(plain: str | None) -> str | None:
    """Encrypt miner password for storage."""
    if plain is None or plain == "":
        return None
    return _get_fernet().encrypt(plain.encode()).decode()


def decrypt_password(encrypted: str | None) -> str | None:
    """Decrypt stored password."""
    if encrypted is None or encrypted == "":
        return None
    try:
        return _get_fernet().decrypt(encrypted.encode()).decode()
    except Exception:
        return None
