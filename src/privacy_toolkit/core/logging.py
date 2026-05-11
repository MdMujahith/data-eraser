"""Centralised logging configuration with Rich handler and redaction filter."""

from __future__ import annotations

import logging
import re
from typing import ClassVar

from rich.logging import RichHandler

_SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", re.IGNORECASE),   # email
    re.compile(r"\b\d{10}\b"),                                       # 10-digit phone
    re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),              # phone w/ separators
]


class SensitiveDataFilter(logging.Filter):
    """Strip sensitive patterns from log records before emission."""

    REDACT_PATTERNS: ClassVar[list[re.Pattern[str]]] = _SENSITIVE_PATTERNS

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.msg = self._redact(str(record.msg))
        record.args = tuple(self._redact(str(a)) if isinstance(a, str) else a for a in (record.args or ()))
        return True

    @staticmethod
    def _redact(text: str) -> str:
        for pattern in _SENSITIVE_PATTERNS:
            text = pattern.sub("[REDACTED]", text)
        return text


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Return a Rich-formatted, redaction-filtered logger.

    Args:
        name: Logger namespace (typically ``__name__``).
        level: Log level string, e.g. ``"DEBUG"``, ``"INFO"``.

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = RichHandler(
            rich_tracebacks=True,
            markup=False,
            show_path=False,
        )
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


def configure_root(level: str = "INFO") -> None:
    """Configure the root logger once at startup."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                markup=False,
                show_path=False,
            )
        ],
    )
    # Quiet noisy third-party loggers
    for noisy in ("httpx", "httpcore", "apscheduler", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
