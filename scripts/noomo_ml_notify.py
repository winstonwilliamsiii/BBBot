from __future__ import annotations

import logging
import os
from typing import Mapping

import requests


logger = logging.getLogger(__name__)


def _resolve_noomo_webhook() -> str:
    return (
        os.getenv("DISCORD_WEBHOOK_NOOMO", "").strip()
        or os.getenv("DISCORD_AI_ML_WEBHOOK", "").strip()
        or os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        or os.getenv("DISCORD_WEBHOOK", "").strip()
        or os.getenv("DISCORD_WEBHOOK_PROD", "").strip()
    )


def notify_training_completion(
    bot_name: str,
    model_label: str,
    fields: Mapping[str, object],
    timeout: int = 8,
) -> bool:
    return notify_ml_event(
        bot_name=bot_name,
        event_label=f"{model_label} training completed",
        fields=fields,
        timeout=timeout,
    )


def notify_ml_event(
    bot_name: str,
    event_label: str,
    fields: Mapping[str, object],
    timeout: int = 8,
) -> bool:
    webhook_url = _resolve_noomo_webhook()
    if not webhook_url:
        return False

    message_parts = [f"Noomo | {bot_name} {event_label}"]
    for key, value in fields.items():
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        message_parts.append(f"{key}={text}")

    try:
        response = requests.post(
            webhook_url,
            json={"content": " | ".join(message_parts)},
            timeout=timeout,
        )
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.warning("Noomo training notification failed: %s", exc)
        return False
