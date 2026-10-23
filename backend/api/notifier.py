import hmac
import json
import logging
import os
from typing import Any, Optional

import requests
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from frontend.utils.webhook_router import get_webhook

logger = logging.getLogger(__name__)
router = APIRouter(tags=["notifications"])


class SignalNotification(BaseModel):
    bot_name: str
    symbol: str
    decision: str
    cosmic_score: Any = None
    mode: Optional[str] = None
    heads: Any = None


class TradingViewAlert(BaseModel):
    bot_name: str
    screenshot: Optional[str] = None
    message: Optional[str] = None
    secret: Optional[str] = None


def send_to_discord(webhook_url: str, payload: dict[str, Any]) -> None:
    """Deliver a Discord webhook payload or raise on delivery failure."""
    response = requests.post(webhook_url, json=payload, timeout=8)
    response.raise_for_status()


def _format_insights(insights: Any) -> str:
    if insights is None:
        return "N/A"
    if isinstance(insights, (dict, list)):
        return json.dumps(insights, ensure_ascii=False)
    return str(insights)


async def _deliver(webhook_url: str, payload: dict[str, Any]) -> None:
    try:
        await run_in_threadpool(send_to_discord, webhook_url, payload)
    except requests.RequestException as exc:
        logger.error("Discord webhook delivery failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="Discord webhook delivery failed",
        ) from exc


def _get_bot_webhook(bot_name: str) -> str:
    webhook_url = get_webhook(bot_name)
    if not webhook_url:
        logger.error("No Discord webhook configured for bot %s", bot_name)
        raise HTTPException(
            status_code=503,
            detail=f"No Discord webhook configured for bot {bot_name}",
        )
    return webhook_url


@router.post("/notify/signal")
async def notify_signal(notification: SignalNotification):
    """Route an EA or bot signal, including its Cosmic Score and ML insights."""
    webhook_url = _get_bot_webhook(notification.bot_name)
    insights = _format_insights(notification.heads)
    payload = {
        "content": f"**{notification.bot_name} Signal**",
        "embeds": [
            {
                "title": f"{notification.symbol} — {notification.decision}",
                "description": (
                    f"Cosmic Score: {notification.cosmic_score if notification.cosmic_score is not None else 'N/A'}\n"
                    f"Mode: {notification.mode or 'N/A'}\n"
                    f"ML Insights: {insights}"
                ),
                "color": 3447003,
            }
        ],
        "allowed_mentions": {"parse": []},
    }
    await _deliver(webhook_url, payload)
    return {"status": "ok"}


@router.post("/tv-alert")
async def tradingview_alert(
    alert: TradingViewAlert,
    tradingview_secret: Optional[str] = Header(
        default=None,
        alias="X-TradingView-Secret",
    ),
):
    """Authenticate and route TradingView alert messages and chart URLs."""
    configured_secret = os.getenv("TRADINGVIEW_WEBHOOK_SECRET", "").strip()
    if not configured_secret:
        raise HTTPException(
            status_code=503,
            detail="TradingView webhook authentication is not configured",
        )

    supplied_secret = (tradingview_secret or alert.secret or "").strip()
    if not supplied_secret or not hmac.compare_digest(
        supplied_secret,
        configured_secret,
    ):
        raise HTTPException(status_code=401, detail="Invalid TradingView secret")

    webhook_url = _get_bot_webhook(alert.bot_name)
    content = f"**{alert.bot_name} Chart Update**"
    if alert.message:
        content += f"\n{alert.message}"

    payload: dict[str, Any] = {
        "content": content,
        "allowed_mentions": {"parse": []},
    }
    if alert.screenshot:
        payload["embeds"] = [{"image": {"url": alert.screenshot}}]

    await _deliver(webhook_url, payload)
    return {"status": "ok"}
