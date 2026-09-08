"""Per-subscriber API key authentication and subscription-tier enforcement.

This module is intentionally separate from ``Main.py``'s existing ``auth()``
dependency (a single service-wide ``BENTLEY_SIGNAL_API_KEY``). It authenticates
individual premium subscribers (retail, SDK, external app, mobile, partner)
against the ``subscribers`` registry table and enforces their subscription
tier. It does not alter the existing service-key authentication behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .db import VALID_TIERS, get_subscriber_by_api_key


class SubscriberAuthError(Exception):
    """Raised when a subscriber cannot be authenticated or authorized."""

    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class Subscriber:
    """Authenticated subscriber record resolved from the registry."""

    subscriber_id: str
    email: str | None
    tier: str
    api_key: str
    delivery_method: str
    webhook_url: str | None
    status: str
    created_at: str

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Subscriber":
        return cls(
            subscriber_id=str(row["subscriber_id"]),
            email=row.get("email"),
            tier=str(row["tier"]).lower(),
            api_key=str(row["api_key"]),
            delivery_method=str(row["delivery_method"]).lower(),
            webhook_url=row.get("webhook_url"),
            status=str(row.get("status", "active")),
            created_at=str(row.get("created_at", "")),
        )

    @property
    def is_active(self) -> bool:
        return self.status == "active"


def authenticate_subscriber(api_key: str) -> Subscriber:
    """Validate an API key against the subscriber registry.

    Raises ``SubscriberAuthError`` (401/403) when the key is missing, unknown,
    inactive, or associated with an invalid tier. Returns the resolved
    ``Subscriber`` on success.
    """
    supplied_key = (api_key or "").strip()
    if not supplied_key:
        raise SubscriberAuthError("Missing subscriber API key", status_code=401)

    row = get_subscriber_by_api_key(supplied_key)
    if row is None:
        raise SubscriberAuthError("Invalid subscriber API key", status_code=401)

    subscriber = Subscriber.from_row(row)
    if not subscriber.is_active:
        raise SubscriberAuthError(
            f"Subscriber '{subscriber.subscriber_id}' is not active", status_code=403
        )
    if subscriber.tier not in VALID_TIERS:
        raise SubscriberAuthError(
            f"Subscriber '{subscriber.subscriber_id}' has an unsupported tier "
            f"'{subscriber.tier}'",
            status_code=403,
        )
    return subscriber


def enforce_tier(subscriber: Subscriber, allowed_tiers: tuple[str, ...]) -> None:
    """Raise ``SubscriberAuthError`` (403) if the subscriber's tier is not allowed."""
    if subscriber.tier not in allowed_tiers:
        raise SubscriberAuthError(
            f"Subscriber tier '{subscriber.tier}' does not have access to this "
            f"resource; requires one of {allowed_tiers}",
            status_code=403,
        )
