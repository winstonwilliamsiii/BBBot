"""
Unified Discord Notifier — Bentley Budget Bot
==============================================
Rich-embed Discord notifications in the Procryon format for ALL bots.
Covers:
  • Signal events  (per-head + Cosmic Score)
  • Trade events   (paper & live, success & failure)

All public functions are fire-and-forget — they never raise so that a Discord
failure can never break a live trade path.

Webhook resolution order (same as Procryon):
  DISCORD_BOT_TALK_WEBHOOK  →  DISCORD_WEBHOOK_URL  →  DISCORD_WEBHOOK
  →  DISCORD_WEBHOOK_PROD

Signal embeds also go to DISCORD_WEBHOOK_NOOMO (ai/ml channel) when set.

Environment variables
---------------------
DISCORD_BOT_TALK_WEBHOOK   Trade execution channel
DISCORD_WEBHOOK_NOOMO      AI / ML signals channel
DISCORD_WEBHOOK_URL        Fallback general webhook
DISCORD_WEBHOOK            Fallback #2
DISCORD_WEBHOOK_PROD       Fallback #3
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("bentley.discord")

# ─── Colour palette ───────────────────────────────────────────────────────────
COLOR_BUY     = 3066993    # green   #2ECC71
COLOR_SELL    = 15158332   # red     #E74C3C
COLOR_HOLD    = 10181046   # purple  #9B59B6
COLOR_ERROR   = 15105570   # orange  #E67E22
COLOR_PAPER   = 3447003    # blue    #3498DB
COLOR_INFO    = 5592575    # teal    #55BFFF

# Cosmic symbol map
_DECISION_COLORS = {
    "BUY":  COLOR_BUY,
    "SELL": COLOR_SELL,
    "HOLD": COLOR_HOLD,
}
_COSMIC_LABELS = {
    "BUY":  "🔥 starfire",
    "SELL": "🌑 eclipse",
    "HOLD": "⚖️  cosmic balance",
}


# ─── Webhook helpers ──────────────────────────────────────────────────────────

def _bot_talk_webhook() -> Optional[str]:
    return (
        os.getenv("DISCORD_BOT_TALK_WEBHOOK", "").strip()
        or os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        or os.getenv("DISCORD_WEBHOOK", "").strip()
        or os.getenv("DISCORD_WEBHOOK_PROD", "").strip()
        or None
    )


def _noomo_webhook() -> Optional[str]:
    return (
        os.getenv("DISCORD_WEBHOOK_NOOMO", "").strip()
        or os.getenv("DISCORD_AI_ML_WEBHOOK", "").strip()
        or os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        or None
    )


def _post(webhook_url: str, payload: dict) -> bool:
    try:
        r = requests.post(webhook_url, json=payload, timeout=8)
        r.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Discord post failed: %s", exc)
        return False


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _mode_tag(mode: str) -> str:
    return "🔴 LIVE" if str(mode).lower() == "live" else "📄 PAPER"


# ─── Signal notification (Cosmic Score format) ────────────────────────────────

def notify_signal(
    bot_name: str,
    symbol: str,
    decision: str,              # BUY | SELL | HOLD
    cosmic_score: float,        # -1 … +1
    heads: Optional[List[Dict[str, Any]]] = None,
    mode: str = "paper",
    extra_fields: Optional[List[dict]] = None,
) -> None:
    """Fire-and-forget signal notification.

    Posted to:
    • ``DISCORD_WEBHOOK_NOOMO``   (ai/ml channel)
    • ``DISCORD_BOT_TALK_WEBHOOK`` (bot_talk channel) when decision ≠ HOLD
    """
    decision = decision.upper()
    color = _DECISION_COLORS.get(decision, COLOR_INFO)
    cosmic_label = _COSMIC_LABELS.get(decision, decision)

    bar_width = 12
    filled = round((cosmic_score + 1) / 2 * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)

    description = (
        f"**Time:** {_now_utc()}\n"
        f"**Symbol:** `{symbol}` │ **Mode:** {_mode_tag(mode)}\n"
        f"**Cosmic Score:** `{cosmic_score:+.4f}`\n"
        f"```\n[{bar}] {cosmic_score:+.2f}\n```\n"
        f"**Decision:** {cosmic_label}"
    )

    fields: List[dict] = []

    # Analytic heads breakdown
    if heads:
        head_lines = "\n".join(
            f"`{h.get('head', '?'):20s}` {h.get('score', 0):+.3f} "
            f"× w={h.get('weight', 0):.2f} "
            f"→ `{h.get('score', 0) * h.get('weight', 0):+.4f}`"
            for h in heads
        )
        fields.append({
            "name": "🧠 Analytic Heads",
            "value": head_lines[:1024],
            "inline": False,
        })

    if extra_fields:
        fields.extend(extra_fields[:4])

    embed: dict = {
        "title": f"🤖 {bot_name} | Signal — {_mode_tag(mode)}",
        "description": description,
        "color": color,
        "fields": fields,
        "footer": {"text": f"{bot_name} Cosmic Signal Engine | Bentley Budget Bot"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    payload = {"embeds": [embed]}

    # ai/ml channel always receives signal
    if wh := _noomo_webhook():
        _post(wh, payload)

    # bot_talk only on actionable decisions
    if decision in ("BUY", "SELL"):
        if wh := _bot_talk_webhook():
            _post(wh, payload)


# ─── Trade notification (Procryon format) ────────────────────────────────────

def notify_trade(
    bot_name: str,
    symbol: str,
    side: str,                  # buy | sell
    qty: float,
    status: str,                # submitted | simulated | filled | failed | dry_run
    mode: str = "paper",
    ticket: Optional[str] = None,
    broker: str = "",
    order_type: str = "market",
    limit_price: Optional[float] = None,
    error: Optional[str] = None,
    probability: Optional[float] = None,
    cosmic_score: Optional[float] = None,
    fund_name: str = "",
) -> None:
    """Fire-and-forget trade notification in Procryon embed format.

    Posted to ``DISCORD_BOT_TALK_WEBHOOK``.
    """
    side_upper = side.upper()
    is_live = str(mode).lower() == "live"
    is_success = status.lower() in ("submitted", "filled", "simulated", "dry_run")
    is_error = status.lower() in ("failed", "error")
    is_paper = not is_live

    if is_live and is_error:
        color = COLOR_ERROR
    elif is_live and is_success:
        color = COLOR_BUY if side_upper == "BUY" else COLOR_SELL
    else:
        color = COLOR_PAPER

    ticket_line = f" │ Ticket: `{ticket}`" if ticket else ""
    broker_line  = f" via **{broker.upper()}**" if broker else ""
    price_line   = f" @ ${limit_price:.4f}" if limit_price else ""
    mode_tag     = _mode_tag(mode)

    if status.lower() == "dry_run":
        status_line = "⏩ Dry-run — signal only, no order sent"
    elif is_error:
        status_line = f"❌ FAILED: {error or 'unknown error'}"
    elif is_success and is_live:
        status_line = f"✅ Trade placed{ticket_line}"
    else:
        status_line = f"📄 Simulated{ticket_line}"

    description = (
        f"**{side_upper} {symbol}** — {qty} lot(s){broker_line}{price_line}\n"
        f"{status_line}"
    )
    if fund_name:
        description = f"**Fund:** {fund_name}\n" + description

    fields: List[dict] = []
    if probability is not None:
        fields.append({
            "name": "🎯 ML Probability",
            "value": f"{probability:.1%}",
            "inline": True,
        })
    if cosmic_score is not None:
        cs_label = _COSMIC_LABELS.get(
            "BUY" if cosmic_score > 0.20 else ("SELL" if cosmic_score < -0.20 else "HOLD"),
            "—",
        )
        fields.append({
            "name": "✨ Cosmic Score",
            "value": f"`{cosmic_score:+.4f}` {cs_label}",
            "inline": True,
        })

    embed: dict = {
        "title": f"🤖 {bot_name} | {side_upper} {symbol} [{mode_tag}]",
        "description": description,
        "color": color,
        "fields": fields,
        "footer": {
            "text": (
                f"{bot_name} {'LIVE' if is_live else 'PAPER'} Trade │ "
                f"{fund_name or 'Bentley Budget Bot'} │ {_now_utc()}"
            )
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if wh := _bot_talk_webhook():
        _post(wh, {"embeds": [embed]})


# ─── Generic bot-status notification ─────────────────────────────────────────

def notify_status(
    bot_name: str,
    message: str,
    mode: str = "paper",
    color: int = COLOR_INFO,
) -> None:
    """Send a plain status / info notification to bot_talk."""
    embed = {
        "title": f"ℹ️  {bot_name} — Status",
        "description": f"**Mode:** {_mode_tag(mode)}\n{message}",
        "color": color,
        "footer": {"text": f"{bot_name} | Bentley Budget Bot"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if wh := _bot_talk_webhook():
        _post(wh, {"embeds": [embed]})
