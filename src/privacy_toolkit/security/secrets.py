"""OS keyring helpers with graceful fallback to env vars."""

from __future__ import annotations

from typing import Optional

from privacy_toolkit.core.logging import get_logger

logger = get_logger(__name__)

_KEYRING_AVAILABLE: Optional[bool] = None


def _keyring_available() -> bool:
    global _KEYRING_AVAILABLE
    if _KEYRING_AVAILABLE is None:
        try:
            import keyring  # noqa: F401
            _KEYRING_AVAILABLE = True
        except ImportError:
            _KEYRING_AVAILABLE = False
    return _KEYRING_AVAILABLE


def store_secret(service: str, username: str, secret: str) -> bool:
    """Store a secret in the OS keyring.

    Returns:
        ``True`` if stored successfully, ``False`` if keyring unavailable.
    """
    if not _keyring_available():
        logger.warning("keyring not available; secret not stored in OS keychain.")
        return False
    import keyring
    keyring.set_password(service, username, secret)
    logger.info("Secret stored in OS keyring: service=%r, username=%r", service, username)
    return True


def retrieve_secret(service: str, username: str) -> Optional[str]:
    """Retrieve a secret from the OS keyring.

    Returns:
        The secret string or ``None`` if not found / keyring unavailable.
    """
    if not _keyring_available():
        return None
    try:
        import keyring
        return keyring.get_password(service, username)
    except Exception as exc:
        logger.debug("keyring retrieval failed: %s", exc)
        return None


def delete_secret(service: str, username: str) -> bool:
    """Delete a secret from the OS keyring."""
    if not _keyring_available():
        return False
    try:
        import keyring
        keyring.delete_password(service, username)
        return True
    except Exception:
        return False
