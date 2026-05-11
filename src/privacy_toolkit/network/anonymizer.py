"""Anonymizer facade: combines proxy config + route verification + client construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from privacy_toolkit.core.constants import ProxyMode
from privacy_toolkit.core.exceptions import ProxyVerificationError
from privacy_toolkit.core.logging import get_logger
from privacy_toolkit.network.client import NetworkClient, build_client_from_settings
from privacy_toolkit.network.verifier import RouteInfo, verify_current_route

logger = get_logger(__name__)

_ANONYMIZER_DISCLAIMER = (
    "\n⚠  PRIVACY NOTICE: This tool does NOT guarantee anonymity.\n"
    "   Route verification confirms proxy connectivity only.\n"
    "   Metadata, timing attacks, and browser fingerprinting are out of scope.\n"
)


@dataclass
class AnonymizerStatus:
    """Combined anonymizer state returned to callers."""

    route: Optional[RouteInfo]
    client: NetworkClient
    verified: bool
    message: str


def prepare_anonymized_client(
    fail_closed: bool = True,
    print_disclaimer: bool = True,
) -> AnonymizerStatus:
    """Build a :class:`NetworkClient` after optional route verification.

    Args:
        fail_closed: Abort with :class:`ProxyVerificationError` if proxy
            cannot be confirmed when ``privacy_verify_enabled=True``.
        print_disclaimer: Print anonymity disclaimer to stderr.

    Returns:
        :class:`AnonymizerStatus` with the configured client.

    Raises:
        :class:`ProxyVerificationError`: When fail_closed and verification fails.
    """
    from privacy_toolkit.config.settings import get_settings
    settings = get_settings()

    if print_disclaimer:
        import sys
        print(_ANONYMIZER_DISCLAIMER, file=sys.stderr)

    client = build_client_from_settings()
    route: Optional[RouteInfo] = None
    verified = False
    message = "Privacy verification disabled — direct connection."

    if settings.privacy_verify_enabled:
        try:
            route = verify_current_route(
                proxy_mode=settings.proxy_mode,
                proxy_url=settings.proxy_url,
                tor_host=settings.tor_socks_host,
                tor_port=settings.tor_socks_port,
                timeout=float(settings.request_timeout),
                fail_closed=fail_closed,
            )
            verified = True
            mode_label = settings.proxy_mode.upper()
            message = f"Route verified via {mode_label}. Public IP: [REDACTED]"
            if route.warning:
                message += f" | ⚠ {route.warning}"
        except ProxyVerificationError as exc:
            logger.error("Proxy verification failed (fail-closed): %s", exc)
            raise
    elif settings.proxy_mode != ProxyMode.NONE:
        message = f"Proxy mode: {settings.proxy_mode} (verification disabled)"

    return AnonymizerStatus(route=route, client=client, verified=verified, message=message)
