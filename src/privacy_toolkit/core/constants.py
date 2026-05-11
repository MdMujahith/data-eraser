"""Application-wide constants."""

from __future__ import annotations

APP_NAME = "Privacy Toolkit"
APP_SLUG = "privacy_toolkit"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Personal Data Broker Tracking & Cleanup Command Center"

# ── Status values ─────────────────────────────────────────────────────────────
class Status:
    NOT_STARTED = "NOT_STARTED"
    SCANNING = "SCANNING"
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    REQUEST_READY = "REQUEST_READY"
    REQUEST_SENT = "REQUEST_SENT"
    EMAIL_VERIFICATION_REQUIRED = "EMAIL_VERIFICATION_REQUIRED"
    MANUAL_CAPTCHA_REQUIRED = "MANUAL_CAPTCHA_REQUIRED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RESCAN_REQUIRED = "RESCAN_REQUIRED"

    ALL: list[str] = [
        NOT_STARTED,
        SCANNING,
        FOUND,
        NOT_FOUND,
        REQUEST_READY,
        REQUEST_SENT,
        EMAIL_VERIFICATION_REQUIRED,
        MANUAL_CAPTCHA_REQUIRED,
        MANUAL_REVIEW_REQUIRED,
        COMPLETED,
        FAILED,
        RESCAN_REQUIRED,
    ]

    # Terminal states (no further transitions expected)
    TERMINAL: list[str] = [NOT_FOUND, COMPLETED, FAILED]

    # States requiring human action
    MANUAL_REQUIRED: list[str] = [
        MANUAL_CAPTCHA_REQUIRED,
        MANUAL_REVIEW_REQUIRED,
        EMAIL_VERIFICATION_REQUIRED,
    ]


# ── Broker categories ─────────────────────────────────────────────────────────
class BrokerCategory:
    PEOPLE_SEARCH = "people_search"
    DATA_AGGREGATOR = "data_aggregator"
    MARKETING = "marketing"
    BACKGROUND_CHECK = "background_check"
    CREDIT_REPORTING = "credit_reporting"
    SOCIAL_MEDIA = "social_media"
    PUBLIC_RECORDS = "public_records"
    OTHER = "other"

    ALL: list[str] = [
        PEOPLE_SEARCH,
        DATA_AGGREGATOR,
        MARKETING,
        BACKGROUND_CHECK,
        CREDIT_REPORTING,
        SOCIAL_MEDIA,
        PUBLIC_RECORDS,
        OTHER,
    ]


# ── Proxy modes ───────────────────────────────────────────────────────────────
class ProxyMode:
    NONE = "none"
    HTTP = "http"
    SOCKS5 = "socks5"
    TOR = "tor"
    VPN_CHECK_ONLY = "vpn-check-only"


# ── Network defaults ──────────────────────────────────────────────────────────
DEFAULT_TIMEOUT = 30
DEFAULT_RETRY_MAX = 3
DEFAULT_RATE_LIMIT_PER_MINUTE = 10
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
IP_CHECK_URLS: list[str] = [
    "https://httpbin.org/ip",
    "https://api.ipify.org?format=json",
    "https://icanhazip.com",
]

# ── Scheduler ─────────────────────────────────────────────────────────────────
DEFAULT_SCHEDULER_INTERVAL_DAYS = 30
SCHEDULER_JOB_ID_RECURRING_SCAN = "recurring_privacy_scan"

# ── Database ──────────────────────────────────────────────────────────────────
DB_FILENAME = "privacy_toolkit.db"

# ── Encryption ────────────────────────────────────────────────────────────────
KEYRING_SERVICE = "privacy_toolkit"
KEYRING_USERNAME = "fernet_key"
SENSITIVE_FIELDS: list[str] = [
    "full_name",
    "email",
    "phone",
    "address",
    "date_of_birth",
]

# ── TUI ───────────────────────────────────────────────────────────────────────
TUI_TITLE = "PRIVACY TOOLKIT"
TUI_WELCOME = "Welcome to PRIVATE DATA CLEANUP TOOLKIT"
