"""Dogon bot runtime runner for Mansa_ETF allocation."""

from __future__ import annotations

import json
import importlib
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, cast

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from dotenv import load_dotenv

try:
    from scripts.bot_mlflow_benchmark import log_bot_benchmark_run
except ModuleNotFoundError:
    from bot_mlflow_benchmark import log_bot_benchmark_run

try:
    import xgboost as xgb

    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    keras = importlib.import_module("tensorflow.keras")
    TENSORFLOW_AVAILABLE = True
except ImportError:
    keras = None
    TENSORFLOW_AVAILABLE = False


logger = logging.getLogger(__name__)
load_dotenv()


class DogonRuntimeError(RuntimeError):
    """Raised when Dogon runtime prerequisites are missing."""


def _parse_symbols(raw_symbols: str) -> List[str]:
    return [
        symbol.strip().upper()
        for symbol in raw_symbols.split(",")
        if symbol.strip()
    ]


def _compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gains = delta.clip(lower=0).rolling(period).mean()
    losses = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gains / losses
    return 100 - (100 / (1 + rs))


def _load_training_summary(path: Path) -> Dict[str, object]:
    if not path.exists():
        raise DogonRuntimeError(
            f"Training summary missing at {path}. "
            "Run scripts/train_dogon_models.py first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _fetch_prices(symbols: List[str], days: int = 90) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for symbol in symbols:
        data = yf.download(symbol, period=f"{days}d", progress=False)
        if data is None or data.empty:
            logger.warning("No data returned for %s", symbol)
            continue
        close_values = data["Close"]
        if isinstance(close_values, pd.DataFrame):
            close_values = cast(
                pd.Series,
                cast(pd.DataFrame, close_values).iloc[:, 0],
            )
        frames.append(close_values.to_frame(name=f"close_{symbol}"))

    if not frames:
        logger.warning("Yahoo data unavailable, trying Alpaca bars fallback")
        return _fetch_alpaca_prices(symbols, days)

    merged = pd.concat(frames, axis=1).dropna()
    merged.index = pd.to_datetime(merged.index)
    return merged


def _fetch_alpaca_prices(symbols: List[str], days: int) -> pd.DataFrame:
    api_key = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
    api_secret = (
        os.getenv("ALPACA_SECRET_KEY")
        or os.getenv("APCA_API_SECRET_KEY")
        or os.getenv("ALPACA_API_SECRET")
    )
    if not api_key or not api_secret:
        raise DogonRuntimeError(
            "No Alpaca credentials available for market-data fallback"
        )

    data_url = os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets")
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret,
    }

    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=max(days, 30) + 5)
    params = {
        "symbols": ",".join(symbols),
        "timeframe": "1Day",
        "start": start_dt.isoformat().replace("+00:00", "Z"),
        "end": end_dt.isoformat().replace("+00:00", "Z"),
        "adjustment": "raw",
        "limit": 10000,
        "feed": os.getenv("ALPACA_DATA_FEED", "iex"),
    }

    response = requests.get(
        f"{data_url.rstrip('/')}/v2/stocks/bars",
        headers=headers,
        params=params,
        timeout=20,
    )
    if response.status_code != 200:
        raise DogonRuntimeError(
            f"Alpaca bars request failed ({response.status_code}): "
            f"{response.text[:200]}"
        )

    payload = response.json()
    bars = payload.get("bars", {})
    frames: List[pd.DataFrame] = []
    for symbol in symbols:
        rows = bars.get(symbol, [])
        if not rows:
            continue
        frame = pd.DataFrame(rows)
        if frame.empty or "c" not in frame.columns or "t" not in frame.columns:
            continue
        frame["t"] = pd.to_datetime(frame["t"]).dt.tz_localize(None)
        close_frame = frame.set_index("t")[["c"]].rename(
            columns={"c": f"close_{symbol}"}
        )
        frames.append(close_frame)

    if not frames:
        raise DogonRuntimeError("No Alpaca bars returned for runtime fallback")

    merged = pd.concat(frames, axis=1).dropna().sort_index()
    if merged.empty:
        raise DogonRuntimeError("Alpaca fallback produced empty price frame")
    return merged


