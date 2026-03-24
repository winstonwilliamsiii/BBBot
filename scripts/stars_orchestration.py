"""Helpers for Titan-led orchestration of Titan/Rigel/Dogon/Orion."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests

from scripts.mansa_titan_bot import TitanBot, TitanConfig
from scripts.orion_bot import run_cycle as run_orion_cycle
from scripts.train_orion_ffnn import run_training as run_orion_training


logger = logging.getLogger(__name__)

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

BOT_FUND_ALLOCATIONS = {
    "Titan": "Mansa Tech",
    "Rigel": "Mansa FOREX",
    "Dogon": "Mansa ETF",
    "Orion": "Mansa Minerals",
}


SCRIPT_MAP = {
    "Titan": "#MANSA_FUND TITAN_BOT.py",
    "Rigel": "scripts/rigel_forex_bot.py",
    "Dogon": "scripts/dogon_bot.py",
    "Orion": "scripts/orion_bot.py",
}


def _persist_snapshot(file_name: str, payload: Dict[str, Any]) -> None:
    snapshot_path = LOG_DIR / file_name
    snapshot_path.write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )


def _get_noomo_webhook() -> str | None:
    return (
        os.getenv("DISCORD_WEBHOOK_NOOMO")
        or os.getenv("DISCORD_WEBHOOK_URL")
        or os.getenv("DISCORD_WEBHOOK")
        or os.getenv("DISCORD_WEBHOOK_PROD")
    )


def _notify_noomo(message: str) -> Dict[str, Any]:
    webhook_url = _get_noomo_webhook()
    if not webhook_url:
        return {"sent": False, "reason": "No Discord webhook configured"}

    try:
        response = requests.post(
            webhook_url,
            json={"content": message},
            timeout=8,
        )
        response.raise_for_status()
        return {"sent": True, "status_code": response.status_code}
    except requests.RequestException as exc:
        logger.warning("Noomo Discord notification failed: %s", exc)
        return {"sent": False, "reason": str(exc)}


def train_orion_for_refresh(
    days: int = 365,
    max_iter: int = 250,
    hidden_layer_sizes: tuple[int, int] = (32, 16),
    notify_discord: bool = True,
) -> Dict[str, Any]:
    """Train Orion FFNN and persist a dashboard-visible status snapshot."""
    result = run_orion_training(
        days=days,
        max_iter=max_iter,
        hidden_layer_sizes=hidden_layer_sizes,
    )
    payload: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bot": "Orion",
        "fund": "Mansa_Minerals",
        "task": "training",
        **result,
    }

    if notify_discord:
        payload["discord"] = _notify_noomo(
            "Noomo | Orion FFNN training completed "
            f"| run_id={result.get('run_id', 'n/a')} "
            f"| accuracy={float(result.get('accuracy', 0.0)):.4f}"
        )

    _persist_snapshot("orion_training_latest.json", payload)
    return payload


def evaluate_titan_gate(
    buffer_threshold: float | None = None,
) -> Dict[str, str]:
    """Evaluate Titan liquidity gate and return orchestration decision."""
    bot = TitanBot(TitanConfig.from_env())
    try:
        bot.ensure_database_tables()
    except (RuntimeError, OSError, ValueError):
        logger.warning("Titan DB setup skipped during gate evaluation")

    allowed = bot.titan_guard(buffer_threshold=buffer_threshold)
    if allowed:
        return {"status": "approved", "reason": "liquidity-ok"}
    return {"status": "blocked", "reason": "liquidity-buffer-breached"}


def run_fund_bot(bot_name: str) -> Dict[str, Any]:
    """Execute or stage bot run. Returns dashboard-friendly status payload."""
    fund_name = BOT_FUND_ALLOCATIONS.get(bot_name, "Unmapped")
    script_path = SCRIPT_MAP.get(bot_name, "")

    if bot_name == "Orion":
        result = run_orion_cycle(days=180, log_mlflow=True)
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **result,
        }
        payload["discord"] = _notify_noomo(
            "Noomo | Orion Gold RSI cycle completed "
            f"| signal={result.get('signal', 'n/a')} "
            f"| rsi={float(result.get('rsi_14', 0.0)):.2f}"
        )
        _persist_snapshot("orion_cycle_latest.json", payload)
        return payload

    if not script_path:
        return {
            "bot": bot_name,
            "fund": fund_name,
            "status": "missing",
            "detail": "No script mapping configured",
        }

    script_exists = Path(script_path).exists()
    if not script_exists:
        return {
            "bot": bot_name,
            "fund": fund_name,
            "status": "placeholder",
            "detail": f"Script not found: {script_path}",
        }

    return {
        "bot": bot_name,
        "fund": fund_name,
        "status": "ready",
        "detail": f"Script available: {script_path}",
    }


def summarize_bot_runs(bot_names: List[str]) -> List[Dict[str, str]]:
    """Run all requested bots (staged) and return status summary."""
    return [run_fund_bot(bot_name) for bot_name in bot_names]
