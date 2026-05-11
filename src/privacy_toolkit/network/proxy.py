"""Proxy configuration helpers for httpx."""

from __future__ import annotations

from typing import Optional

from privacy_toolkit.core.constants import ProxyMode
from privacy_toolkit.core.logging import get_logger

logger = get_logger(__name__)


def build_proxy_url(
    mode: str,
    proxy_url: Optional[str] = None,
    tor_host: str = "127.0.0.1",
    tor_port: int = 9050,
) -> Optional[str]:
    """Return the proxy URL string to pass to httpx, or None for direct.

    Args:
        mode: One of the :class:`~privacy_toolkit.core.constants.ProxyMode` values.
        proxy_url: Explicit proxy URL for HTTP/SOCKS5 modes.
        tor_host: Tor SOCKS host.
        tor_port: Tor SOCKS port.

    Returns:
        Proxy URL string or ``None``.
    """
    if mode == ProxyMode.TOR:
        url = f"socks5://{tor_host}:{tor_port}"
        logger.debug("Using Tor proxy: %s", url)
        return url
    if mode in {ProxyMode.HTTP, ProxyMode.SOCKS5}:
        if not proxy_url:
            logger.warning("proxy_mode=%r set but no proxy_url configured — using direct.", mode)
            return None
        logger.debug("Using proxy: %s", proxy_url)
        return proxy_url
    # ProxyMode.NONE or VPN_CHECK_ONLY (direct connection)
    return None


def build_httpx_proxies(proxy_url: Optional[str]) -> Optional[dict[str, str]]:
    """Build the ``proxies`` dict for httpx from a single proxy URL.

    Returns ``None`` when no proxy is needed.
    """
    if not proxy_url:
        return None
    return {"http://": proxy_url, "https://": proxy_url}
