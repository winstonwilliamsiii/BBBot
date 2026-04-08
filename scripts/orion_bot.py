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
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from config.broker_mode_config import get_config as get_broker_mode_config
except ModuleNotFoundError:
    get_broker_mode_config = None

try:
    from frontend.components.mt5_connector import MT5Connector
except ModuleNotFoundError:
    MT5Connector = None

try:
    from scripts.orion_settings import OrionSettings, load_orion_settings
except ModuleNotFoundError:
    from orion_settings import OrionSettings, load_orion_settings

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
load_dotenv(override=False)


def _normalize_close_frame(data: pd.DataFrame) -> pd.DataFrame:
    close_data: Any = None
    if isinstance(data.columns, pd.MultiIndex):
        if "Close" not in data.columns.get_level_values(0):
            raise ValueError("Downloaded data does not include Close column")
        close_data = data["Close"]
        if isinstance(close_data, pd.DataFrame):
            close_data = close_data.iloc[:, 0]
    elif "Close" in data.columns:
        close_data = data["Close"]
    else:
        raise ValueError("Downloaded data does not include Close column")

    close_series = pd.to_numeric(close_data, errors="coerce")
    if not isinstance(close_series, pd.Series):
        raise TypeError("Close payload is not a 1-D series")

    normalized = close_series.dropna()
    if normalized.empty:
        raise ValueError(
            "Downloaded Close series is empty after normalization"
        )
    return pd.DataFrame({"Close": normalized})


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


def _fetch_symbol_history(symbol: str, days: int) -> pd.DataFrame:
    """Fetch symbol history with deterministic synthetic fallback."""
    if yf is not None:
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - pd.Timedelta(days=max(days, 45))
        data = yf.download(
            symbol,
            start=start_dt.date().isoformat(),
            end=end_dt.date().isoformat(),
            progress=False,
            auto_adjust=True,
        )
        if not data.empty:
            try:
                return _normalize_close_frame(data)
            except (TypeError, ValueError) as exc:
                logger.warning(
                    (
                        "Discarding downloaded %s data due to "
                        "invalid close series: %s"
                    ),
                    symbol,
                    exc,
                )

    seed = 17 + sum(ord(char) for char in symbol)
    rng = np.random.default_rng(seed)
    periods = max(days, 60)
    idx = pd.date_range(end=datetime.now(), periods=periods, freq="D")
    base = 220.0
    shocks = rng.normal(loc=0.03, scale=1.2, size=periods)
    close = base + np.cumsum(shocks)
    return pd.DataFrame({"Close": close}, index=idx)


def _signal_from_rsi(
    rsi: float,
    oversold: float,
    overbought: float,
) -> str:
    if rsi < oversold:
        return "BUY"
    if rsi > overbought:
        return "SELL"
    return "HOLD"


def _score_signal(
    signal: str,
    rsi: float | None,
    oversold: float,
    overbought: float,
    primary_symbol: str,
    symbol: str,
) -> tuple[int, float, int]:
    if rsi is None:
        return (-1, float("-inf"), 0)
    if signal == "BUY":
        return (2, oversold - rsi, int(symbol == primary_symbol))
    if signal == "SELL":
        return (1, rsi - overbought, int(symbol == primary_symbol))
    neutral_gap = min(abs(rsi - oversold), abs(overbought - rsi))
    return (0, -neutral_gap, int(symbol == primary_symbol))


def _evaluate_symbol(
    symbol: str,
    settings: OrionSettings,
    days: int,
) -> Dict[str, Any]:
    prices = _fetch_symbol_history(symbol, days)
    close = pd.to_numeric(prices["Close"], errors="coerce").dropna()
    latest_price = float(close.iloc[-1]) if not close.empty else None
    rsi = _compute_rsi(close, period=settings.rsi_period)
    signal = (
        _signal_from_rsi(rsi, settings.rsi_oversold, settings.rsi_overbought)
        if rsi is not None
        else "HOLD"
    )
    score = _score_signal(
        signal,
        rsi,
        settings.rsi_oversold,
        settings.rsi_overbought,
        settings.primary_symbol,
        symbol,
    )
    return {
        "symbol": symbol,
        "signal": signal,
        "latest_price": latest_price,
        "rsi": rsi,
        "score": score,
        "status": "ready" if rsi is not None else "partial",
    }


def _get_effective_broker_mode(settings: OrionSettings) -> str:
    if get_broker_mode_config is None:
        return settings.execution_mode
    config = get_broker_mode_config()
    if config is None or not hasattr(config, "get_bot_mode"):
        return settings.execution_mode
    resolved_mode = config.get_bot_mode("Orion")
    if resolved_mode not in {"paper", "live"}:
        return settings.execution_mode
    return resolved_mode