def _build_features(prices: pd.DataFrame, symbols: List[str]) -> pd.DataFrame:
    feature_parts: List[pd.DataFrame] = []
    for symbol in symbols:
        col_name = f"close_{symbol}"
        if col_name not in prices.columns:
            continue

        close = prices[col_name]
        if isinstance(close, pd.DataFrame):
            close = cast(
                pd.Series,
                cast(pd.DataFrame, close).iloc[:, 0],
            )

        part = pd.DataFrame(index=prices.index)
        part[f"{symbol}_ret_1"] = close.pct_change(1)
        part[f"{symbol}_ret_5"] = close.pct_change(5)
        part[f"{symbol}_ret_10"] = close.pct_change(10)
        part[f"{symbol}_vol_10"] = close.pct_change().rolling(10).std()
        part[f"{symbol}_rsi_14"] = _compute_rsi(close, period=14)
        feature_parts.append(part)

    if not feature_parts:
        raise DogonRuntimeError("No feature columns could be computed")

    features = pd.concat(feature_parts, axis=1).dropna()
    if features.empty:
        raise DogonRuntimeError("Insufficient feature rows for inference")
    return features


def _align_feature_vector(
    features: pd.DataFrame,
    model: object,
) -> pd.DataFrame:
    feature_names = getattr(model, "feature_names_in_", None)
    if feature_names is None:
        return features

    aligned = features.reindex(columns=list(feature_names), fill_value=0.0)
    missing_count = int((aligned.columns != list(feature_names)).sum())
    if missing_count:
        logger.warning(
            "Feature alignment applied with %s mismatches",
            missing_count,
        )
    return aligned


def _run_gbt_inference(
    gbt_model_path: Path,
    features: pd.DataFrame,
) -> Dict[str, object]:
    if not XGBOOST_AVAILABLE:
        raise DogonRuntimeError("xgboost is not installed for GBT inference")
    if not gbt_model_path.exists():
        raise DogonRuntimeError(f"GBT model not found at {gbt_model_path}")

    model = xgb.XGBClassifier()
    model.load_model(str(gbt_model_path))
    aligned = _align_feature_vector(features, model)
    latest = aligned.tail(1)

    probabilities = model.predict_proba(latest)[0]
    pred_class = int(np.argmax(probabilities))
    confidence = float(probabilities[pred_class])
    signal = "buy" if pred_class == 1 else "hold"

    return {
        "model_used": "gbt",
        "signal": signal,
        "predicted_class": pred_class,
        "confidence": confidence,
    }


def _run_sequence_inference(
    model_name: str,
    model_path: Path,
    features: pd.DataFrame,
    sequence_window: int,
) -> Optional[Dict[str, object]]:
    if not (TENSORFLOW_AVAILABLE and model_path.exists()):
        return None

    if len(features) < sequence_window:
        logger.warning(
            "Insufficient rows (%s) for %s sequence window %s",
            len(features),
            model_name,
            sequence_window,
        )
        return None

    if keras is None:
        return None
    model = keras.models.load_model(str(model_path), compile=False)
    window = features.tail(sequence_window).values
    payload = np.expand_dims(window, axis=0)
    probability = float(model.predict(payload, verbose=0).flatten()[0])
    pred_class = int(probability > 0.5)

    return {
        "model_used": model_name,
        "signal": "buy" if pred_class == 1 else "hold",
        "predicted_class": pred_class,
        "confidence": probability if pred_class == 1 else 1.0 - probability,
        "raw_probability": probability,
    }


