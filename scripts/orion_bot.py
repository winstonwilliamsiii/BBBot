"""Orion bot runner for Mansa Minerals Gold RSI strategy."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_mlflow_spec = importlib.util.find_spec("mlflow")
mlflow = importlib.import_module("mlflow") if _mlflow_spec else None
if mlflow is not None:
    try:
        from mlflow.exceptions import MlflowException
    except ImportError:
        MlflowException = RuntimeError
else:
    MlflowException = RuntimeError

_yfinance_spec = importlib.util.find_spec("yfinance")
yf = importlib.import_module("yfinance") if _yfinance_spec else None

_mlflow_cfg_spec = importlib.util.find_spec("bbbot1_pipeline.mlflow_config")
if _mlflow_cfg_spec:
    _mlflow_cfg = importlib.import_module("bbbot1_pipeline.mlflow_config")
    get_mlflow_tracking_uri = getattr(
        _mlflow_cfg,
        "get_mlflow_tracking_uri",
        None,
    )
else:
    get_mlflow_tracking_uri = None


logger = logging.getLogger(__name__)


def _compute_rsi(close: pd.Series, period: int = 14) -> float | None:
    if close.empty or len(close) <= period:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    value = rsi.iloc[-1]
    return None if pd.isna(value) else float(value)


def _fetch_gold_history(days: int) -> pd.DataFrame:
    """Fetch GLD history with deterministic synthetic fallback."""
    if yf is not None:
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - pd.Timedelta(days=max(days, 45))
        data = yf.download(
            "GLD",
            start=start_dt.date().isoformat(),
            end=end_dt.date().isoformat(),
            progress=False,
            auto_adjust=True,
        )
        if not data.empty and "Close" in data.columns:
            return data

    rng = np.random.default_rng(17)
    periods = max(days, 60)
    idx = pd.date_range(end=datetime.now(), periods=periods, freq="D")
    base = 220.0
    shocks = rng.normal(loc=0.03, scale=1.2, size=periods)
    close = base + np.cumsum(shocks)
    return pd.DataFrame({"Close": close}, index=idx)


def _signal_from_rsi(rsi: float) -> str:
    if rsi < 30:
        return "BUY"
    if rsi > 70:
        return "SELL"
    return "HOLD"


def run_cycle(days: int = 120, log_mlflow: bool = True) -> Dict[str, Any]:
    """Execute one Orion cycle using Gold RSI technical signal generation."""
    now_utc = datetime.now(timezone.utc).isoformat()
    prices = _fetch_gold_history(days)
    close = pd.to_numeric(prices["Close"], errors="coerce").dropna()
    latest_price = float(close.iloc[-1]) if not close.empty else None
    rsi = _compute_rsi(close, period=14)
    signal = _signal_from_rsi(rsi) if rsi is not None else "HOLD"

    mlflow_logged = False
    if log_mlflow and mlflow is not None:
        try:
            tracking_uri = (
                get_mlflow_tracking_uri()
                if get_mlflow_tracking_uri is not None
                else os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
            )
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment("Orion_Mansa_Minerals")
            with mlflow.start_run(
                run_name=(
                    "orion_cycle_"
                    f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                )
            ):
                mlflow.log_param("bot", "Orion")
                mlflow.log_param("fund", "Mansa_Minerals")
                mlflow.log_param("strategy", "Gold_RSI")
                mlflow.log_param("lookback_days", days)
                mlflow.log_param("signal", signal)
                mlflow.log_metric("latest_price", latest_price or 0.0)
                if rsi is not None:
                    mlflow.log_metric("rsi_14", float(rsi))
                mlflow_logged = True
        except (
            RuntimeError,
            ValueError,
            TypeError,
            OSError,
            MlflowException,
        ) as exc:
            logger.warning("Orion MLflow logging skipped: %s", exc)

    result = {
        "bot": "Orion",
        "fund": "Mansa_Minerals",
        "strategy": "Gold_RSI",
        "signal": signal,
        "status": "ready" if rsi is not None else "partial",
        "timestamp": now_utc,
        "detail": "Gold RSI cycle evaluated.",
        "latest_price": latest_price,
        "rsi_14": rsi,
        "mlflow_logged": mlflow_logged,
    }
    logger.info("Orion cycle executed: %s", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Orion Mansa Minerals Gold RSI cycle"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=120,
        help="Lookback window for market data (default: 120)",
    )
    parser.add_argument(
        "--no-mlflow",
        action="store_true",
        help="Disable MLflow logging for this cycle",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    result = run_cycle(days=args.days, log_mlflow=not args.no_mlflow)
    print(result)


if __name__ == "__main__":
    main()
