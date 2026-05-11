"""Central HTTP client — all network I/O must go through this module.

Features:
- Proxy / Tor support
- Configurable retry with exponential backoff
- Per-request rate limiting
- robots.txt compliance
- Unified timeout handling
- Redacted logging (no sensitive URLs/params in logs at INFO level)
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Optional

import httpx

from privacy_toolkit.core.constants import (
    DEFAULT_RETRY_MAX,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    ProxyMode,
)
from privacy_toolkit.core.exceptions import NetworkError, RobotsDisallowedError
from privacy_toolkit.core.logging import get_logger
from privacy_toolkit.network.proxy import build_proxy_url
from privacy_toolkit.network.rate_limiter import RateLimiter
from privacy_toolkit.network.robots import check_allowed

logger = get_logger(__name__)

_RETRY_BACKOFF_BASE = 2.0  # seconds


class NetworkClient:
    """Single httpx wrapper for all toolkit HTTP requests.

    Args:
        proxy_mode: Active proxy mode.
        proxy_url: Explicit proxy URL.
        tor_host: Tor SOCKS host.
        tor_port: Tor SOCKS port.
        timeout: Request timeout in seconds.
        retry_max: Maximum number of retries on transient failures.
        rate_limiter: Optional shared :class:`RateLimiter` instance.
        user_agent: User-agent string.
        check_robots: Enforce robots.txt compliance.
    """

    def __init__(
        self,
        proxy_mode: str = ProxyMode.NONE,
        proxy_url: Optional[str] = None,
        tor_host: str = "127.0.0.1",
        tor_port: int = 9050,
        timeout: int = DEFAULT_TIMEOUT,
        retry_max: int = DEFAULT_RETRY_MAX,
        rate_limiter: Optional[RateLimiter] = None,
        user_agent: str = DEFAULT_USER_AGENT,
        check_robots: bool = True,
    ) -> None:
        self.proxy_mode = proxy_mode
        self.timeout = timeout
        self.retry_max = retry_max
        self.rate_limiter = rate_limiter
        self.user_agent = user_agent
        self.check_robots = check_robots

        self._proxy_url = build_proxy_url(proxy_mode, proxy_url, tor_host, tor_port)
        self._base_headers = {"User-Agent": user_agent}

    def _build_client(self) -> httpx.Client:
        kwargs: dict[str, Any] = {
            "timeout": self.timeout,
            "headers": self._base_headers,
            "follow_redirects": True,
        }
        if self._proxy_url:
            kwargs["proxy"] = self._proxy_url
        return httpx.Client(**kwargs)

    def get(
        self,
        url: str,
        params: Optional[dict[str, str]] = None,
        headers: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Perform a rate-limited, retried GET request.

        Args:
            url: Target URL.
            params: Query parameters.
            headers: Additional headers (merged with base headers).

        Returns:
            :class:`httpx.Response`

        Raises:
            :class:`RobotsDisallowedError`: If robots.txt disallows the URL.
            :class:`NetworkError`: On unrecoverable HTTP failure.
        """
        if self.check_robots:
            try:
                check_allowed(url, self.user_agent)
            except RobotsDisallowedError:
                raise
            except Exception as exc:
                logger.debug("robots.txt check error for %s: %s — continuing", url, exc)

        if self.rate_limiter:
            self.rate_limiter.acquire_sync()

        merged_headers = {**self._base_headers, **(headers or {})}

        last_exc: Optional[Exception] = None
        for attempt in range(1, self.retry_max + 2):
            try:
                with self._build_client() as client:
                    resp = client.get(url, params=params, headers=merged_headers, **kwargs)
                    resp.raise_for_status()
                    logger.debug("GET %s → %s", _trunc(url), resp.status_code)
                    return resp
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500:
                    raise NetworkError(f"HTTP {exc.response.status_code} for {_trunc(url)}") from exc
                last_exc = exc
            except (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError) as exc:
                last_exc = exc

            if attempt <= self.retry_max:
                backoff = _RETRY_BACKOFF_BASE ** attempt
                logger.debug("Retry %d/%d for %s in %.1fs", attempt, self.retry_max, _trunc(url), backoff)
                time.sleep(backoff)

        raise NetworkError(f"Request failed after {self.retry_max + 1} attempts: {last_exc}") from last_exc

    def post(
        self,
        url: str,
        data: Optional[dict[str, str]] = None,
        json: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Perform a rate-limited, retried POST request."""
        if self.rate_limiter:
            self.rate_limiter.acquire_sync()

        merged_headers = {**self._base_headers, **(headers or {})}
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.retry_max + 2):
            try:
                with self._build_client() as client:
                    resp = client.post(
                        url,
                        data=data,
                        json=json,
                        headers=merged_headers,
                        **kwargs,
                    )
                    resp.raise_for_status()
                    logger.debug("POST %s → %s", _trunc(url), resp.status_code)
                    return resp
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500:
                    raise NetworkError(f"HTTP {exc.response.status_code} for {_trunc(url)}") from exc
                last_exc = exc
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_exc = exc

            if attempt <= self.retry_max:
                backoff = _RETRY_BACKOFF_BASE ** attempt
                time.sleep(backoff)

        raise NetworkError(f"POST failed after {self.retry_max + 1} attempts: {last_exc}") from last_exc


def _trunc(url: str, n: int = 60) -> str:
    """Truncate URL for safe log output."""
    return url[:n] + "…" if len(url) > n else url


def build_client_from_settings() -> NetworkClient:
    """Construct a :class:`NetworkClient` from the current app settings."""
    from privacy_toolkit.config.settings import get_settings
    s = get_settings()
    limiter = RateLimiter(max_calls=s.scan_rate_limit_per_minute, period=60.0)
    return NetworkClient(
        proxy_mode=s.proxy_mode,
        proxy_url=s.proxy_url,
        tor_host=s.tor_socks_host,
        tor_port=s.tor_socks_port,
        timeout=s.request_timeout,
        retry_max=s.request_retry_max,
        rate_limiter=limiter,
        user_agent=s.user_agent,
    )
