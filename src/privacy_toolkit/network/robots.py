"""robots.txt compliance checker with timeout protection."""

from __future__ import annotations

import urllib.robotparser
import urllib.request
from functools import lru_cache
from urllib.parse import urlparse

from privacy_toolkit.core.constants import DEFAULT_USER_AGENT
from privacy_toolkit.core.exceptions import RobotsDisallowedError
from privacy_toolkit.core.logging import get_logger

logger = get_logger(__name__)

_ROBOTS_TIMEOUT = 5  # seconds — never hang longer than this


@lru_cache(maxsize=128)
def _fetch_robots(robots_url: str, user_agent: str) -> urllib.robotparser.RobotFileParser:
    """Fetch and parse robots.txt (cached per URL, 5s timeout)."""
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        # Use urllib directly so we can enforce a timeout
        with urllib.request.urlopen(robots_url, timeout=_ROBOTS_TIMEOUT) as resp:
            rp.parse(resp.read().decode("utf-8", errors="replace").splitlines())
    except Exception as exc:
        logger.debug("robots.txt fetch failed for %s (%s) — assuming allowed.", robots_url, exc)
    return rp


def robots_url_for(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


def is_allowed(url: str, user_agent: str = DEFAULT_USER_AGENT) -> bool:
    """Return True if user_agent may fetch url per robots.txt.
    Defaults to allowed on any fetch error or timeout.
    """
    try:
        robots_url = robots_url_for(url)
        rp = _fetch_robots(robots_url, user_agent)
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True  # fail-open: never block on robots error


def check_allowed(url: str, user_agent: str = DEFAULT_USER_AGENT) -> None:
    if not is_allowed(url, user_agent):
        raise RobotsDisallowedError(url)


def clear_robots_cache() -> None:
    _fetch_robots.cache_clear()
