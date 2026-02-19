"""Helpers for Titan-led orchestration of Titan/Rigel/Dogon/Orion."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

from frontend.utils.bot_fund_mapping import BOT_FUND_ALLOCATIONS
from scripts.mansa_titan_bot import TitanBot, TitanConfig


logger = logging.getLogger(__name__)


SCRIPT_MAP = {
    "Titan": "#MANSA_FUND TITAN_BOT.py",
    "Rigel": "scripts/rigel_forex_bot.py",
    "Dogon": "scripts/dogon_bot.py",
    "Orion": "scripts/orion_bot.py",
}


def evaluate_titan_gate(buffer_threshold: float | None = None) -> Dict[str, str]:
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


def run_fund_bot(bot_name: str) -> Dict[str, str]:
    """Execute or stage bot run. Returns dashboard-friendly status payload."""
    fund_name = BOT_FUND_ALLOCATIONS.get(bot_name, "Unmapped")
    script_path = SCRIPT_MAP.get(bot_name, "")

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
