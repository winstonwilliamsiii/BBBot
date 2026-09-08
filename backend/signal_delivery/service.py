"""Signal publication workflow shared by Airflow and the API."""

from __future__ import annotations

from typing import Any

from .broadcaster import enqueue_signal_delivery
from .db import store_signal


def publish_signal(result: dict[str, Any]) -> dict[str, Any]:
    """Store one engine result and asynchronously fan it out to subscribers."""
    payload = {
        "bot": result["bot_name"],
        "symbol": result["symbol"],
        "cosmic_score": result["cosmic_score"],
        "decision": result["decision"],
        "heads": result.get("heads", []),
        "mode": result.get("mode", "paper"),
        "metadata": {
            "extra_fields": result.get("extra_fields", []),
            "bot_meta": result.get("bot_meta", {}),
        },
    }
    if result.get("timestamp"):
        payload["timestamp"] = result["timestamp"]
    stored = store_signal(payload)
    enqueue_signal_delivery(stored)
    return stored
