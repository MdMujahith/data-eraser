"""Application settings loaded from environment / .env file.

All sensitive defaults are empty strings or ``None``; secrets must be provided
via environment variables or the OS keyring — never hardcoded here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from platformdirs import user_data_dir
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from privacy_toolkit.core.constants import (
    APP_SLUG,
    APP_VERSION,
    DEFAULT_RATE_LIMIT_PER_MINUTE,
    DEFAULT_RETRY_MAX,
    DEFAULT_SCHEDULER_INTERVAL_DAYS,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    DB_FILENAME,
    KEYRING_SERVICE,
    ProxyMode,
)


def _default_db_path() -> str:
    data_dir = Path(user_data_dir(APP_SLUG, appauthor=False))
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / DB_FILENAME)


class Settings(BaseSettings):
    """All runtime configuration for the Privacy Toolkit.

    Values are read (in order) from:
    1. Explicit environment variables
    2. ``.env`` file in the current working directory
    3. Defaults defined here
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: str = Field(default="production", description="development | production")
    log_level: str = Field(default="INFO")
    app_version: str = Field(default=APP_VERSION)

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default_factory=lambda: f"sqlite:///{_default_db_path()}",
        description="SQLAlchemy database URL",
    )

    # ── Encryption ────────────────────────────────────────────────────────────
    encryption_key: Optional[str] = Field(
        default=None,
        description="Base64-encoded Fernet key; prefer OS keyring over env var",
    )
    keyring_service_name: str = Field(default=KEYRING_SERVICE)

    # ── Proxy / Network ───────────────────────────────────────────────────────
    proxy_mode: str = Field(default=ProxyMode.NONE)
    proxy_url: Optional[str] = Field(default=None)
    tor_socks_host: str = Field(default="127.0.0.1")
    tor_socks_port: int = Field(default=9050)

    # ── Privacy verification ──────────────────────────────────────────────────
    privacy_verify_enabled: bool = Field(default=False)
    privacy_verify_url: str = Field(default="https://httpbin.org/ip")

    # ── Request behaviour ─────────────────────────────────────────────────────
    request_timeout: int = Field(default=DEFAULT_TIMEOUT)
    request_retry_max: int = Field(default=DEFAULT_RETRY_MAX)
    scan_rate_limit_per_minute: int = Field(default=DEFAULT_RATE_LIMIT_PER_MINUTE)
    user_agent: str = Field(default=DEFAULT_USER_AGENT)

    # ── Scheduler ─────────────────────────────────────────────────────────────
    scheduler_interval_days: int = Field(default=DEFAULT_SCHEDULER_INTERVAL_DAYS)

    # ── Opt-out automation (DISABLED BY DEFAULT) ──────────────────────────────
    auto_optout_enabled: bool = Field(
        default=False,
        description=(
            "Enable automated opt-out form submission. "
            "MUST be explicitly set to true by the user after reviewing docs/privacy-model.md."
        ),
    )

    @field_validator("proxy_mode")
    @classmethod
    def _validate_proxy_mode(cls, v: str) -> str:
        valid = {ProxyMode.NONE, ProxyMode.HTTP, ProxyMode.SOCKS5, ProxyMode.TOR, ProxyMode.VPN_CHECK_ONLY}
        if v not in valid:
            raise ValueError(f"proxy_mode must be one of {valid}")
        return v

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}")
        return upper

    @property
    def effective_proxy_url(self) -> str | None:
        """Return the proxy URL to hand to httpx, accounting for Tor mode."""
        if self.proxy_mode == ProxyMode.TOR:
            return f"socks5://{self.tor_socks_host}:{self.tor_socks_port}"
        if self.proxy_mode in {ProxyMode.HTTP, ProxyMode.SOCKS5}:
            return self.proxy_url
        return None

    @property
    def db_path(self) -> Path:
        """Resolve the file path of the SQLite database."""
        url = self.database_url
        prefix = "sqlite:///"
        if url.startswith(prefix):
            return Path(url[len(prefix):])
        return Path(url)


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the singleton Settings instance (lazy-initialised)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Force re-initialisation of Settings (useful in tests)."""
    global _settings
    _settings = None
