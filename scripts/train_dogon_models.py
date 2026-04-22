#!/usr/bin/env python3
"""Dogon ETF model training for GBT baseline + LSTM/TCN sequence models."""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import mlflow
import numpy as np
import pandas as pd
import requests
import yfinance as yf
from dotenv import load_dotenv
from sklearn.metrics import accuracy_score, f1_score

try:
    from scripts.noomo_ml_notify import notify_training_completion
except ImportError:
    from noomo_ml_notify import notify_training_completion

try:
    import xgboost as xgb

    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    from tensorflow.keras.callbacks import EarlyStopping
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
    from tensorflow.keras.models import Sequential

    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

try:
    from tcn import TCN

    TCN_AVAILABLE = True
except ImportError:
    TCN_AVAILABLE = False


logger = logging.getLogger(__name__)
load_dotenv()


@dataclass
class DogonTrainingConfig:
    symbols: List[str]
    days: int = 730
    sequence_window: int = 30
    min_accuracy: float = 0.53
    tracking_uri: str = os.getenv(
        "MLFLOW_TRACKING_URI",
        "http://localhost:5000",
    )
    experiment_name: str = os.getenv(
        "DOGON_MLFLOW_EXPERIMENT",
        "Dogon-ETF-Models",
    )


class DogonModelTrainer:
    def __init__(self, config: DogonTrainingConfig) -> None:
        self.config = config
        self.output_dir = Path("models") / "dogon"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fetch_data(self) -> pd.DataFrame:
        frames: List[pd.DataFrame] = []
        for symbol in self.config.symbols:
            data = yf.download(
                symbol,
                period=f"{self.config.days}d",
                progress=False,
            )
            if data is None or data.empty:
                logger.warning("No data returned for %s", symbol)
                continue
            close_values = data["Close"]
            if isinstance(close_values, pd.DataFrame):
                close_values = close_values.iloc[:, 0]
            close_col = close_values.to_frame(name=f"close_{symbol}")
            frames.append(close_col)

        if not frames:
            logger.warning(
                "Yahoo data unavailable for training; trying Alpaca fallback"
            )
            return self.fetch_data_from_alpaca()

        merged = pd.concat(frames, axis=1).dropna()
        merged.index = pd.to_datetime(merged.index)
        return merged

    def fetch_data_from_alpaca(self) -> pd.DataFrame:
        api_key = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
        api_secret = (
            os.getenv("ALPACA_SECRET_KEY")
            or os.getenv("APCA_API_SECRET_KEY")
            or os.getenv("ALPACA_API_SECRET")
        )
        if not api_key or not api_secret:
            raise RuntimeError(
                "No ETF price data available for Dogon training "
                "(Yahoo unavailable, Alpaca credentials missing)"
            )

        data_url = os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets")
        headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret,
        }

        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(days=max(self.config.days, 30) + 5)
        params = {
            "symbols": ",".join(self.config.symbols),
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
            raise RuntimeError(
                f"Alpaca bars request failed ({response.status_code}): "
                f"{response.text[:200]}"
            )

        payload = response.json()
        bars = payload.get("bars", {})
        frames: List[pd.DataFrame] = []
        for symbol in self.config.symbols:
            rows = bars.get(symbol, [])
            if not rows:
                logger.warning("No Alpaca bars returned for %s", symbol)
                continue
            frame = pd.DataFrame(rows)
            if (
                frame.empty
                or "c" not in frame.columns
                or "t" not in frame.columns
            ):
                continue
            frame["t"] = pd.to_datetime(frame["t"]).dt.tz_localize(None)
            close_col = frame.set_index("t")[["c"]].rename(
                columns={"c": f"close_{symbol}"}
            )
            frames.append(close_col)

        if not frames:
            raise RuntimeError(
                "No ETF price data available for Dogon training"
            )

        merged = pd.concat(frames, axis=1).dropna().sort_index()
        if merged.empty:
            raise RuntimeError(
                "Alpaca fallback produced empty training dataset"
            )
        return merged

    @staticmethod
    def _compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gains = delta.clip(lower=0).rolling(period).mean()
        losses = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gains / losses
        return 100 - (100 / (1 + rs))

    def build_features(
        self,
        prices: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        feature_parts: List[pd.DataFrame] = []
        for symbol in self.config.symbols:
            col_name = f"close_{symbol}"
            if col_name not in prices.columns:
                continue

            close = prices[col_name]
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            part = pd.DataFrame(index=prices.index)
            part[f"{symbol}_ret_1"] = close.pct_change(1)
            part[f"{symbol}_ret_5"] = close.pct_change(5)
            part[f"{symbol}_ret_10"] = close.pct_change(10)
            part[f"{symbol}_vol_10"] = close.pct_change().rolling(10).std()
            part[f"{symbol}_rsi_14"] = self._compute_rsi(close, period=14)
            feature_parts.append(part)

        if not feature_parts:
            raise RuntimeError("No feature columns could be computed")

        features = pd.concat(feature_parts, axis=1)
        benchmark_symbol = (
            "SPY" if "close_SPY" in prices.columns else self.config.symbols[0]
        )
        benchmark_col = f"close_{benchmark_symbol}"
        benchmark_close = prices[benchmark_col]
        if isinstance(benchmark_close, pd.DataFrame):
            benchmark_close = benchmark_close.iloc[:, 0]
        target = (benchmark_close.pct_change().shift(-1) > 0).astype(int)

        dataset = pd.concat(
            [features, target.rename("target")],
            axis=1,
        ).dropna()
        return dataset.drop(columns=["target"]), dataset["target"]

    @staticmethod
    def split_time_series(X: pd.DataFrame, y: pd.Series, ratio: float = 0.8):
        split_idx = int(len(X) * ratio)
        X_train = X.iloc[:split_idx].copy()
        X_test = X.iloc[split_idx:].copy()
        y_train = y.iloc[:split_idx].copy()
        y_test = y.iloc[split_idx:].copy()
        return X_train, X_test, y_train, y_test

    @staticmethod
    def build_sequences(X: pd.DataFrame, y: pd.Series, window: int):
        values = X.values
        labels = y.values
        X_seq: List[np.ndarray] = []
        y_seq: List[int] = []

        for i in range(window, len(values)):
            X_seq.append(values[i - window:i])
            y_seq.append(int(labels[i]))

        return np.array(X_seq), np.array(y_seq)

    def train_gbt(self, X_train: pd.DataFrame, y_train: pd.Series):
        if not XGBOOST_AVAILABLE:
            raise RuntimeError("xgboost is not installed")

        model = xgb.XGBClassifier(
            n_estimators=250,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            eval_metric="logloss",
        )
        model.fit(X_train, y_train)
        return model

    def train_lstm(self, X_seq_train: np.ndarray, y_seq_train: np.ndarray):
        if not TENSORFLOW_AVAILABLE:
            raise RuntimeError("tensorflow is not installed")

        model = Sequential(
            [
                Input(shape=(X_seq_train.shape[1], X_seq_train.shape[2])),
                LSTM(64, return_sequences=False),
                Dropout(0.2),
                Dense(32, activation="relu"),
                Dense(1, activation="sigmoid"),
            ]
        )
        model.compile(
            optimizer="adam",
            loss="binary_crossentropy",
            metrics=["accuracy"],
        )
        model.fit(
            X_seq_train,
            y_seq_train,
            epochs=20,
            batch_size=32,
            validation_split=0.2,
            verbose=0,
            callbacks=[
                EarlyStopping(
                    monitor="val_loss",
                    patience=4,
                    restore_best_weights=True,
                )
            ],
        )
        return model

    def train_tcn(self, X_seq_train: np.ndarray, y_seq_train: np.ndarray):
        if not (TENSORFLOW_AVAILABLE and TCN_AVAILABLE):
            raise RuntimeError("tensorflow and keras-tcn are required")

        model = Sequential(
            [
                Input(shape=(X_seq_train.shape[1], X_seq_train.shape[2])),
                TCN(32, return_sequences=False),
                Dense(32, activation="relu"),
                Dropout(0.2),
                Dense(1, activation="sigmoid"),
            ]
        )
        model.compile(
            optimizer="adam",
            loss="binary_crossentropy",
            metrics=["accuracy"],
        )
        model.fit(
            X_seq_train,
            y_seq_train,
            epochs=20,
            batch_size=32,
            validation_split=0.2,
            verbose=0,
            callbacks=[
                EarlyStopping(
                    monitor="val_loss",
                    patience=4,
                    restore_best_weights=True,
                )
            ],
        )
        return model

    @staticmethod
    def classification_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, float]:
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        }

    def run(self) -> Dict[str, object]:
        prices = self.fetch_data()
        X, y = self.build_features(prices)
        X_train, X_test, y_train, y_test = self.split_time_series(X, y)

        seq_window = min(
            self.config.sequence_window,
            max(5, len(X_train) // 4),
        )
        if TENSORFLOW_AVAILABLE:
            X_seq_train, y_seq_train = self.build_sequences(
                X_train,
                y_train,
                seq_window,
            )
            X_seq_test, y_seq_test = self.build_sequences(
                X_test,
                y_test,
                seq_window,
            )

            if len(X_seq_train) < 20 or len(X_seq_test) < 5:
                raise RuntimeError(
                    "Insufficient sequence samples for LSTM/TCN training"
                )
        else:
            X_seq_train = np.array([])
            y_seq_train = np.array([])
            X_seq_test = np.array([])
            y_seq_test = np.array([])

        mlflow.set_tracking_uri(self.config.tracking_uri)
        mlflow.set_experiment(self.config.experiment_name)

        results: Dict[str, Dict[str, float]] = {}
        artifacts: Dict[str, str] = {}
        run_id = "n/a"

        with mlflow.start_run(run_name="dogon_biweekly_training") as run:
            run_id = run.info.run_id
            mlflow.log_param("symbols", ",".join(self.config.symbols))
            mlflow.log_param("days", self.config.days)
            mlflow.log_param("sequence_window", seq_window)
            mlflow.log_param("min_accuracy", self.config.min_accuracy)

            if XGBOOST_AVAILABLE:
                gbt = self.train_gbt(X_train, y_train)
                gbt_preds = gbt.predict(X_test)
                gbt_metrics = self.classification_metrics(
                    y_test.values,
                    gbt_preds,
                )
                results["gbt"] = gbt_metrics
                gbt_path = self.output_dir / "dogon_gbt_model.json"
                gbt.save_model(str(gbt_path))
                artifacts["gbt_model"] = str(gbt_path)
                mlflow.log_metrics(
                    {f"gbt_{k}": v for k, v in gbt_metrics.items()}
                )
                mlflow.log_artifact(str(gbt_path))

            if TENSORFLOW_AVAILABLE:
                lstm = self.train_lstm(X_seq_train, y_seq_train)
                lstm_probs = lstm.predict(X_seq_test, verbose=0).flatten()
                lstm_preds = (lstm_probs > 0.5).astype(int)
                lstm_metrics = self.classification_metrics(
                    y_seq_test,
                    lstm_preds,
                )
                results["lstm"] = lstm_metrics
                lstm_path = self.output_dir / "dogon_lstm_model.keras"
                lstm.save(str(lstm_path))
                artifacts["lstm_model"] = str(lstm_path)
                mlflow.log_metrics(
                    {f"lstm_{k}": v for k, v in lstm_metrics.items()}
                )
                mlflow.log_artifact(str(lstm_path))

            if TENSORFLOW_AVAILABLE and TCN_AVAILABLE:
                tcn_model = self.train_tcn(X_seq_train, y_seq_train)
                tcn_probs = tcn_model.predict(X_seq_test, verbose=0).flatten()
                tcn_preds = (tcn_probs > 0.5).astype(int)
                tcn_metrics = self.classification_metrics(
                    y_seq_test,
                    tcn_preds,
                )
                results["tcn"] = tcn_metrics
                tcn_path = self.output_dir / "dogon_tcn_model.keras"
                tcn_model.save(str(tcn_path))
                artifacts["tcn_model"] = str(tcn_path)
                mlflow.log_metrics(
                    {f"tcn_{k}": v for k, v in tcn_metrics.items()}
                )
                mlflow.log_artifact(str(tcn_path))

            if not results:
                raise RuntimeError(
                    "No Dogon models trained; "
                    "install xgboost/tensorflow/keras-tcn"
                )

            best_model = max(
                results.items(),
                key=lambda item: item[1]["accuracy"],
            )
            promote = bool(
                best_model[1]["accuracy"] >= self.config.min_accuracy
            )
            mlflow.log_metric("best_accuracy", best_model[1]["accuracy"])
            mlflow.log_param("best_model", best_model[0])
            mlflow.log_param("promotion_passed", promote)

        summary = {
            "fund": "Mansa_ETF",
            "bot": "Dogon",
            "results": results,
            "best_model": best_model[0],
            "best_accuracy": float(best_model[1]["accuracy"]),
            "min_accuracy": float(self.config.min_accuracy),
            "promote": promote,
            "artifacts": artifacts,
        }

        summary_path = self.output_dir / "dogon_training_summary.json"
        summary_path.write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8",
        )
        notify_training_completion(
            bot_name="Dogon",
            model_label=str(best_model[0]).upper(),
            fields={
                "symbol": "ETF_BASKET",
                "run_id": run_id,
                "accuracy": f"{float(best_model[1]['accuracy']):.4f}",
            },
        )
        return summary