def run_cycle() -> Dict[str, object]:
    """Execute one Dogon cycle with model-backed inference."""
    models_dir = Path(os.getenv("DOGON_MODELS_DIR", "models/dogon"))
    summary_path = models_dir / "dogon_training_summary.json"
    try:
        summary = _load_training_summary(summary_path)
    except DogonRuntimeError as exc:
        now_utc = datetime.now(timezone.utc).isoformat()
        result: Dict[str, object] = {
            "bot": "Dogon",
            "fund": "Mansa_ETF",
            "status": "not_ready",
            "timestamp": now_utc,
            "detail": str(exc),
            "next_step": (
                "Run scripts/train_dogon_models.py "
                "to generate models."
            ),
        }
        log_bot_benchmark_run(
            bot_name="Dogon",
            experiment_name="Dogon_Runtime_Benchmark",
            run_name="Dogon-runtime-not-ready",
            payload=result,
            strategy_label="ETF raw strategy",
            discipline_mode="raw_strategy",
            extra_params={
                "best_training_model": "missing",
            },
            extra_tags={"trade_status": str(result["status"])},
        )
        logger.warning("Dogon runtime not ready: %s", result)
        return result

    symbols = _parse_symbols(
        os.getenv("DOGON_ETF_SYMBOLS", "SPY,QQQ,IWM,DIA,XLK,XLF")
    )
    sequence_window = int(os.getenv("DOGON_SEQUENCE_WINDOW", "30"))

    prices = _fetch_prices(symbols, days=90)
    features = _build_features(prices, symbols)

    artifacts = summary.get("artifacts", {})
    if not isinstance(artifacts, dict):
        artifacts = {}
    best_model_name = str(summary.get("best_model", "gbt")).lower()

    inference: Optional[Dict[str, object]] = None
    if best_model_name == "gbt":
        inference = _run_gbt_inference(
            models_dir / "dogon_gbt_model.json",
            features,
        )
    elif best_model_name in {"lstm", "tcn"}:
        model_file = artifacts.get(f"{best_model_name}_model")
        if model_file:
            resolved_path = Path(model_file)
        else:
            resolved_path = (
                models_dir
                / f"dogon_{best_model_name}_model.keras"
            )
        inference = _run_sequence_inference(
            best_model_name,
            resolved_path,
            features,
            sequence_window,
        )

        if inference is None:
            inference = _run_gbt_inference(
                models_dir / "dogon_gbt_model.json",
                features,
            )

    if inference is None:
        inference = _run_gbt_inference(
            models_dir / "dogon_gbt_model.json",
            features,
        )

    confidence_raw = inference.get("confidence", 0.0)
    if isinstance(confidence_raw, (int, float, np.floating)):
        confidence_value = float(confidence_raw)
    else:
        confidence_value = 0.0

    now_utc = datetime.now(timezone.utc).isoformat()
    result = {
        "bot": "Dogon",
        "fund": "Mansa_ETF",
        "status": "ready",
        "timestamp": now_utc,
        "signal": str(inference["signal"]),
        "confidence": confidence_value,
        "model_used": str(inference["model_used"]),
        "best_training_model": best_model_name,
        "latest_feature_timestamp": str(features.index[-1]),
        "feature_rows": float(len(features)),
        "symbol_count": float(len(symbols)),
        "predicted_class": float(inference.get("predicted_class", 0)),
        "raw_probability": float(inference.get("raw_probability", 0.0) or 0.0),
        "detail": "Model-backed runtime inference completed.",
    }
    log_bot_benchmark_run(
        bot_name="Dogon",
        experiment_name="Dogon_Runtime_Benchmark",
        run_name=f"Dogon-{result['status']}-{result['model_used']}",
        payload=result,
        strategy_label="ETF raw strategy",
        discipline_mode="raw_strategy",
        extra_params={
            "best_training_model": best_model_name,
            "model_used": str(inference["model_used"]),
            "symbols": ",".join(symbols),
        },
        extra_tags={
            "trade_status": str(result["status"]),
        },
    )
    logger.info("Dogon cycle executed: %s", result)
    return result


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    result = run_cycle()
    print(result)


if __name__ == "__main__":
    main()
