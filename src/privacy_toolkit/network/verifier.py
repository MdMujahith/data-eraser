"""Pre-scan privacy route verification.

When ``privacy_verify_enabled=True``, every scan must pass this check first.
On failure the scan is aborted (fail-closed model).

This module does NOT guarantee anonymity. It performs a best-effort IP
check and warns the user clearly about limitations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

import httpx

from privacy_toolkit.core.constants import IP_CHECK_URLS, ProxyMode
from privacy_toolkit.core.exceptions import ProxyVerificationError
from privacy_toolkit.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RouteInfo:
    """Result of a route verification check."""

    public_ip: Optional[str]
    proxy_mode: str
    proxy_active: bool
    tor_confirmed: bool
    verification_url: str
    warning: Optional[str] = None


def verify_current_route(
    proxy_mode: str = ProxyMode.NONE,
    proxy_url: Optional[str] = None,
    tor_host: str = "127.0.0.1",
    tor_port: int = 9050,
    timeout: float = 10.0,
    fail_closed: bool = True,
) -> RouteInfo:
    """Check the current public IP and proxy status.

    Args:
        proxy_mode: Active proxy mode.
        proxy_url: Explicit proxy URL (for HTTP/SOCKS5 modes).
        tor_host: Tor SOCKS host.
        tor_port: Tor SOCKS port.
        timeout: HTTP request timeout.
        fail_closed: If ``True``, raise :class:`ProxyVerificationError` when
            the expected proxy is not confirmed active.

    Returns:
        :class:`RouteInfo` with IP and proxy status.

    Raises:
        :class:`ProxyVerificationError`: When fail_closed and verification fails.
    """
    # Determine effective proxy
    effective_proxy: Optional[str] = None
    if proxy_mode == ProxyMode.TOR:
        effective_proxy = f"socks5://{tor_host}:{tor_port}"
    elif proxy_mode in {ProxyMode.HTTP, ProxyMode.SOCKS5} and proxy_url:
        effective_proxy = proxy_url

    public_ip: Optional[str] = None
    verification_url = IP_CHECK_URLS[0]
    warning: Optional[str] = None

    for check_url in IP_CHECK_URLS:
        try:
            client_kwargs: dict = {"timeout": timeout}
            if effective_proxy:
                client_kwargs["proxy"] = effective_proxy
            with httpx.Client(**client_kwargs) as client:
                resp = client.get(check_url)
                resp.raise_for_status()
                text = resp.text.strip()
                # Try JSON parse first (httpbin, ipify)
                try:
                    data = json.loads(text)
                    public_ip = data.get("ip") or data.get("origin") or data.get("IP")
                except (json.JSONDecodeError, AttributeError):
                    # icanhazip returns plain IP
                    public_ip = text if text else None
                verification_url = check_url
                break
        except Exception as exc:
            logger.debug("IP check failed at %s: %s", check_url, exc)
            continue

    if public_ip is None:
        warning = "Could not determine public IP — all check URLs failed."
        if fail_closed and proxy_mode not in {ProxyMode.NONE, ProxyMode.VPN_CHECK_ONLY}:
            raise ProxyVerificationError(f"Proxy verification failed (fail-closed): {warning}")

    # Tor confirmation
    tor_confirmed = False
    if proxy_mode == ProxyMode.TOR:
        from privacy_toolkit.network.tor import check_tor_proxy
        tor_confirmed, _ = check_tor_proxy(tor_host, tor_port, timeout)
        if not tor_confirmed:
            warning = "Tor proxy unreachable or not confirmed by check.torproject.org"
            if fail_closed:
                raise ProxyVerificationError(f"Tor verification failed (fail-closed): {warning}")

    proxy_active = effective_proxy is not None and public_ip is not None

    route = RouteInfo(
        public_ip=public_ip,
        proxy_mode=proxy_mode,
        proxy_active=proxy_active,
        tor_confirmed=tor_confirmed,
        verification_url=verification_url,
        warning=warning,
    )
    logger.info(
        "Route verification: mode=%s ip=%s tor=%s warning=%s",
        proxy_mode,
        "[REDACTED]",
        tor_confirmed,
        warning,
    )
    return route
