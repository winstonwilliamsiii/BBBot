"""
Procryon FTMO Test Trade — 9:30 AM Scheduled Runner
====================================================
Waits until 09:30 (local time), fetches the latest MLflow Procryon training
run metrics, runs evaluate_opportunity, and if the signal is valid places a
micro test trade on FTMO via the local MT5 bridge.

Discord notifications:
  • DISCORD_WEBHOOK_NOOMO  → #ai-ml thread  (MLflow results + Procryon signal)
  • DISCORD_BOT_TALK_WEBHOOK → #bot_talk    (trade execution result)

Usage:
    python scripts/procryon_ftmo_test_trade.py           # waits for 09:30 today
    python scripts/procryon_ftmo_test_trade.py --now     # runs immediately (skip wait)
    python scripts/procryon_ftmo_test_trade.py --dry-run # signal only, no trade
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv(override=True)

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from procryon_bot import ProcryonBot, ProcryonConfig, MLFLOW_AVAILABLE  # noqa: E402

try:
    from bbbot1_pipeline.mlflow_config import get_mlflow_tracking_uri
except ImportError:
    get_mlflow_tracking_uri = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("procryon_ftmo_test")

# ── Constants ─────────────────────────────────────────────────────────────────
TRADE_TIME_HOUR = 9
TRADE_TIME_MINUTE = 30
DEFAULT_SYMBOL = "EURUSD"
DEFAULT_ACTION = "BUY"
DEFAULT_VOLUME = 0.01          # micro-lot — smallest possible test trade
BROKER = "ftmo"

# ── Discord helpers ────────────────────────────────────────────────────────────

def _get_bot_talk_webhook() -> Optional[str]:
    return (
        os.getenv("DISCORD_BOT_TALK_WEBHOOK", "").strip()
        or os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        or os.getenv("DISCORD_WEBHOOK", "").strip()
        or os.getenv("DISCORD_WEBHOOK_PROD", "").strip()
        or None
    )


def _get_noomo_webhook() -> Optional[str]:
    return (
        os.getenv("DISCORD_WEBHOOK_NOOMO", "").strip()
        or os.getenv("DISCORD_AI_ML_WEBHOOK", "").strip()
        or os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        or None
    )


def _discord_post(webhook_url: str, payload: dict) -> bool:
    try:
        r = requests.post(webhook_url, json=payload, timeout=8)
        r.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Discord post failed: %s", exc)
        return False


def notify_ai_ml(
    mlflow_status: dict,
    eval_result: dict,
    training_metrics: dict,
    dry_run: bool = False,
) -> None:
    """Post MLflow results + Procryon signal to #ai-ml / Noomo thread."""
    webhook = _get_noomo_webhook()
    if not webhook:
        logger.warning("DISCORD_WEBHOOK_NOOMO not set — skipping ai/ml notification")
        return

    mode_tag = "🧪 DRY RUN" if dry_run else "🔴 LIVE"
    execute = eval_result.get("execute", False)
    probability = eval_result.get("execution_probability", 0.0)
    cluster = eval_result.get("cluster")
    spread_bps = eval_result.get("average_spread_bps", 0.0)

    knn_acc = training_metrics.get("knn_train_accuracy", "N/A")
    fnn_acc = training_metrics.get("fnn_train_accuracy", "N/A")
    knn_samples = int(training_metrics.get("knn_samples", 0))
    fnn_samples = int(training_metrics.get("fnn_samples", 0))

    mlflow_uri = mlflow_status.get("tracking_uri", "unavailable")
    mlflow_exp_count = mlflow_status.get("experiment_count", "?")
    mlflow_reachable = mlflow_status.get("reachable", False)

    signal_color = 3066993 if execute else 15158332  # green / red
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    embed = {
        "title": f"🤖 Noomo | Procryon Signal — {mode_tag}",
        "description": (
            f"**Time:** {now_utc}\n"
            f"**Symbol:** {DEFAULT_SYMBOL}  |  **Action:** {DEFAULT_ACTION}\n"
            f"**Execute:** {'✅ YES' if execute else '❌ NO'}  "
            f"**Probability:** {probability:.1%}  "
            f"**Cluster:** {cluster}  "
            f"**Spread:** {spread_bps:.1f} bps"
        ),
        "color": signal_color,
        "fields": [
            {
                "name": "📊 MLflow",
                "value": (
                    f"Reachable: {'✅' if mlflow_reachable else '❌'}\n"
                    f"URI: `{mlflow_uri}`\n"
                    f"Experiments: {mlflow_exp_count}"
                ),
                "inline": True,
            },
            {
                "name": "🧠 Model Metrics",
                "value": (
                    f"KNN accuracy: {knn_acc if isinstance(knn_acc, str) else f'{knn_acc:.1%}'} "
                    f"({knn_samples} samples)\n"
                    f"FNN accuracy: {fnn_acc if isinstance(fnn_acc, str) else f'{fnn_acc:.1%}'} "
                    f"({fnn_samples} samples)"
                ),
                "inline": True,
            },
        ],
        "footer": {"text": "Procryon MT5 Spread Arbitrage | FTMO"},
    }

    _discord_post(webhook, {"embeds": [embed]})
    logger.info("ai/ml Discord notification sent")