def train_and_evaluate(config: DogonTrainingConfig) -> Dict[str, object]:
    trainer = DogonModelTrainer(config)
    return trainer.run()


def _parse_symbols(raw_symbols: str) -> List[str]:
    return [
        symbol.strip().upper()
        for symbol in raw_symbols.split(",")
        if symbol.strip()
    ]


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train Dogon Mansa_ETF models"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=os.getenv("DOGON_ETF_SYMBOLS", "SPY,QQQ,IWM,DIA,XLK,XLF"),
        help="Comma-separated ETF symbols",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=_env_int("DOGON_TRAIN_DAYS", 730),
        help="Training lookback in days",
    )
    parser.add_argument(
        "--sequence-window",
        type=int,
        default=_env_int("DOGON_SEQUENCE_WINDOW", 30),
        help="Sequence window for LSTM/TCN",
    )
    parser.add_argument(
        "--min-accuracy",
        type=float,
        default=_env_float("DOGON_MIN_ACCURACY", 0.53),
        help="Minimum validation accuracy for promotion",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    config = DogonTrainingConfig(
        symbols=_parse_symbols(args.symbols),
        days=args.days,
        sequence_window=args.sequence_window,
        min_accuracy=args.min_accuracy,
    )
    summary = train_and_evaluate(config)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