def _resolve_execution_symbol(
    selected_symbol: str,
    settings: OrionSettings,
) -> str | None:
    mapped = settings.symbol_map.get(selected_symbol.upper())
    return mapped or None


def _build_risk_prices(
    side: str,
    current_price: float,
    settings: OrionSettings,
) -> tuple[float, float]:
    if side == "BUY":
        stop_loss = current_price * (1 - settings.stop_loss_pct)
        take_profit = current_price * (1 + settings.take_profit_pct)
    else:
        stop_loss = current_price * (1 + settings.stop_loss_pct)
        take_profit = current_price * (1 - settings.take_profit_pct)
    return round(stop_loss, 5), round(take_profit, 5)


def _position_side_from_type(position_type: str) -> str:
    return "long" if str(position_type).upper() == "BUY" else "short"


def _execute_broker_order(
    settings: OrionSettings,
    selected_symbol: str,
    signal: str,
) -> Dict[str, Any]:
    effective_mode = _get_effective_broker_mode(settings)
    if not settings.execution_enabled:
        return {
            "enabled": False,
            "attempted": False,
            "mode": effective_mode,
            "status": "disabled",
            "detail": "Orion execution disabled in YAML profile",
        }

    if signal not in {"BUY", "SELL"}:
        return {
            "enabled": True,
            "attempted": False,
            "mode": effective_mode,
            "status": "skipped",
            "detail": f"No broker order for neutral Orion signal: {signal}",
        }

    if settings.primary_client != "mt5_client":
        return {
            "enabled": True,
            "attempted": False,
            "mode": effective_mode,
            "status": "unsupported_broker",
            "detail": (
                "Orion broker execution currently supports mt5_client only"
            ),
        }

    execution_symbol = _resolve_execution_symbol(selected_symbol, settings)
    if not execution_symbol:
        return {
            "enabled": True,
            "attempted": False,
            "mode": effective_mode,
            "status": "unmapped_symbol",
            "detail": (
                "No MT5 execution symbol mapping configured for "
                f"{selected_symbol}"
            ),
        }

    if MT5Connector is None:
        return {
            "enabled": True,
            "attempted": False,
            "mode": effective_mode,
            "status": "connector_unavailable",
            "detail": (
                "MT5 connector module unavailable in current environment"
            ),
        }

    connector = MT5Connector(
        base_url=os.getenv("MT5_API_URL", "http://localhost:8000")
    )
    user = os.getenv("MT5_USER", "")
    password = os.getenv("MT5_PASSWORD", "")
    host = os.getenv("MT5_HOST", "")
    port = int(os.getenv("MT5_PORT", "443"))

    if not user or not password or not host:
        return {
            "enabled": True,
            "attempted": False,
            "mode": effective_mode,
            "status": "missing_credentials",
            "detail": (
                "MT5 credentials are incomplete in environment variables"
            ),
            "execution_symbol": execution_symbol,
        }

    if not connector.connect(
        user=user,
        password=password,
        host=host,
        port=port,
    ):
        return {
            "enabled": True,
            "attempted": True,
            "mode": effective_mode,
            "status": "connection_failed",
            "detail": connector.last_connect_error or "MT5 connect failed",
            "execution_symbol": execution_symbol,
        }

    try:
        desired_side = "long" if signal == "BUY" else "short"
        existing_position = None
        positions = connector.get_positions() or []
        for position in positions:
            if position.symbol == execution_symbol:
                existing_position = position
                break

        if existing_position is not None:
            existing_side = _position_side_from_type(existing_position.type)
            if existing_side == desired_side:
                return {
                    "enabled": True,
                    "attempted": False,
                    "mode": effective_mode,
                    "status": "position_exists",
                    "detail": (
                        f"Existing {existing_side} position already open on "
                        f"{execution_symbol}"
                    ),
                    "execution_symbol": execution_symbol,
                    "selected_symbol": selected_symbol,
                }

            if not settings.close_on_reverse:
                return {
                    "enabled": True,
                    "attempted": False,
                    "mode": effective_mode,
                    "status": "reverse_blocked",
                    "detail": (
                        f"Opposite position exists on {execution_symbol} and "
                        "close_on_reverse is disabled"
                    ),
                    "execution_symbol": execution_symbol,
                    "selected_symbol": selected_symbol,
                }

            closed = connector.close_position(existing_position.ticket)
            if not closed:
                return {
                    "enabled": True,
                    "attempted": True,
                    "mode": effective_mode,
                    "status": "close_failed",
                    "detail": (
                        "Failed to close opposite position on "
                        f"{execution_symbol}"
                    ),
                    "execution_symbol": execution_symbol,
                    "selected_symbol": selected_symbol,
                }

        symbol_info = connector.get_symbol_info(execution_symbol) or {}
        reference_price = float(
            symbol_info.get("ask")
            or symbol_info.get("bid")
            or symbol_info.get("price")
            or 0.0
        )
        stop_loss, take_profit = _build_risk_prices(
            side=signal,
            current_price=reference_price,
            settings=settings,
        )
        comment = (
            f"Orion {signal} {selected_symbol}->{execution_symbol} "
            f"mode={effective_mode}"
        )
        result = connector.place_trade(
            symbol=execution_symbol,
            order_type=signal,
            volume=settings.volume_lots,
            sl=stop_loss,
            tp=take_profit,
            comment=comment,
        )

        if not result:
            return {
                "enabled": True,
                "attempted": True,
                "mode": effective_mode,
                "status": "order_failed",
                "detail": (
                    "MT5 order returned no result for "
                    f"{execution_symbol}"
                ),
                "execution_symbol": execution_symbol,
                "selected_symbol": selected_symbol,
            }

        return {
            "enabled": True,
            "attempted": True,
            "mode": effective_mode,
            "status": "submitted",
            "detail": (
                f"Orion {signal} order submitted for {execution_symbol} "
                "via MT5"
            ),
            "selected_symbol": selected_symbol,
            "execution_symbol": execution_symbol,
            "volume_lots": settings.volume_lots,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "order_result": result,
        }
    finally:
        connector.disconnect()