def notify_bot_talk(
    trade_result: dict,
    eval_result: dict,
    dry_run: bool = False,
) -> None:
    """Post trade execution result to #bot_talk."""
    webhook = _get_bot_talk_webhook()
    if not webhook:
        logger.warning("DISCORD_BOT_TALK_WEBHOOK not set — skipping bot_talk notification")
        return

    success = trade_result.get("success", False)
    ticket = trade_result.get("ticket")
    error = trade_result.get("error", "")
    broker = trade_result.get("broker", BROKER).upper()
    symbol = trade_result.get("symbol", DEFAULT_SYMBOL)
    action = trade_result.get("action", DEFAULT_ACTION)
    volume = trade_result.get("volume", DEFAULT_VOLUME)
    probability = eval_result.get("execution_probability", 0.0)
    mode_tag = "DRY RUN" if dry_run else "LIVE"

    if dry_run:
        status_line = "⏩ Trade skipped (dry-run mode)"
        color = 10181046  # purple
    elif success:
        status_line = f"✅ Trade placed | Ticket: `{ticket}`"
        color = 3066993  # green
    else:
        status_line = f"❌ Trade FAILED: {error}"
        color = 15158332  # red

    embed = {
        "title": f"🤖 Procryon | {broker} Trade [{mode_tag}]",
        "description": (
            f"**{action} {symbol}** — {volume} lot(s)\n"
            f"{status_line}\n"
            f"Signal probability: {probability:.1%}"
        ),
        "color": color,
        "footer": {"text": f"Procryon MT5 | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"},
    }

    _discord_post(webhook, {"embeds": [embed]})
    logger.info("bot_talk Discord notification sent (success=%s)", success)


# ── MLflow latest run metrics ─────────────────────────────────────────────────

def _fetch_latest_mlflow_metrics(bot: ProcryonBot) -> dict[str, Any]:
    """Pull the most recent Procryon training run metrics from MLflow if available."""
    if not MLFLOW_AVAILABLE or get_mlflow_tracking_uri is None:
        return {}
    try:
        import mlflow
        from mlflow.tracking import MlflowClient
        uri = get_mlflow_tracking_uri()
        mlflow.set_tracking_uri(uri)
        client = MlflowClient()
        exp = client.get_experiment_by_name(bot.config.mlflow_experiment)
        if exp is None:
            return {}
        runs = client.search_runs(
            experiment_ids=[exp.experiment_id],
            order_by=["start_time DESC"],
            max_results=1,
        )
        if not runs:
            return {}
        run = runs[0]
        return {k: v for k, v in run.data.metrics.items()}
    except Exception as exc:  # noqa: BLE001
        logger.warning("MLflow metric fetch failed: %s", exc)
        return {}


# ── Wait until 09:30 ──────────────────────────────────────────────────────────

