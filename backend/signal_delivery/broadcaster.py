"""Real-time delivery engine: fan-out signals to premium subscribers.

Implements the ``DeliveryRouter`` used by the Cosmic Engine integration layer.
Supported delivery methods:

- ``webhook``   -- POST the full payload to ``subscriber.webhook_url`` via an
                   async ``httpx`` client, with retries + exponential backoff
                   and a dead-letter queue for exhausted retries.
- ``api``       -- placeholder; subscribers pull signals via the FastAPI
                   ``/signals/{bot_name}`` surface, so no push is required.
- ``websocket`` -- placeholder for a future streaming transport.
- ``email``     -- placeholder for a future email digest transport.

Delivery is always enqueued onto a background thread pool so it never blocks
Cosmic Engine execution.
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx

from .db import list_active_subscribers, record_dead_letter
from .rate_limiter import DEFAULT_RATE_LIMITER, RateLimitExceeded

logger = logging.getLogger("bentley.signal_delivery")

_MAX_ATTEMPTS = 3
_WEBHOOK_TIMEOUT_SECONDS = 8.0


class _WebhookDeliveryFailed(Exception):
    """Raised when all retry attempts for a webhook delivery are exhausted."""


class DeliveryRouter:
    """Determines how each subscriber receives signals and fans them out.

    Delivery never blocks the caller: :meth:`deliver` submits one task per
    active subscriber onto a bounded thread pool and returns immediately.
    """

    def __init__(self, max_workers: int = 4, rate_limiter=DEFAULT_RATE_LIMITER):
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="signal-delivery"
        )
        self._rate_limiter = rate_limiter

    # -- public API -------------------------------------------------
    def deliver(self, payload: dict[str, Any]) -> None:
        """Fan a stored signal payload out to all active subscribers.

        Non-blocking: work is queued on the background executor so this call
        never blocks Cosmic Engine execution.
        """
        for subscriber in list_active_subscribers():
            self._executor.submit(self._route, subscriber, payload)

    def shutdown(self, wait: bool = False) -> None:
        self._executor.shutdown(wait=wait)

    # -- routing ------------------------------------------------------
    def _route(self, subscriber: dict[str, Any], payload: dict[str, Any]) -> None:
        subscriber_id = str(subscriber.get("subscriber_id", "unknown"))
        tier = str(subscriber.get("tier", "basic"))
        try:
            self._rate_limiter.check(subscriber_id, tier)
        except RateLimitExceeded as exc:
            logger.warning("Skipping delivery to %s: %s", subscriber_id, exc)
            return

        method = str(subscriber.get("delivery_method", "")).lower()
        if method == "webhook":
            self._deliver_webhook(subscriber, payload)
        elif method == "api":
            logger.info(
                "Subscriber %s uses API-pull delivery; no push required", subscriber_id
            )
        elif method == "websocket":
            logger.info(
                "Websocket delivery for subscriber %s is not yet implemented (placeholder)",
                subscriber_id,
            )
        elif method == "email":
            logger.info(
                "Email delivery for subscriber %s is not yet implemented (placeholder)",
                subscriber_id,
            )
        else:
            logger.warning(
                "Unsupported delivery method '%s' for subscriber %s", method, subscriber_id
            )

    # -- webhook transport (async httpx) -------------------------------
    def _deliver_webhook(self, subscriber: dict[str, Any], payload: dict[str, Any]) -> None:
        subscriber_id = str(subscriber.get("subscriber_id", "unknown"))
        url = subscriber.get("webhook_url")
        if not url:
            logger.warning("Subscriber %s has no webhook_url configured", subscriber_id)
            return

        try:
            asyncio.run(_post_webhook_with_retry(subscriber_id, url, payload))
        except _WebhookDeliveryFailed as exc:
            record_dead_letter(
                subscriber_id=subscriber_id,
                delivery_method="webhook",
                payload=payload,
                error=str(exc),
                attempts=_MAX_ATTEMPTS,
            )
            logger.error(
                "Signal delivery permanently failed for subscriber %s webhook=%s "
                "after %s attempts; moved to dead-letter queue: %s",
                subscriber_id,
                url,
                _MAX_ATTEMPTS,
                exc,
            )


async def _post_webhook_with_retry(subscriber_id: str, url: str, payload: dict[str, Any]) -> None:
    """POST ``payload`` to ``url`` with retries and exponential backoff."""
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=_WEBHOOK_TIMEOUT_SECONDS) as client:
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                logger.info(
                    "Delivered signal to subscriber %s via webhook=%s (attempt %s)",
                    subscriber_id,
                    url,
                    attempt,
                )
                return
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt == _MAX_ATTEMPTS:
                    break
                backoff = 2 ** (attempt - 1)
                logger.warning(
                    "Webhook delivery attempt %s/%s failed for subscriber %s "
                    "webhook=%s: %s; retrying in %ss",
                    attempt,
                    _MAX_ATTEMPTS,
                    subscriber_id,
                    url,
                    exc,
                    backoff,
                )
                await asyncio.sleep(backoff)

    raise _WebhookDeliveryFailed(str(last_error))


#: Shared process-wide router instance used by the Cosmic Engine integration.
DEFAULT_ROUTER = DeliveryRouter()


def enqueue_signal_delivery(payload: dict[str, Any]) -> None:
    """Backwards-compatible functional entry point used by ``service.py``."""
    DEFAULT_ROUTER.deliver(payload)
