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
from scripts.load_screener_csv import load_bot_trade_candidates
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


def _record_orchestration_event(
    bot: TitanBot,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    bot.log_orchestration_run(
        bot_name=str(payload.get("bot") or "Titan"),
        task_name=str(payload.get("task") or "execution"),
        fund_name=payload.get("fund"),
        status=str(payload.get("status") or "unknown"),
        decision_reason=payload.get("decision_reason"),
        candidates_considered=payload.get("candidates_considered"),
        candidates_executed=payload.get("candidates_executed"),
        traded_symbols=payload.get("traded_symbols") or [],
        detail=str(payload.get("detail") or ""),
    )
    return payload


def _run_titan_cycle(max_trades: int = 1) -> Dict[str, Any]:
    config = TitanConfig.from_env()
    bot = TitanBot(config)
    fund_name = BOT_FUND_ALLOCATIONS.get("Titan", "Mansa Tech")
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        bot.ensure_database_tables()
    except (RuntimeError, OSError, ValueError):
        logger.warning("Titan DB setup skipped during execution run")

    try:
        candidates = load_bot_trade_candidates(bot.config.active_bot_name)
        rank_candidates = getattr(bot, "rank_candidates", None)
        if callable(rank_candidates):
            candidates = rank_candidates(candidates)
        else:
            candidates = bot._rank_candidates(candidates)
    except Exception as exc:
        payload = {
            "timestamp": timestamp,
            "bot": "Titan",
            "fund": fund_name,
            "task": "execution",
            "status": "error",
            "detail": f"Candidate load failed: {exc}",
            "decision_reason": "candidate-load-failed",
            "candidates_considered": 0,
            "candidates_executed": 0,
            "traded_symbols": [],
        }
        _record_orchestration_event(bot, payload)
        _persist_snapshot("titan_orchestration_latest.json", payload)
        return payload

    selected_candidates = candidates
    selected_symbols = [
        str(candidate.get("symbol", "")).strip().upper()
        for candidate in selected_candidates
        if str(candidate.get("symbol", "")).strip()
    ]
    if not selected_symbols:
        payload = {
            "timestamp": timestamp,
            "bot": "Titan",
            "fund": fund_name,
            "task": "execution",
            "status": "no_candidates",
            "detail": "Titan screener returned no trade candidates",
            "decision_reason": "no-candidates",
            "candidates_considered": len(candidates),
            "candidates_executed": 0,
            "traded_symbols": [],
        }
        _record_orchestration_event(bot, payload)
        _persist_snapshot("titan_orchestration_latest.json", payload)
        return payload

    run_started_at = datetime.now(timezone.utc).replace(tzinfo=None)
    results = bot.execute_from_screener(max_trades=max_trades)
    recent_trades = bot.get_recent_trade_activity(
        since=run_started_at,
        symbols=selected_symbols,
        limit=max(25, len(selected_symbols) * 10),
    )

    latest_status = "completed"
    detail = "Titan cycle completed without a new trade log row"
    candidates_executed = 0
    traded_symbols = list(selected_symbols)
    if not recent_trades.empty:
        latest_row = recent_trades.iloc[0]
        latest_status = str(latest_row.get("status") or "completed")
        detail = str(latest_row.get("notes") or latest_status)
        candidates_executed = int(
            (recent_trades["status"] == "submitted").sum()
        )
        traded_symbols = [
            str(symbol).strip().upper()
            for symbol in recent_trades["symbol"].astype(str).tolist()
            if str(symbol).strip()
        ]
    elif results:
        if bot.config.dry_run or not bot.config.enable_trading:
            latest_status = "simulated"
            detail = "Titan cycle ran in dry-run mode"
        else:
            latest_status = "completed"
            detail = "Titan cycle ran but did not create a new trade log row"

    payload = {
        "timestamp": timestamp,
        "bot": "Titan",
        "fund": fund_name,
        "task": "execution",
        "status": latest_status,
        "detail": detail,
        "decision_reason": "scheduled-cycle",
        "candidates_considered": len(candidates),
        "candidates_executed": candidates_executed,
        "traded_symbols": traded_symbols,
        "results": results,
    }
    _record_orchestration_event(bot, payload)
    _persist_snapshot("titan_orchestration_latest.json", payload)
    return payload


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
            f"| symbol={result.get('training_symbol', 'n/a')} "
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
    decision = {
        "status": "approved" if allowed else "blocked",
        "reason": "liquidity-ok" if allowed else "liquidity-buffer-breached",
    }
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bot": "Titan",
        "fund": BOT_FUND_ALLOCATIONS.get("Titan", "Mansa Tech"),
        "task": "gate",
        "status": decision["status"],
        "decision_reason": decision["reason"],
        "detail": (
            "Titan liquidity gate approved orchestration"
            if allowed
            else "Titan liquidity gate blocked orchestration"
        ),
        "candidates_considered": 0,
        "candidates_executed": 0,
        "traded_symbols": [],
    }
    _record_orchestration_event(bot, payload)
    _persist_snapshot("titan_gate_latest.json", payload)
    return decision


def run_fund_bot(bot_name: str) -> Dict[str, Any]:
    """Execute or stage bot run. Returns dashboard-friendly status payload."""
    fund_name = BOT_FUND_ALLOCATIONS.get(bot_name, "Unmapped")
    script_path = SCRIPT_MAP.get(bot_name, "")

    if bot_name == "Titan":
        return _run_titan_cycle()

    if bot_name == "Orion":
        result = run_orion_cycle(days=180, log_mlflow=True)
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **result,
        }
        payload["discord"] = _notify_noomo(
            "Noomo | Orion minerals RSI cycle completed "
            f"| symbol={result.get('selected_symbol', 'n/a')} "
            f"| exec={result.get('execution', {}).get('status', 'n/a')} "
            f"| signal={result.get('signal', 'n/a')} "
            f"| rsi={float(result.get('rsi_value', 0.0)):.2f}"
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
