"""Date/time utilities."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional


def utcnow() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(tz=timezone.utc)


def fmt_datetime(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Format a datetime or return '—' for None."""
    if dt is None:
        return "—"
    return dt.strftime(fmt)


def days_since(dt: Optional[datetime]) -> Optional[int]:
    """Return number of days since *dt*, or None."""
    if dt is None:
        return None
    delta = utcnow() - dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else utcnow() - dt
    return delta.days


def next_run_label(days: int) -> str:
    """Return a human label for a next-run offset in days."""
    dt = utcnow() + timedelta(days=days)
    return dt.strftime("%Y-%m-%d")
