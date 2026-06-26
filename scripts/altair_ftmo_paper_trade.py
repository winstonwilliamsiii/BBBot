"""
Altair FTMO Paper Trade — Mansa AI Fund
========================================
Runs Altair Bot news-trading signal analysis and executes a paper trade on FTMO.
Posts ML analysis results to Discord and updates Bentley Dashboard.

Usage:
    python scripts/altair_ftmo_paper_trade.py              # analyze + paper trade
    python scripts/altair_ftmo_paper_trade.py --dry-run    # signal only, no trade
    python scripts/altair_ftmo_paper_trade.py --symbol NVDA # specific ticker
    python scripts/altair_ftmo_paper_trade.py --headlines "AI boom" "Strong earnings"
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv(override=True)

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from altair_bot import AltairBot, AltairConfig  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("altair_ftmo_paper")

# ── Constants ─────────────────────────────────────────────────────────────────
DEFAULT_SYMBOL = None
DEFAULT_ACTION = "BUY"
DEFAULT_VOLUME = 100  # shares for paper trading
DEFAULT_BROKER = "auto"
FUND_NAME = "Mansa AI Fund"
STRATEGY_NAME = "News Trading"

# Default news headlines for demonstration
DEFAULT_NEWS_HEADLINES = [
    "AI infrastructure demand stays strong after enterprise upgrade cycle",
    "Analysts highlight durable data center growth for leading AI names",
    "Enterprise AI spending continues to accelerate amid competition",
]

# ── Discord helpers ────────────────────────────────────────────────────────────


def _get_bot_talk_webhook() -> Optional[str]:
    """Get Discord webhook for bot trade notifications."""
    return (
        os.getenv("DISCORD_BOT_TALK_WEBHOOK", "").strip()
        or os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        or os.getenv("DISCORD_WEBHOOK", "").strip()
        or os.getenv("DISCORD_WEBHOOK_PROD", "").strip()
        or None
    )


def _get_noomo_webhook() -> Optional[str]:
    """Get Discord webhook for AI/ML analysis notifications."""
    return (
        os.getenv("DISCORD_WEBHOOK_NOOMO", "").strip()
        or os.getenv("DISCORD_AI_ML_WEBHOOK", "").strip()
        or None
    )


def _discord_post(webhook_url: str, payload: dict) -> bool:
    """Post message to Discord webhook."""
    try:
        r = requests.post(webhook_url, json=payload, timeout=8)
        r.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Discord post failed: %s", exc)
        return False


def notify_ml_analysis(
    bot: AltairBot,
    analysis: dict[str, Any],
    dry_run: bool = False,
) -> None:
    """Post Altair ML analysis results to #ai-ml Discord thread."""
    webhook = _get_noomo_webhook()
    if not webhook:
        logger.warning("DISCORD_WEBHOOK_NOOMO not set — skipping ai/ml notification")
        return

    mode_tag = "🧪 DRY RUN" if dry_run else "🟢 LIVE"
    ticker = analysis.get("ticker", "N/A")
    action = analysis.get("action", "HOLD")
    composite_score = analysis.get("composite_score", 0.0)
    sentiment_score = analysis.get("sentiment", {}).get("score", 0.0)
    volume_score = analysis.get("screener", {}).get("volume_score", 0.0)
    valuation_score = analysis.get("screener", {}).get("valuation_score", 0.0)

    # Build embed for Discord
    embed = {
        "title": f"{mode_tag} Altair News Trading Signal",
        "color": 0x00FF00 if action == "BUY" else 0xFF0000 if action == "SELL" else 0xFFFF00,
        "fields": [
            {"name": "Ticker", "value": ticker, "inline": True},
            {"name": "Action", "value": action, "inline": True},
            {"name": "Composite Score", "value": f"{composite_score:.4f}", "inline": True},
            {"name": "Sentiment Score", "value": f"{sentiment_score:.4f}", "inline": True},
            {"name": "Volume Score", "value": f"{volume_score:.4f}", "inline": True},
            {"name": "Valuation Score", "value": f"{valuation_score:.4f}", "inline": True},
            {"name": "Fund", "value": analysis.get("fund", "N/A"), "inline": True},
            {"name": "Strategy", "value": analysis.get("strategy", "N/A"), "inline": True},
            {
                "name": "MLflow Experiment",
                "value": analysis.get("data_pipeline", {}).get("mlflow_experiment", "N/A"),
                "inline": True,
            },
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    payload = {"embeds": [embed]}
    _discord_post(webhook, payload)
    logger.info("✅ ML analysis posted to Discord")


def notify_trade_execution(
    ticker: str,
    action: str,
    qty: float,
    status: str,
    order_id: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """Post trade execution result to #bot_talk Discord channel."""
    webhook = _get_bot_talk_webhook()
    if not webhook:
        logger.warning("DISCORD_BOT_TALK_WEBHOOK not set — skipping trade notification")
        return

    mode_tag = "🧪 DRY RUN" if dry_run else "🔴 LIVE"
    status_emoji = (
        "✅" if status == "submitted" else "🟡" if status == "simulated" else "❌"
    )

    title = f"{status_emoji} {mode_tag} Altair Trade: {action} {qty} {ticker}"
    color = 0x00FF00 if action == "BUY" else 0xFF0000

    embed = {
        "title": title,
        "color": color,
        "fields": [
            {"name": "Symbol", "value": ticker, "inline": True},
            {"name": "Side", "value": action, "inline": True},
            {"name": "Quantity", "value": str(qty), "inline": True},
            {"name": "Status", "value": status, "inline": True},
            {"name": "Fund", "value": FUND_NAME, "inline": True},
            {"name": "Strategy", "value": STRATEGY_NAME, "inline": True},
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if order_id:
        embed["fields"].append({"name": "Order ID", "value": order_id, "inline": True})

    payload = {"embeds": [embed]}
    _discord_post(webhook, payload)
    logger.info(f"✅ Trade execution posted to Discord (Order: {order_id})")


# ── Main logic ─────────────────────────────────────────────────────────────────


def run_altair_paper_trade(
    symbol: Optional[str] = DEFAULT_SYMBOL,
    headlines: Optional[list[str]] = None,
    broker: str = DEFAULT_BROKER,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Execute Altair paper trade:
    1. Load Altair Bot configuration
    2. Run ML analysis on symbol with news headlines
    3. Execute paper trade if signal is BUY
    4. Post results to Discord and Bentley Dashboard
    """
    print("\n" + "=" * 80)
    print(f"🚀 ALTAIR PAPER TRADE EXECUTION")
    print("=" * 80 + "\n")

    # ────── LOAD CONFIGURATION ────────────────────────────────────────────────
    logger.info("📋 Loading Altair Bot configuration...")
    config = AltairConfig.from_env()
    bot = AltairBot(config)

    print(f"✅ Altair Bot loaded: {bot.config.name}")
    print(f"   Fund: {bot.config.fund}")
    print(f"   Strategy: {bot.config.strategy}")
    print(f"   Execution Mode: {bot.config.execution_mode}")
    print(f"   Trading Enabled: {bot.config.enable_trading}")

    # ────── RUN ML ANALYSIS ────────────────────────────────────────────────────
    if headlines is None:
        headlines = DEFAULT_NEWS_HEADLINES

    if symbol:
        target_tickers = [symbol.upper()]
    else:
        target_tickers = [str(t).upper() for t in bot.config.default_universe if str(t).strip()]

    if not target_tickers:
        raise ValueError("Altair universe is empty; provide --symbol explicitly")

    logger.info("🤖 Running ML analysis for tickers: %s", ", ".join(target_tickers))

    universe_analyses: list[dict[str, Any]] = []
    for ticker in target_tickers:
        universe_analyses.append(
            bot.analyze_ticker(
                ticker,
                headlines=headlines,
                log_to_mlflow=False,
            )
        )

    buy_signals = [a for a in universe_analyses if a.get("action") == "BUY"]
    analysis = (
        max(buy_signals, key=lambda a: float(a.get("composite_score", -999.0)))
        if buy_signals
        else max(universe_analyses, key=lambda a: float(a.get("composite_score", -999.0)))
    )
    symbol = str(analysis["ticker"]).upper()

    print("\n📌 Universe Scan (top first):")
    ranked = sorted(
        universe_analyses,
        key=lambda a: float(a.get("composite_score", -999.0)),
        reverse=True,
    )
    for row in ranked:
        print(
            f"   {row['ticker']}: score={row['composite_score']:.4f} action={row['action']}"
        )

    print(f"\n📊 Analysis Results:")
    print(f"   Ticker: {analysis['ticker']}")
    print(f"   Composite Score: {analysis['composite_score']:.4f}")
    print(f"   Sentiment Score: {analysis['sentiment']['score']:.4f}")
    print(f"   Action: {analysis['action']}")
    print(f"   Buy Threshold: {analysis['buy_threshold']}")
    print(f"   Sell Threshold: {analysis['sell_threshold']}")

    # ────── NOTIFY DISCORD - ML ANALYSIS ───────────────────────────────────────
    logger.info("📢 Posting ML analysis to Discord...")
    notify_ml_analysis(bot, analysis, dry_run=dry_run)

    # ────── EXECUTE TRADE (IF BUY SIGNAL) ──────────────────────────────────────
    trade_result = None
    if analysis["action"] == "BUY":
        logger.info(f"💹 Executing {analysis['action']} trade for {symbol}...")

        # Override dry_run based on environment if not explicitly disabled
        effective_dry_run = dry_run or not bot.config.enable_trading
        requested_broker = (
            str(broker or "").strip().lower()
            or str(os.getenv("ALTAIR_BROKER", "")).strip().lower()
            or str(getattr(bot.config, "primary_broker", "auto")).strip().lower()
            or DEFAULT_BROKER
        )
        trade_result = bot.execute_trade(
            broker=requested_broker,
            ticker=symbol,
            action=analysis["action"],
            qty=DEFAULT_VOLUME,
            dry_run=effective_dry_run,
        )

        print(f"\n✅ Trade Execution Result:")
        print(f"   Broker: {trade_result.get('broker')}")
        print(f"   Ticker: {trade_result.get('ticker')}")
        print(f"   Action: {trade_result.get('action')}")
        print(f"   Qty: {trade_result.get('qty')}")
        print(f"   Requested Broker: {requested_broker}")
        print(f"   Status: {trade_result.get('status')}")
        print(f"   Order ID: {trade_result.get('order_id', 'N/A')}")

        # ────── NOTIFY DISCORD - TRADE EXECUTION ──────────────────────────────
        logger.info("📢 Posting trade execution to Discord...")
        notify_trade_execution(
            ticker=symbol,
            action=analysis["action"],
            qty=DEFAULT_VOLUME,
            status=trade_result.get("status", "unknown"),
            order_id=trade_result.get("order_id"),
            dry_run=effective_dry_run,
        )
    else:
        logger.info(f"⏸️  No trade executed. Signal: {analysis['action']}")
        print(f"\n⏸️  Signal={analysis['action']} (BUY threshold={analysis['buy_threshold']}, "
              f"SELL threshold={analysis['sell_threshold']})")

    # ────── HEALTH SNAPSHOT ────────────────────────────────────────────────────
    logger.info("🏥 Collecting health snapshot...")
    health = bot.health_snapshot(probe_fastapi=False)

    print(f"\n🏥 System Health:")
    print(f"   FastAPI: {health.get('fastapi', {}).get('reachable', False)}")
    print(f"   MLflow: {health.get('mlflow', {}).get('reachable', False)}")
    print(f"   MySQL: {health.get('mysql', {}).get('reachable', False)}")
    print(f"   Discord: {health.get('discord', {}).get('configured', False)}")
    print(f"   Alpaca: {health.get('brokers', {}).get('alpaca', {}).get('ready', False)}")

    # ────── FINAL RESULT ───────────────────────────────────────────────────────
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bot": bot.config.name,
        "fund": bot.config.fund,
        "strategy": bot.config.strategy,
        "symbol": symbol,
        "analysis": analysis,
        "universe_analyses": universe_analyses,
        "trade": trade_result,
        "health": health,
        "dry_run": dry_run,
    }

    print("\n" + "=" * 80)
    print("✅ ALTAIR PAPER TRADE COMPLETE")
    print("=" * 80 + "\n")

    return result


# ── CLI ────────────────────────────────────────────────────────────────────────


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Altair FTMO Paper Trade — Mansa AI Fund",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default=DEFAULT_SYMBOL,
        help="Ticker symbol to analyze and trade (default: scan Altair configured universe)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run analysis only, skip trade execution",
    )
    parser.add_argument(
        "--headlines",
        nargs="*",
        default=None,
        help="Custom news headlines for sentiment analysis",
    )
    parser.add_argument(
        "--broker",
        type=str,
        default=DEFAULT_BROKER,
        help="Broker route: auto|alpaca|ibkr|mt5|ftmo (default: auto)",
    )

    args = parser.parse_args()

    # Use custom headlines if provided, else default
    headlines = args.headlines if args.headlines else None

    result = run_altair_paper_trade(
        symbol=args.symbol.upper() if args.symbol else None,
        headlines=headlines,
        broker=args.broker,
        dry_run=args.dry_run,
    )

    print("\n📊 Full Result (JSON):")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
