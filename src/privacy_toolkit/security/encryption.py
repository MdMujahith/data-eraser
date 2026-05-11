"""Fernet-based symmetric encryption for sensitive local data."""

from __future__ import annotations

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from privacy_toolkit.core.exceptions import EncryptionError, EncryptionKeyMissingError
from privacy_toolkit.core.logging import get_logger

logger = get_logger(__name__)


def generate_key() -> str:
    """Generate a new Fernet key and return it as a base64 string."""
    return Fernet.generate_key().decode()


def _get_fernet(key: Optional[str] = None) -> Fernet:
    """Resolve key from argument → env var → keyring, then build Fernet."""
    resolved = key

    if not resolved:
        resolved = os.environ.get("ENCRYPTION_KEY")

    if not resolved:
        try:
            import keyring
            from privacy_toolkit.core.constants import KEYRING_SERVICE, KEYRING_USERNAME
            resolved = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        except Exception:
            pass

    if not resolved:
        raise EncryptionKeyMissingError(
            "No encryption key found. Run `privacy-toolkit init --generate-key` "
            "and set ENCRYPTION_KEY in .env or store it in the OS keyring."
        )

    try:
        raw = resolved.encode() if isinstance(resolved, str) else resolved
        # Tolerate URL-safe base64 with or without padding
        padded = raw + b"=" * (-len(raw) % 4)
        base64.urlsafe_b64decode(padded)  # validate format
        return Fernet(raw)
    except Exception as exc:
        raise EncryptionError(f"Invalid encryption key format: {exc}") from exc


class FieldEncryptor:
    """Encrypt/decrypt individual string fields for DB storage.

    Usage::

        enc = FieldEncryptor()
        token = enc.encrypt("john.doe@example.com")
        plain = enc.decrypt(token)
    """

    def __init__(self, key: Optional[str] = None) -> None:
        self._fernet = _get_fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string and return a base64 token."""
        try:
            return self._fernet.encrypt(plaintext.encode()).decode()
        except Exception as exc:
            raise EncryptionError(f"Encryption failed: {exc}") from exc

    def decrypt(self, token: str) -> str:
        """Decrypt a base64 token and return the original string."""
        try:
            return self._fernet.decrypt(token.encode()).decode()
        except InvalidToken as exc:
            raise EncryptionError("Decryption failed — wrong key or corrupted token.") from exc
        except Exception as exc:
            raise EncryptionError(f"Decryption error: {exc}") from exc

    def encrypt_optional(self, value: Optional[str]) -> Optional[str]:
        """Encrypt value if not None; return None otherwise."""
        return self.encrypt(value) if value is not None else None

    def decrypt_optional(self, token: Optional[str]) -> Optional[str]:
        """Decrypt token if not None; return None otherwise."""
        return self.decrypt(token) if token is not None else None


_encryptor: Optional[FieldEncryptor] = None


def get_encryptor(key: Optional[str] = None) -> FieldEncryptor:
    """Return singleton FieldEncryptor (lazy-init)."""
    global _encryptor
    if _encryptor is None:
        _encryptor = FieldEncryptor(key)
    return _encryptor


def reset_encryptor() -> None:
    """Force re-initialisation (useful in tests)."""
    global _encryptor
    _encryptor = None
