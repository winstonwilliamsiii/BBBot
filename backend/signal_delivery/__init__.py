"""Persistent signal storage and premium-subscriber delivery services."""

from .broadcaster import DeliveryRouter, DEFAULT_ROUTER, enqueue_signal_delivery
from .db import (
    VALID_DELIVERY_METHODS,
    VALID_TIERS,
    fetch_latest_signal,
    get_subscriber_by_api_key,
    list_active_subscribers,
    list_dead_letters,
    record_dead_letter,
    register_subscriber,
    store_signal,
)
from .rate_limiter import DEFAULT_RATE_LIMITER, RateLimitExceeded, RateLimiter
from .service import publish_signal
from .subscriber_auth import Subscriber, SubscriberAuthError, authenticate_subscriber, enforce_tier

__all__ = [
    "publish_signal",
    "store_signal",
    "fetch_latest_signal",
    "register_subscriber",
    "list_active_subscribers",
    "get_subscriber_by_api_key",
    "record_dead_letter",
    "list_dead_letters",
    "VALID_TIERS",
    "VALID_DELIVERY_METHODS",
    "DeliveryRouter",
    "DEFAULT_ROUTER",
    "enqueue_signal_delivery",
    "RateLimiter",
    "RateLimitExceeded",
    "DEFAULT_RATE_LIMITER",
    "Subscriber",
    "SubscriberAuthError",
    "authenticate_subscriber",
    "enforce_tier",
]
