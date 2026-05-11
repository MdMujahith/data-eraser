"""Tests for network anonymizer and rate limiter."""

from __future__ import annotations

import asyncio
import time

import pytest

from privacy_toolkit.network.rate_limiter import RateLimiter
from privacy_toolkit.core.exceptions import RateLimitError


def test_rate_limiter_allows_within_limit() -> None:
    limiter = RateLimiter(max_calls=5, period=60.0)
    for _ in range(5):
        limiter.acquire_sync()  # should not raise


def test_rate_limiter_fail_on_limit() -> None:
    limiter = RateLimiter(max_calls=2, period=60.0, fail_on_limit=True)
    limiter.acquire_sync()
    limiter.acquire_sync()
    with pytest.raises(RateLimitError):
        limiter.acquire_sync()


def test_rate_limiter_window_expiry() -> None:
    limiter = RateLimiter(max_calls=2, period=0.1, fail_on_limit=True)
    limiter.acquire_sync()
    limiter.acquire_sync()
    time.sleep(0.15)
    limiter.acquire_sync()  # window expired — should succeed


@pytest.mark.asyncio
async def test_rate_limiter_async() -> None:
    limiter = RateLimiter(max_calls=3, period=60.0)
    for _ in range(3):
        await limiter.acquire()  # should not raise


def test_proxy_url_tor() -> None:
    from privacy_toolkit.network.proxy import build_proxy_url
    from privacy_toolkit.core.constants import ProxyMode
    url = build_proxy_url(ProxyMode.TOR, tor_host="127.0.0.1", tor_port=9050)
    assert url == "socks5://127.0.0.1:9050"


def test_proxy_url_none() -> None:
    from privacy_toolkit.network.proxy import build_proxy_url
    from privacy_toolkit.core.constants import ProxyMode
    assert build_proxy_url(ProxyMode.NONE) is None


def test_robots_cache_clears() -> None:
    from privacy_toolkit.network.robots import clear_robots_cache
    clear_robots_cache()  # should not raise


def test_redaction_in_logs() -> None:
    from privacy_toolkit.core.logging import SensitiveDataFilter
    import logging
    f = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test", level=logging.INFO,
        pathname="", lineno=0,
        msg="Email is john@example.com and phone 9876543210",
        args=(), exc_info=None,
    )
    f.filter(record)
    assert "john@example.com" not in record.msg
    assert "9876543210" not in record.msg
    assert "[REDACTED]" in record.msg
