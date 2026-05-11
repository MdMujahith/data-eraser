"""Custom exception hierarchy for the Privacy Toolkit."""

from __future__ import annotations


class PrivacyToolkitError(Exception):
    """Base exception for all toolkit errors."""


# ── Config ────────────────────────────────────────────────────────────────────
class ConfigError(PrivacyToolkitError):
    """Configuration load or validation failure."""


class EncryptionKeyMissingError(ConfigError):
    """No encryption key found — run `privacy-toolkit init` first."""


# ── Database ──────────────────────────────────────────────────────────────────
class DatabaseError(PrivacyToolkitError):
    """Database operation failure."""


class RecordNotFoundError(DatabaseError):
    """Requested record does not exist."""

    def __init__(self, model: str, record_id: int | str) -> None:
        super().__init__(f"{model} with id={record_id!r} not found")
        self.model = model
        self.record_id = record_id


# ── Network ───────────────────────────────────────────────────────────────────
class NetworkError(PrivacyToolkitError):
    """Generic network or HTTP failure."""


class ProxyVerificationError(NetworkError):
    """Privacy proxy/Tor verification failed — scan aborted (fail-closed)."""


class RobotsDisallowedError(NetworkError):
    """robots.txt disallows crawling the requested URL."""

    def __init__(self, url: str) -> None:
        super().__init__(f"robots.txt disallows: {url}")
        self.url = url


class RateLimitError(NetworkError):
    """Outbound request rate limit exceeded."""


# ── Encryption / Security ─────────────────────────────────────────────────────
class EncryptionError(PrivacyToolkitError):
    """Encryption or decryption failure."""


class RedactionError(PrivacyToolkitError):
    """Redaction helper failure."""


# ── Recon ─────────────────────────────────────────────────────────────────────
class ReconError(PrivacyToolkitError):
    """Recon scan failure."""


class BrokerAdapterError(ReconError):
    """Broker adapter raised an error during scan."""


class ParserError(ReconError):
    """HTML/response parsing failure."""


# ── Opt-out ───────────────────────────────────────────────────────────────────
class OptOutError(PrivacyToolkitError):
    """Opt-out workflow failure."""


class AutoOptOutDisabledError(OptOutError):
    """Automated opt-out is disabled — user must enable it explicitly."""


class CaptchaRequiredError(OptOutError):
    """CAPTCHA detected; manual intervention required."""


class EmailVerificationRequiredError(OptOutError):
    """Email click-through verification required."""


# ── Scheduler ─────────────────────────────────────────────────────────────────
class SchedulerError(PrivacyToolkitError):
    """APScheduler operation failure."""


# ── Status machine ────────────────────────────────────────────────────────────
class InvalidStatusTransitionError(PrivacyToolkitError):
    """Attempted an illegal status transition."""

    def __init__(self, from_status: str, to_status: str) -> None:
        super().__init__(f"Invalid transition: {from_status!r} → {to_status!r}")
        self.from_status = from_status
        self.to_status = to_status
