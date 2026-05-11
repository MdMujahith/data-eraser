"""Token-bucket rate limiter for outbound HTTP requests."""

from __future__ import annotations

import asyncio
import time
from collections import deque

from privacy_toolkit.core.exceptions import RateLimitError
from privacy_toolkit.core.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Sliding-window rate limiter.

    Args:
        max_calls: Maximum number of calls allowed per *period* seconds.
        period: Window size in seconds (default 60).
        fail_on_limit: Raise :class:`RateLimitError` instead of sleeping.
    """

    def __init__(
        self,
        max_calls: int = 10,
        period: float = 60.0,
        fail_on_limit: bool = False,
    ) -> None:
        self.max_calls = max_calls
        self.period = period
        self.fail_on_limit = fail_on_limit
        self._calls: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Block (or raise) until a call slot is available."""
        async with self._lock:
            now = time.monotonic()
            # Evict timestamps outside the current window
            while self._calls and now - self._calls[0] >= self.period:
                self._calls.popleft()

            if len(self._calls) >= self.max_calls:
                wait = self.period - (now - self._calls[0])
                if self.fail_on_limit:
                    raise RateLimitError(
                        f"Rate limit exceeded: {self.max_calls} calls / {self.period}s"
                    )
                logger.debug("Rate limit hit; sleeping %.2fs", wait)
                await asyncio.sleep(max(0.0, wait))

            self._calls.append(time.monotonic())

    # Sync shim for non-async callers
    def acquire_sync(self) -> None:
        """Synchronous acquire — spins with time.sleep."""
        now = time.monotonic()
        while self._calls and now - self._calls[0] >= self.period:
            self._calls.popleft()

        if len(self._calls) >= self.max_calls:
            wait = self.period - (now - self._calls[0])
            if self.fail_on_limit:
                raise RateLimitError(
                    f"Rate limit exceeded: {self.max_calls} calls / {self.period}s"
                )
            logger.debug("Rate limit hit (sync); sleeping %.2fs", wait)
            time.sleep(max(0.0, wait))

        self._calls.append(time.monotonic())