def run_cycle(days: int = 120, log_mlflow: bool = True) -> Dict[str, Any]:
    """Execute one Orion cycle using YAML-driven minerals RSI scanning."""
    now_utc = datetime.now(timezone.utc).isoformat()
    settings = load_orion_settings()
    evaluations = [
        _evaluate_symbol(symbol, settings, days)
        for symbol in settings.scan_symbols
    ]
    ranked = sorted(
        evaluations,
        key=lambda item: item["score"],
        reverse=True,
    )
    selected = ranked[0] if ranked else {
        "symbol": settings.primary_symbol,
        "signal": "HOLD",
        "latest_price": None,
        "rsi": None,
        "status": "partial",
    }
    selected_symbol = str(selected["symbol"])
    signal = str(selected["signal"])
    latest_price = selected.get("latest_price")
    rsi = selected.get("rsi")
    execution = _execute_broker_order(settings, selected_symbol, signal)

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
                    f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
                )
            ):
                mlflow.log_param("bot", "Orion")
                mlflow.log_param("fund", "Mansa_Minerals")
                mlflow.log_param("strategy", settings.strategy_label)
                mlflow.log_param("lookback_days", days)
                mlflow.log_param("selected_symbol", selected_symbol)
                mlflow.log_param(
                    "execution_symbol",
                    execution.get("execution_symbol", ""),
                )
                mlflow.log_param(
                    "execution_status",
                    execution.get("status", ""),
                )
                mlflow.log_param("primary_symbol", settings.primary_symbol)
                mlflow.log_param("rsi_period", settings.rsi_period)
                mlflow.log_param("rsi_oversold", settings.rsi_oversold)
                mlflow.log_param("rsi_overbought", settings.rsi_overbought)
                mlflow.log_param(
                    "scan_symbols",
                    ",".join(settings.scan_symbols),
                )
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
        "strategy": settings.strategy_label,
        "primary_symbol": settings.primary_symbol,
        "selected_symbol": selected_symbol,
        "symbols_scanned": settings.scan_symbols,
        "scan_top_n": settings.scan_top_n,
        "signal": signal,
        "status": str(selected.get("status") or "partial"),
        "timestamp": now_utc,
        "detail": (
            "Minerals RSI basket evaluated; "
            "top symbol selected for Orion cycle."
        ),
        "latest_price": latest_price,
        "rsi_period": settings.rsi_period,
        "rsi_value": rsi,
        "rsi_oversold": settings.rsi_oversold,
        "rsi_overbought": settings.rsi_overbought,
        "scan_results": [
            {
                "symbol": item["symbol"],
                "signal": item["signal"],
                "latest_price": item["latest_price"],
                "rsi": item["rsi"],
            }
            for item in ranked[: settings.scan_top_n]
        ],
        "execution": execution,
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
