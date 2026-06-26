"""Altair main launcher with broker abstraction, Discord hooks, dashboard health, and Optuna UI."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

import mlflow
import optuna

try:
    import gradio as gr
except Exception:  # pragma: no cover
    gr = None

try:
    from altair_bot import AltairBot, AltairConfig
except Exception:  # pragma: no cover
    from bots.altair_bot import AltairBot, AltairConfig

from frontend.components.mt5_connector import MT5Connector
from frontend.utils.discord_notify import notify_signal, notify_trade

logger = logging.getLogger("altair_main")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

DEFAULT_QTY = 100.0
DEFAULT_BROKER = "auto"


def _to_lines(raw: str) -> list[str]:
    return [line.strip() for line in str(raw or "").splitlines() if line.strip()]


def _ensure_mlflow(bot: AltairBot) -> None:
    mlflow.set_tracking_uri(bot.config.mlflow_tracking_uri)
    mlflow.set_experiment(bot.config.mlflow_experiment)


def _mt5_credentials_for(broker: str) -> dict[str, Any]:
    prefix = "FTMO" if broker.lower() == "ftmo" else "MT5"
    return {
        "api_url": os.getenv(f"{prefix}_MT5_API_URL")
        or os.getenv("MT5_API_URL")
        or "http://localhost:8002",
        "user": os.getenv(f"{prefix}_MT5_USER")
        or os.getenv("MT5_USER")
        or os.getenv("MT5_LOGIN")
        or "",
        "password": os.getenv(f"{prefix}_MT5_PASSWORD") or os.getenv("MT5_PASSWORD") or "",
        "host": os.getenv(f"{prefix}_MT5_SERVER")
        or os.getenv(f"{prefix}_MT5_HOST")
        or os.getenv("MT5_SERVER")
        or os.getenv("MT5_HOST")
        or "",
        "port": int(os.getenv(f"{prefix}_MT5_PORT") or os.getenv("MT5_PORT") or "443"),
    }


def _submit_mt5_trade(
    *,
    broker: str,
    ticker: str,
    action: str,
    qty: float,
    dry_run: bool,
    mode: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "broker": broker,
        "ticker": ticker,
        "action": action,
        "qty": float(qty),
        "mode": mode,
        "attempted_brokers": [broker],
    }

    if dry_run:
        result.update(
            {
                "status": "simulated",
                "reason": "Dry-run enabled or trading disabled",
            }
        )
        return result

    creds = _mt5_credentials_for(broker)
    missing = [k for k in ("user", "password", "host") if not str(creds.get(k) or "").strip()]
    if missing:
        raise RuntimeError(f"Missing {broker.upper()} MT5 credentials: {', '.join(missing)}")

    connector = MT5Connector(base_url=str(creds["api_url"]))
    connected = connector.connect(
        user=str(creds["user"]),
        password=str(creds["password"]),
        host=str(creds["host"]),
        port=int(creds["port"]),
    )
    if not connected:
        raise RuntimeError(f"{broker.upper()} MT5 connection failed")

    try:
        trade = connector.place_trade(
            symbol=ticker,
            order_type=action,
            volume=float(qty),
            comment=f"Altair {broker.upper()}",
        )
    finally:
        connector.disconnect()

    if not trade:
        raise RuntimeError(f"{broker.upper()} MT5 order rejected")

    result.update(
        {
            "status": "submitted",
            "order_id": str(trade.get("ticket") or trade.get("order") or ""),
            "raw_status": trade.get("status") or trade.get("result"),
            "raw": trade,
        }
    )
    return result


def execute_trade(
    bot: AltairBot,
    *,
    broker: str,
    ticker: str,
    action: str,
    qty: float,
    dry_run: bool,
) -> dict[str, Any]:
    selected = str(broker or DEFAULT_BROKER).strip().lower()
    if selected in {"mt5", "ftmo"}:
        return _submit_mt5_trade(
            broker=selected,
            ticker=ticker,
            action=action,
            qty=qty,
            dry_run=dry_run,
            mode=bot.config.execution_mode,
        )

    # Delegate Alpaca/IBKR/auto routing to AltairBot's native broker order logic.
    return bot.execute_trade(
        broker=selected or DEFAULT_BROKER,
        ticker=ticker,
        action=action,
        qty=qty,
        dry_run=dry_run,
    )


def _log_analysis_to_mlflow(bot: AltairBot, analysis: dict[str, Any], broker: str, qty: float, dry_run: bool) -> dict[str, Any]:
    try:
        _ensure_mlflow(bot)
        with mlflow.start_run(run_name=f"altair_analysis_{analysis['ticker'].lower()}") as run:
            mlflow.log_params(
                {
                    "ticker": analysis["ticker"],
                    "broker_requested": broker,
                    "qty": float(qty),
                    "dry_run": bool(dry_run),
                    "action": analysis["action"],
                    "fund": bot.config.fund,
                    "strategy": bot.config.strategy,
                }
            )
            mlflow.log_metrics(
                {
                    "composite_score": float(analysis["composite_score"]),
                    "sentiment_score": float(analysis["sentiment"]["score"]),
                    "volume_score": float(analysis["screener"]["volume_score"]),
                    "valuation_score": float(analysis["screener"]["valuation_score"]),
                    "quality_score": float(analysis["screener"]["quality_score"]),
                }
            )
            return {"logged": True, "run_id": run.info.run_id}
    except Exception as exc:  # pragma: no cover
        return {"logged": False, "error": str(exc)}


def _log_trade_to_mlflow(bot: AltairBot, trade: dict[str, Any]) -> dict[str, Any]:
    try:
        _ensure_mlflow(bot)
        with mlflow.start_run(run_name=f"altair_trade_{str(trade.get('ticker', 'na')).lower()}") as run:
            mlflow.log_params(
                {
                    "broker": str(trade.get("broker", "")),
                    "ticker": str(trade.get("ticker", "")),
                    "action": str(trade.get("action", "")),
                    "mode": str(trade.get("mode", bot.config.execution_mode)),
                    "status": str(trade.get("status", "")),
                }
            )
            mlflow.log_metrics(
                {
                    "qty": float(trade.get("qty", 0.0)),
                    "is_submitted": 1.0 if str(trade.get("status", "")).lower() in {"submitted", "filled"} else 0.0,
                    "is_simulated": 1.0 if str(trade.get("status", "")).lower() in {"simulated", "dry_run"} else 0.0,
                }
            )
            return {"logged": True, "run_id": run.info.run_id}
    except Exception as exc:  # pragma: no cover
        return {"logged": False, "error": str(exc)}


def _optuna_score(bot: AltairBot, max_depth: int, learning_rate: float, n_estimators: int, headlines: list[str]) -> float:
    symbols = [str(s).upper() for s in bot.config.default_universe[:5] if str(s).strip()]
    if not symbols:
        symbols = ["NVDA"]

    analyses = [bot.analyze_ticker(sym, headlines=headlines, log_to_mlflow=False) for sym in symbols]
    avg_composite = sum(float(a["composite_score"]) for a in analyses) / max(len(analyses), 1)

    # Light penalty to avoid extreme, unstable hyperparameters in this lightweight tuning scaffold.
    penalty = (abs(max_depth - 6) * 0.01) + (abs(n_estimators - 250) * 0.0003) + (abs(learning_rate - 0.08) * 0.2)
    score = float(avg_composite - penalty)
    return score


def run_optuna(bot: AltairBot, n_trials: int, headlines: list[str]) -> dict[str, Any]:
    _ensure_mlflow(bot)

    def objective(trial: optuna.Trial) -> float:
        max_depth = trial.suggest_int("max_depth", 3, 10)
        learning_rate = trial.suggest_float("learning_rate", 0.01, 0.3)
        n_estimators = trial.suggest_int("n_estimators", 100, 500)

        score = _optuna_score(
            bot,
            max_depth=max_depth,
            learning_rate=learning_rate,
            n_estimators=n_estimators,
            headlines=headlines,
        )

        with mlflow.start_run(run_name=f"altair_optuna_trial_{trial.number}", nested=True):
            mlflow.log_params(
                {
                    "trial_number": trial.number,
                    "max_depth": max_depth,
                    "learning_rate": learning_rate,
                    "n_estimators": n_estimators,
                }
            )
            mlflow.log_metric("score", float(score))

        return score

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=int(n_trials))

    return {
        "best_params": study.best_params,
        "best_score": float(study.best_value),
        "n_trials": int(n_trials),
    }


def run_analysis_and_trade(
    symbol: str,
    headlines: list[str],
    broker: str = DEFAULT_BROKER,
    qty: float = DEFAULT_QTY,
    dry_run: bool = True,
    run_optuna_tuning: bool = False,
    n_trials: int = 20,
) -> dict[str, Any]:
    config = AltairConfig.from_env()
    bot = AltairBot(config)

    analysis = bot.analyze_ticker(symbol, headlines=headlines, log_to_mlflow=False)
    analysis_mlflow = _log_analysis_to_mlflow(bot, analysis, broker=broker, qty=qty, dry_run=dry_run)

    notify_signal(
        bot_name=bot.config.name,
        symbol=str(analysis["ticker"]),
        decision=str(analysis["action"]),
        cosmic_score=float(analysis["composite_score"]),
        mode=bot.config.execution_mode,
        extra_fields=[
            {"name": "Fund", "value": str(analysis.get("fund", "N/A")), "inline": True},
            {"name": "Strategy", "value": str(analysis.get("strategy", "N/A")), "inline": True},
        ],
    )

    trade_result: Optional[dict[str, Any]] = None
    trade_mlflow: dict[str, Any] = {"logged": False, "reason": "no trade attempted"}

    if str(analysis.get("action", "")).upper() == "BUY":
        effective_dry_run = bool(dry_run or not bot.config.enable_trading)
        trade_result = execute_trade(
            bot,
            broker=broker,
            ticker=str(analysis["ticker"]),
            action="BUY",
            qty=float(qty),
            dry_run=effective_dry_run,
        )
        trade_mlflow = _log_trade_to_mlflow(bot, trade_result)

        notify_trade(
            bot_name=bot.config.name,
            symbol=str(analysis["ticker"]),
            side="BUY",
            qty=float(qty),
            status=str(trade_result.get("status", "unknown")),
            mode=bot.config.execution_mode,
            ticket=str(trade_result.get("order_id") or "") or None,
            broker=str(trade_result.get("broker", broker)),
            fund_name=bot.config.fund,
            cosmic_score=float(analysis["composite_score"]),
        )

    health = bot.health_snapshot(probe_fastapi=False)

    optuna_result = None
    if run_optuna_tuning:
        optuna_result = run_optuna(bot, n_trials=int(n_trials), headlines=headlines)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "analysis": analysis,
        "analysis_mlflow": analysis_mlflow,
        "trade": trade_result,
        "trade_mlflow": trade_mlflow,
        "health": health,
        "optuna": optuna_result,
    }


def _gradio_run(
    symbol: str,
    headlines_text: str,
    broker: str,
    qty: float,
    dry_run: bool,
    run_optuna_tuning: bool,
    n_trials: int,
) -> tuple[str, str, str, str]:
    headlines = _to_lines(headlines_text)
    result = run_analysis_and_trade(
        symbol=symbol.strip().upper(),
        headlines=headlines,
        broker=broker,
        qty=float(qty),
        dry_run=bool(dry_run),
        run_optuna_tuning=bool(run_optuna_tuning),
        n_trials=int(n_trials),
    )

    analysis_txt = json.dumps(result.get("analysis", {}), indent=2, default=str)
    trade_txt = json.dumps(result.get("trade", {}), indent=2, default=str)
    health_txt = json.dumps(result.get("health", {}), indent=2, default=str)
    optuna_txt = json.dumps(result.get("optuna", {"message": "Optuna not run"}), indent=2, default=str)
    return analysis_txt, trade_txt, health_txt, optuna_txt


def launch_gradio() -> Any:
    if gr is None:
        raise RuntimeError("gradio is not installed")

    return gr.Interface(
        fn=_gradio_run,
        inputs=[
            gr.Textbox(label="Symbol", value="NVDA"),
            gr.Textbox(
                label="Headlines (one per line)",
                value="AI demand accelerates\nAnalysts raise target",
                lines=6,
            ),
            gr.Dropdown(
                label="Broker",
                choices=["auto", "alpaca", "ibkr", "mt5", "ftmo"],
                value="auto",
            ),
            gr.Number(label="Quantity", value=DEFAULT_QTY),
            gr.Checkbox(label="Dry run", value=True),
            gr.Checkbox(label="Run Optuna tuning", value=False),
            gr.Slider(label="Optuna n_trials", minimum=5, maximum=100, step=1, value=20),
        ],
        outputs=[
            gr.Textbox(label="Analysis JSON", lines=16),
            gr.Textbox(label="Trade JSON", lines=12),
            gr.Textbox(label="Bentley Health Snapshot", lines=16),
            gr.Textbox(label="Optuna Best Params + Score", lines=12),
        ],
        title="Altair Main",
        description="Broker abstraction (Alpaca/IBKR/MT5/FTMO), Discord notifications, dashboard health, and Optuna surfaced in UI.",
    )


if __name__ == "__main__":
    app = launch_gradio()
    app.launch()
