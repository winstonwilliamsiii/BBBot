#!/usr/bin/env python3
"""Train Orion feed-forward neural network with RSI features and MLflow."""

from __future__ import annotations

import argparse
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

try:
    import mlflow
    import mlflow.sklearn
    from mlflow.exceptions import MlflowException
except ImportError:
    mlflow = None
    MlflowException = RuntimeError

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    from bbbot1_pipeline.mlflow_config import get_mlflow_tracking_uri
except ImportError:
    get_mlflow_tracking_uri = None


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models" / "orion"


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def _load_gold_data(days: int) -> pd.DataFrame:
    """Load GLD daily data from yfinance with synthetic fallback."""
    if yf is not None:
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - pd.Timedelta(days=max(days, 90))
        try:
            df = yf.download(
                "GLD",
                start=start_dt.date().isoformat(),
                end=end_dt.date().isoformat(),
                progress=False,
                auto_adjust=True,
            )
            if not df.empty and "Close" in df.columns:
                return df
        except (RuntimeError, ValueError, OSError, KeyError) as exc:
            logger.warning("GLD data download failed: %s", exc)

    rng = np.random.default_rng(23)
    periods = max(days, 240)
    idx = pd.date_range(end=datetime.now(), periods=periods, freq="D")
    drift = 0.04
    noise = rng.normal(loc=drift, scale=1.25, size=periods)
    close = 220 + np.cumsum(noise)
    high = close + np.abs(rng.normal(0.3, 0.1, size=periods))
    low = close - np.abs(rng.normal(0.3, 0.1, size=periods))
    volume = rng.integers(100_000, 600_000, size=periods)
    return pd.DataFrame(
        {
            "Close": close,
            "High": high,
            "Low": low,
            "Volume": volume,
        },
        index=idx,
    )


def _build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    close = pd.to_numeric(df["Close"], errors="coerce")
    if close.isna().all():
        raise ValueError("Close series contains no valid values")

    feat = pd.DataFrame(index=df.index)
    feat["close"] = close
    feat["ret_1d"] = close.pct_change(1)
    feat["ret_5d"] = close.pct_change(5)
    feat["vol_10d"] = feat["ret_1d"].rolling(10).std()
    feat["sma_10"] = close.rolling(10).mean()
    feat["sma_30"] = close.rolling(30).mean()
    feat["sma_ratio"] = feat["sma_10"] / feat["sma_30"]
    feat["rsi_14"] = _compute_rsi(close, period=14)
    feat["rsi_delta"] = feat["rsi_14"].diff()

    feat["target"] = (close.shift(-1) > close).astype(int)
    feat = feat.dropna().copy()

    if feat.empty:
        raise ValueError("No rows available after feature engineering")

    return feat


def _train_ffnn(
    feat: pd.DataFrame,
    hidden_layer_sizes: Tuple[int, int],
    max_iter: int,
) -> Tuple[
    MLPClassifier,
    StandardScaler,
    Dict[str, float],
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    features = [
        "ret_1d",
        "ret_5d",
        "vol_10d",
        "sma_ratio",
        "rsi_14",
        "rsi_delta",
    ]

    X = feat[features].to_numpy()
    y = feat["target"].to_numpy(dtype=int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = MLPClassifier(
        hidden_layer_sizes=hidden_layer_sizes,
        activation="relu",
        solver="adam",
        alpha=1e-4,
        batch_size=32,
        learning_rate="adaptive",
        max_iter=max_iter,
        random_state=42,
    )
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)

    metrics = {
        "train_samples": float(len(X_train)),
        "test_samples": float(len(X_test)),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
    }

    return model, scaler, metrics, X_test_scaled, y_test, y_pred


def _save_artifacts(
    model: MLPClassifier,
    scaler: StandardScaler,
) -> Dict[str, str]:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    model_path = MODELS_DIR / "orion_ffnn_model.pkl"
    scaler_path = MODELS_DIR / "orion_ffnn_scaler.pkl"

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    return {
        "model": str(model_path),
        "scaler": str(scaler_path),
    }


def run_training(
    days: int,
    max_iter: int,
    hidden_layer_sizes: Tuple[int, int],
) -> Dict[str, float | str]:
    data = _load_gold_data(days=days)
    feat = _build_feature_frame(data)
    model, scaler, metrics, _, _, _ = _train_ffnn(
        feat=feat,
        hidden_layer_sizes=hidden_layer_sizes,
        max_iter=max_iter,
    )
    artifact_paths = _save_artifacts(model=model, scaler=scaler)

    mlflow_logged = False
    run_id = ""

    if mlflow is not None:
        try:
            tracking_uri = (
                get_mlflow_tracking_uri()
                if get_mlflow_tracking_uri is not None
                else os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
            )
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment("Orion_FFNN_Gold_RSI")

            with mlflow.start_run(
                run_name=(
                    "orion_ffnn_"
                    f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
                )
            ) as run:
                run_id = run.info.run_id
                mlflow.log_param("bot", "Orion")
                mlflow.log_param("fund", "Mansa_Minerals")
                mlflow.log_param("strategy", "Gold_RSI_FFNN")
                mlflow.log_param("days", days)
                mlflow.log_param("max_iter", max_iter)
                mlflow.log_param(
                    "hidden_layer_sizes",
                    list(hidden_layer_sizes),
                )

                for key, value in metrics.items():
                    mlflow.log_metric(key, float(value))

                for artifact_name, artifact_path in artifact_paths.items():
                    if os.path.exists(artifact_path):
                        mlflow.log_artifact(
                            artifact_path,
                            artifact_path=artifact_name,
                        )

            mlflow_logged = True
        except (
            RuntimeError,
            ValueError,
            TypeError,
            OSError,
            MlflowException,
        ) as exc:
            logger.warning(
                "MLflow logging failed; training artifacts still saved: %s",
                exc,
            )

    return {
        "status": "trained",
        "mlflow_logged": str(mlflow_logged).lower(),
        "run_id": run_id,
        "accuracy": metrics["accuracy"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "model_path": artifact_paths["model"],
        "scaler_path": artifact_paths["scaler"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train Orion FFNN model with Gold RSI features"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Lookback days for training data",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=250,
        help="Max training iterations for MLP",
    )
    parser.add_argument(
        "--hidden-layer-sizes",
        type=int,
        nargs=2,
        default=[32, 16],
        metavar=("L1", "L2"),
        help="Two hidden layer sizes (default: 32 16)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    result = run_training(
        days=args.days,
        max_iter=args.max_iter,
        hidden_layer_sizes=(
            args.hidden_layer_sizes[0],
            args.hidden_layer_sizes[1],
        ),
    )
    logger.info("Orion FFNN training result: %s", result)
    print(result)


if __name__ == "__main__":
    main()
