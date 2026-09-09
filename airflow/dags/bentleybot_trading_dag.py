"""Simulation-only ML trading pipeline.

This DAG deliberately does not import or invoke broker execution code. Its output is
limited to local artifacts, Airflow XComs, and an optional simulated report log.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator

from bbbot1_pipeline.trading_strategies import MeanReversionStrategy

logger = logging.getLogger(__name__)

DEFAULT_TICKERS = ("BTC-USD", "ETH-USD")
DEFAULT_QUANTITY = 0.01


def _simulation_enabled() -> bool:
    return os.getenv("TRADING_SIMULATION_MODE", "true").strip().lower() == "true"


def _require_simulation_mode() -> None:
    if not _simulation_enabled():
        raise RuntimeError(
            "This DAG is simulation-only. Set TRADING_SIMULATION_MODE=true to run it."
        )


def _work_dir() -> Path:
    path = Path(os.getenv("BENTLEY_TRADING_WORK_DIR", "/tmp/bentley_trading"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _tickers() -> tuple[str, ...]:
    configured = os.getenv("TRADING_TICKERS", ",".join(DEFAULT_TICKERS))
    tickers = tuple(ticker.strip().upper() for ticker in configured.split(",") if ticker.strip())
    if not tickers:
        raise ValueError("TRADING_TICKERS must include at least one ticker.")
    return tickers


def _xcom_push(context: dict[str, Any], key: str, value: Any) -> None:
    task_instance = context.get("task_instance")
    if task_instance is not None:
        task_instance.xcom_push(key=key, value=value)


def _xcom_pull(context: dict[str, Any], task_id: str, key: str) -> Any:
    task_instance = context.get("task_instance")
    if task_instance is None:
        return None
    return task_instance.xcom_pull(task_ids=task_id, key=key)


def fetch_market_data(**context: Any) -> dict[str, Any]:
    """Fetch and persist daily close prices for the configured simulation tickers."""
    _require_simulation_mode()
    logger.info("SIMULATION MODE: fetching market data for %s", ", ".join(_tickers()))

    import yfinance as yf

    frames: list[pd.DataFrame] = []
    for ticker in _tickers():
        history = yf.download(
            ticker,
            period="3mo",
            interval="1d",
            auto_adjust=True,
            progress=False,
        )
        if history.empty:
            raise ValueError(f"No market data returned for {ticker}.")
        close_column = "Close" if "Close" in history.columns else "close"
        if close_column not in history.columns:
            raise ValueError(f"Market data for {ticker} did not include a close price.")
        frame = history[[close_column]].rename(columns={close_column: "Close"}).copy()
        frame["ticker"] = ticker
        frame.index.name = "timestamp"
        frames.append(frame.reset_index())

    market_data = pd.concat(frames, ignore_index=True)
    output_path = _work_dir() / "market_data.csv"
    market_data.to_csv(output_path, index=False)
    result = {"path": str(output_path), "rows": len(market_data), "tickers": list(_tickers())}
    _xcom_push(context, "market_data", result)
    logger.info("Fetched %s market-data rows in SIMULATION MODE", result["rows"])
    return result


def generate_signals(**context: Any) -> dict[str, Any]:
    """Generate strategy signals from persisted simulation market data."""
    _require_simulation_mode()
    market_data = _xcom_pull(context, "fetch_market_data", "market_data")
    path = Path(market_data["path"]) if market_data else _work_dir() / "market_data.csv"
    data = pd.read_csv(path, parse_dates=["timestamp"])
    strategy = MeanReversionStrategy()
    signal_frames: list[pd.DataFrame] = []

    for ticker, ticker_data in data.groupby("ticker", sort=True):
        prices = ticker_data.set_index("timestamp")[["Close"]]
        signals = strategy.generate_signals(prices).reset_index()
        signals["ticker"] = ticker
        signal_frames.append(signals)

    signals = pd.concat(signal_frames, ignore_index=True)
    output_path = _work_dir() / "signals.csv"
    signals.to_csv(output_path, index=False)
    result = {"path": str(output_path), "signals": int((signals["signal"] != 0).sum())}
    _xcom_push(context, "signals", result)
    logger.info("Generated %s actionable signals in SIMULATION MODE", result["signals"])
    return result


def execute_trades(**context: Any) -> dict[str, Any]:
    """Record simulated trades for the latest strategy decision per ticker."""
    _require_simulation_mode()
    signal_data = _xcom_pull(context, "generate_signals", "signals")
    path = Path(signal_data["path"]) if signal_data else _work_dir() / "signals.csv"
    signals = pd.read_csv(path, parse_dates=["timestamp"])
    latest = signals.sort_values("timestamp").groupby("ticker", as_index=False).tail(1)
    action_map = {1: "BUY", -1: "SELL", 0: "HOLD"}
    trades = latest.loc[:, ["timestamp", "ticker", "price", "signal"]].copy()
    trades.rename(columns={"price": "close_price"}, inplace=True)
    trades["action"] = trades["signal"].map(action_map).fillna("HOLD")
    trades["quantity"] = DEFAULT_QUANTITY
    trades["status"] = "simulated"
    trades["execution_mode"] = "SIMULATION MODE"

    output_path = _work_dir() / "simulated_trades.csv"
    trades.to_csv(output_path, index=False)
    result = {"path": str(output_path), "trades": len(trades), "executed": 0}
    _xcom_push(context, "trades", result)
    logger.info(
        "SIMULATION MODE: recorded %s simulated trade decisions; real executions=0",
        result["trades"],
    )
    return result


def calculate_performance(**context: Any) -> dict[str, Any]:
    """Calculate simulation metrics and log them to the Airflow task log."""
    _require_simulation_mode()
    trade_data = _xcom_pull(context, "execute_trades", "trades")
    path = Path(trade_data["path"]) if trade_data else _work_dir() / "simulated_trades.csv"
    trades = pd.read_csv(path)
    metrics = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "SIMULATION MODE",
        "trade_decisions": int(len(trades)),
        "buy_signals": int((trades["action"] == "BUY").sum()),
        "sell_signals": int((trades["action"] == "SELL").sum()),
        "hold_signals": int((trades["action"] == "HOLD").sum()),
        "real_executions": 0,
    }
    output_path = _work_dir() / "performance_metrics.json"
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    metrics["path"] = str(output_path)
    _xcom_push(context, "performance", metrics)
    logger.info("SIMULATION MODE: performance metrics logged: %s", metrics)
    return metrics


def send_daily_report(**context: Any) -> dict[str, Any]:
    """Publish the simulation report to the Airflow log without external delivery."""
    _require_simulation_mode()
    performance = _xcom_pull(context, "calculate_performance", "performance")
    if performance is None:
        performance_path = _work_dir() / "performance_metrics.json"
        performance = json.loads(performance_path.read_text(encoding="utf-8"))

    report = {"status": "sent", "delivery": "Airflow task log", "metrics": performance}
    _xcom_push(context, "daily_report", report)
    logger.info("SIMULATION MODE: daily report sent to Airflow task log: %s", report)
    return report


default_args = {
    "owner": "bentleybot",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}

with DAG(
    dag_id="bentleybot_dag",
    description="Simulation-only ML trading pipeline",
    default_args=default_args,
    start_date=datetime(2024, 12, 1),
    schedule="@daily",
    catchup=False,
    tags=["trading", "ml", "simulation"],
) as dag:
    fetch_market_data_task = PythonOperator(
        task_id="fetch_market_data", python_callable=fetch_market_data
    )
    generate_signals_task = PythonOperator(
        task_id="generate_signals", python_callable=generate_signals
    )
    execute_trades_task = PythonOperator(
        task_id="execute_trades", python_callable=execute_trades
    )
    calculate_performance_task = PythonOperator(
        task_id="calculate_performance", python_callable=calculate_performance
    )
    send_daily_report_task = PythonOperator(
        task_id="send_daily_report", python_callable=send_daily_report
    )

    (
        fetch_market_data_task
        >> generate_signals_task
        >> execute_trades_task
        >> calculate_performance_task
        >> send_daily_report_task
    )