def _wait_until_930() -> None:
    now = datetime.now()
    target = now.replace(
        hour=TRADE_TIME_HOUR, minute=TRADE_TIME_MINUTE, second=0, microsecond=0
    )
    if now >= target:
        logger.info("Already past 09:30 — running immediately")
        return
    delta = (target - now).total_seconds()
    logger.info(
        "Waiting %.0f seconds until 09:30 (%s)...",
        delta,
        target.strftime("%H:%M:%S"),
    )
    time.sleep(delta)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Procryon FTMO test trade at 09:30")
    parser.add_argument("--now", action="store_true", help="Skip wait, run immediately")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
                        help="Evaluate signal but do not place trade")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--action", default=DEFAULT_ACTION, choices=["BUY", "SELL"])
    parser.add_argument("--volume", type=float, default=DEFAULT_VOLUME)
    args = parser.parse_args()

    logger.info("=== Procryon FTMO Test Trade Runner ===")
    logger.info("Mode: %s | Symbol: %s | Action: %s | Volume: %s",
                "DRY RUN" if args.dry_run else "LIVE",
                args.symbol, args.action, args.volume)

    # ── 1. Wait ───────────────────────────────────────────────────────────────
    if not args.now:
        _wait_until_930()
    else:
        logger.info("--now flag set: executing immediately")

    # ── 2. Init bot and train models ──────────────────────────────────────────
    config = ProcryonConfig.from_env()
    bot = ProcryonBot(config)
    training_metrics = bot.bootstrap_demo_models()
    logger.info("Models ready: KNN acc=%.1f%% FNN acc=%.1f%%",
                training_metrics.get("knn_train_accuracy", 0) * 100,
                training_metrics.get("fnn_train_accuracy", 0) * 100)

    # Attempt to overlay real MLflow metrics if available
    live_metrics = _fetch_latest_mlflow_metrics(bot)
    if live_metrics:
        logger.info("MLflow live metrics loaded: %s", live_metrics)
        training_metrics.update(live_metrics)

    # ── 3. MLflow status ──────────────────────────────────────────────────────
    mlflow_status = bot.check_mlflow()
    logger.info("MLflow reachable: %s", mlflow_status.get("reachable"))

    # ── 4. Build eval features from current metrics ───────────────────────────
    # Spread vector from training — use live metrics if available, else demo
    knn_acc = float(training_metrics.get("knn_train_accuracy", 0.85))
    fnn_acc = float(training_metrics.get("fnn_train_accuracy", 0.85))
    spread_vector = [0.0036, 0.0029, 0.0041]     # representative EURUSD spreads
    exec_features = [30, knn_acc, 6, 2, fnn_acc]  # RSI-like, accuracy, volume, time, fnn_acc

    eval_result = bot.evaluate_opportunity(spread_vector, exec_features)
    logger.info("Signal: execute=%s probability=%.3f cluster=%s",
                eval_result["execute"],
                eval_result["execution_probability"],
                eval_result["cluster"])

    print("\n=== SIGNAL ===")
    print(json.dumps(eval_result, indent=2))
    print()

    # ── 5. Notify ai/ml (Noomo) ───────────────────────────────────────────────
    notify_ai_ml(mlflow_status, eval_result, training_metrics, dry_run=args.dry_run)

    # ── 6. Place trade (or skip on dry-run / no signal) ───────────────────────
    trade_result: Dict[str, Any] = {}

    if args.dry_run:
        logger.info("DRY RUN — skipping trade placement")
        trade_result = {
            "success": False,
            "broker": BROKER,
            "symbol": args.symbol,
            "action": args.action,
            "volume": args.volume,
            "error": "dry-run mode",
        }
    elif not eval_result["execute"]:
        logger.info("Signal says NO EXECUTE — skipping trade")
        trade_result = {
            "success": False,
            "broker": BROKER,
            "symbol": args.symbol,
            "action": args.action,
            "volume": args.volume,
            "error": f"execute=False (probability={eval_result['execution_probability']:.3f})",
        }
    else:
        logger.info("Placing FTMO test trade: %s %s %.2f lots",
                    args.action, args.symbol, args.volume)
        trade_result = bot.place_trade(
            broker_name=BROKER,
            symbol=args.symbol,
            action=args.action,
            volume=args.volume,
            comment="Procryon-Test-9:30",
        )

    print("=== TRADE RESULT ===")
    print(json.dumps(trade_result, indent=2, default=str))
    print()

    # ── 7. Notify bot_talk ────────────────────────────────────────────────────
    notify_bot_talk(trade_result, eval_result, dry_run=args.dry_run)

    # ── 8. Log to MLflow if live trade succeeded ──────────────────────────────
    if not args.dry_run and trade_result.get("success"):
        log_payload = {
            **training_metrics,
            "trade_placed": 1.0,
            "execution_probability": eval_result["execution_probability"],
            "cluster": float(eval_result["cluster"]),
        }
        log_result = bot.log_training_run(log_payload)
        logger.info("MLflow trade log: %s", log_result)

    logger.info("=== Done ===")


if __name__ == "__main__":
    main()
