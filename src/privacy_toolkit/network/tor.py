"""Tor connectivity utilities.

This module provides helpers to:
- Check whether a Tor SOCKS proxy is reachable.
- Request a new Tor circuit (requires Tor ControlPort + cookie auth).

No Tor daemon management is performed — the user is responsible for running
the Tor Browser or standalone ``tor`` service.
"""

from __future__ import annotations

import socket
from typing import Optional

from privacy_toolkit.core.logging import get_logger

logger = get_logger(__name__)

_TOR_CHECK_URL = "https://check.torproject.org/api/ip"


def is_socks_reachable(host: str = "127.0.0.1", port: int = 9050, timeout: float = 5.0) -> bool:
    """Return ``True`` if a SOCKS5 listener is reachable at *host*:*port*."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_tor_proxy(
    host: str = "127.0.0.1",
    port: int = 9050,
    timeout: float = 10.0,
) -> tuple[bool, Optional[str]]:
    """Verify that the Tor proxy is reachable and confirm the exit IP.

    Returns:
        ``(is_tor, exit_ip_or_none)`` — ``is_tor`` is ``True`` when the
        ``check.torproject.org`` API confirms Tor usage.
    """
    if not is_socks_reachable(host, port):
        return False, None
    try:
        import httpx
        with httpx.Client(
            proxy=f"socks5://{host}:{port}",
            timeout=timeout,
        ) as client:
            resp = client.get(_TOR_CHECK_URL)
            resp.raise_for_status()
            data = resp.json()
            is_tor: bool = data.get("IsTor", False)
            ip: Optional[str] = data.get("IP")
            return is_tor, ip
    except Exception as exc:
        logger.debug("Tor check failed: %s", exc)
        return False, None


def request_new_circuit(
    control_port: int = 9051,
    host: str = "127.0.0.1",
    auth_password: Optional[str] = None,
) -> bool:
    """Send NEWNYM signal to Tor ControlPort to rotate the circuit.

    Args:
        control_port: Tor ControlPort (default 9051).
        host: Tor control host.
        auth_password: Tor control password if HashedControlPassword is set;
            leave ``None`` for CookieAuthentication (not supported here — use
            Stem for full control-port auth).

    Returns:
        ``True`` if NEWNYM was acknowledged.
    """
    try:
        with socket.create_connection((host, control_port), timeout=5.0) as sock:
            auth_line = (
                f'AUTHENTICATE "{auth_password}"\r\n'
                if auth_password
                else "AUTHENTICATE\r\n"
            )
            sock.sendall(auth_line.encode())
            resp = sock.recv(1024).decode()
            if not resp.startswith("250"):
                logger.warning("Tor auth failed: %s", resp.strip())
                return False
            sock.sendall(b"SIGNAL NEWNYM\r\n")
            resp2 = sock.recv(1024).decode()
            return resp2.startswith("250")
    except Exception as exc:
        logger.debug("Tor NEWNYM failed: %s", exc)
        return False
