"""In-memory tier-based rate limiting for subscriber signal delivery/API pull.

Uses a simple fixed-window counter per subscriber. Institutional tier is
unlimited. Thread-safe via a module-level lock so it is safe to call from the
ThreadPoolExecutor-based delivery workers as well as FastAPI request handlers.
"""

from __future__ import annotations

import threading
import time
from typing import Dict

#: Requests allowed per rolling 60-second window, keyed by subscription tier.
#: ``None`` means unlimited.
TIER_LIMITS_PER_MINUTE: Dict[str, int | None] = {
    "basic": 10,
    "pro": 60,
    "institutional": None,
}

_WINDOW_SECONDS = 60.0


class RateLimitExceeded(Exception):
    """Raised when a subscriber exceeds their tier's request budget."""

    def __init__(self, subscriber_id: str, tier: str, limit: int, retry_after: float):
        super().__init__(
            f"Subscriber '{subscriber_id}' (tier={tier}) exceeded rate limit of "
            f"{limit}/min; retry after {retry_after:.1f}s"
        )
        self.subscriber_id = subscriber_id
        self.tier = tier
        self.limit = limit
        self.retry_after = retry_after


class RateLimiter:
    """Simple in-memory fixed-window rate limiter keyed by subscriber id."""

    def __init__(self, limits: Dict[str, int | None] | None = None, window_seconds: float = _WINDOW_SECONDS):
        self._limits = limits if limits is not None else TIER_LIMITS_PER_MINUTE
        self._window_seconds = window_seconds
        self._lock = threading.Lock()
        # subscriber_id -> (window_start_epoch, request_count)
        self._windows: Dict[str, tuple[float, int]] = {}

    def limit_for_tier(self, tier: str) -> int | None:
        return self._limits.get(str(tier).lower())

    def check(self, subscriber_id: str, tier: str) -> None:
        """Raise ``RateLimitExceeded`` if the subscriber is over budget.

        Otherwise records the request against the current window.
        """
        limit = self.limit_for_tier(tier)
        if limit is None:
            return  # institutional / unlimited

        now = time.monotonic()
        with self._lock:
            window_start, count = self._windows.get(subscriber_id, (now, 0))
            if now - window_start >= self._window_seconds:
                window_start, count = now, 0

            if count >= limit:
                retry_after = self._window_seconds - (now - window_start)
                raise RateLimitExceeded(subscriber_id, tier, limit, max(retry_after, 0.0))

            self._windows[subscriber_id] = (window_start, count + 1)

    def allow(self, subscriber_id: str, tier: str) -> bool:
        """Non-raising variant of :meth:`check`; returns ``True`` if allowed."""
        try:
            self.check(subscriber_id, tier)
            return True
        except RateLimitExceeded:
            return False


#: Shared process-wide limiter instance used by the delivery router and any
#: subscriber-facing API-pull endpoints.
DEFAULT_RATE_LIMITER = RateLimiter()
