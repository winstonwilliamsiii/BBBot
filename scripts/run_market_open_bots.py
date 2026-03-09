"""Market-open launcher for Titan and Dogon bots.

Runs both bots with liquidity and dry-powder controls so morning automation
can remain risk-aware without manual intervention.
"""

from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from dotenv import load_dotenv

from scripts.dogon_bot import run_cycle as run_dogon_cycle
from scripts.mansa_titan_bot import TitanBot, TitanConfig

try:
    from alpaca_trade_api.rest import APIError
except ImportError:
    APIError = RuntimeError

logger = logging.getLogger(__name__)


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _as_int(value: str | None, default: int) -> int:
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _as_float(value: str | None, default: float) -> float:
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _compute_position_size(
    configured_size: float,
    cash: float,
    equity: float,
    liquidity_buffer: float,
    deploy_pct: float,
    min_trade_cash: float,
) -> Tuple[float, float]:
    reserve_target = max(0.0, equity * liquidity_buffer)
    deployable_cash = max(0.0, cash - reserve_target)
    budget = max(0.0, deployable_cash * max(0.0, min(1.0, deploy_pct)))

    if budget < min_trade_cash:
        return 0.0, deployable_cash

    return min(configured_size, budget), deployable_cash


def run_market_open_cycle() -> Dict[str, Any]:
    load_dotenv(override=False)

    config = TitanConfig.from_env()
    bot = TitanBot(config)

    max_trades = _as_int(os.getenv("TITAN_MAX_TRADES"), 1)
    deploy_pct = _as_float(os.getenv("TITAN_DRY_POWDER_DEPLOY_PCT"), 0.25)
    min_trade_cash = _as_float(os.getenv("TITAN_MIN_TRADE_CASH"), 50.0)
    assumed_notional = _as_float(
        os.getenv("TITAN_ASSUMED_TRADE_NOTIONAL"),
        1000.0,
    )
    scheduled_qty = _as_float(os.getenv("TITAN_SCHEDULED_QTY"), 1.0)

    # Respect explicit env flags, but still apply safety overrides below.
    env_enable_trading = _as_bool(os.getenv("TITAN_ENABLE_TRADING"), True)
    env_dry_run = _as_bool(os.getenv("TITAN_DRY_RUN"), False)
    config.enable_trading = env_enable_trading
    config.dry_run = env_dry_run

    try:
        bot.ensure_database_tables()
    except (RuntimeError, OSError, ValueError) as exc:
        logger.warning("Could not ensure Titan tables: %s", exc)

    snapshot = bot.get_account_snapshot()
    cash = float(snapshot.get("cash", 0.0))
    equity = float(snapshot.get("equity", 0.0))
    ratio = (cash / equity) if equity > 0 else 0.0

    safety_reason = None
    if equity <= 0 or cash <= 0:
        safety_reason = "no_account_equity_or_cash"
    elif ratio < config.liquidity_buffer_threshold:
        safety_reason = "liquidity_buffer_breached"

    position_size, deployable_cash = _compute_position_size(
        configured_size=float(config.position_size),
        cash=cash,
        equity=equity,
        liquidity_buffer=float(config.liquidity_buffer_threshold),
        deploy_pct=deploy_pct,
        min_trade_cash=min_trade_cash,
    )

    if safety_reason is not None or position_size <= 0.0:
        config.enable_trading = False
        config.dry_run = True
        if safety_reason is None:
            safety_reason = "insufficient_dry_powder"
    else:
        allowed_trades = int(
            math.floor(deployable_cash / max(assumed_notional, 1.0))
        )
        if allowed_trades <= 0:
            config.enable_trading = False
            config.dry_run = True
            safety_reason = "insufficient_dry_powder"
        else:
            max_trades = min(max_trades, allowed_trades)
            config.position_size = max(1.0, round(scheduled_qty, 4))

    titan_error = None
    try:
        titan_results = bot.execute_from_screener(max_trades=max_trades)
    except (APIError, RuntimeError, OSError, ValueError) as exc:
        titan_error = str(exc)
        logger.warning(
            "Titan execution failed, forcing dry-run fallback: %s",
            exc,
        )
        config.enable_trading = False
        config.dry_run = True
        titan_results = bot.execute_from_screener(max_trades=max_trades)

    dogon_result = run_dogon_cycle()

    summary: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "titan": {
            "enable_trading": config.enable_trading,
            "dry_run": config.dry_run,
            "liquidity_buffer_threshold": config.liquidity_buffer_threshold,
            "cash": cash,
            "equity": equity,
            "cash_to_equity_ratio": ratio,
            "deployable_cash": deployable_cash,
            "position_size": config.position_size,
            "max_trades": max_trades,
            "safety_reason": safety_reason,
            "error": titan_error,
            "results": titan_results,
        },
        "dogon": dogon_result,
    }

    return summary


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    result = run_market_open_cycle()
    print(json.dumps(result, default=str))


if __name__ == "__main__":
    main()
