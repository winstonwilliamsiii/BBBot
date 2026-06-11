from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np
import pandas as pd

try:
    import mlflow.pyfunc as mlflow_pyfunc
except ImportError:
    mlflow_pyfunc = None

try:
    from tensorflow import keras

    TENSORFLOW_AVAILABLE = True
except ImportError:
    keras = None
    TENSORFLOW_AVAILABLE = False


BASE_FEATURE_COLUMNS: tuple[str, ...] = (
    "rsi_14",
    "bb_bandwidth",
    "bb_percent_b",
    "sentiment_score",
    "liquidity_ratio",
)
DEFAULT_SEQUENCE_WINDOW = 20


if mlflow_pyfunc is not None:
    _PyfuncBase = mlflow_pyfunc.PythonModel
else:
    class _PyfuncBase:
        pass


def make_flat_feature_columns(
    feature_columns: Sequence[str] = BASE_FEATURE_COLUMNS,
    window_size: int = DEFAULT_SEQUENCE_WINDOW,
) -> List[str]:
    columns: List[str] = []
    for offset in range(window_size):
        step_label = f"t_minus_{window_size - offset - 1}"
        for feature_name in feature_columns:
            columns.append(f"{feature_name}_{step_label}")
    return columns


def compute_rsi_series(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gains = delta.clip(lower=0).rolling(period).mean()
    losses = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gains / losses.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_bollinger_features(
    series: pd.Series,
    period: int = 20,
    std_dev: int = 2,
) -> pd.DataFrame:
    middle = series.rolling(period).mean()
    deviation = series.rolling(period).std()
    upper = middle + std_dev * deviation
    lower = middle - std_dev * deviation
    spread = (upper - lower).replace(0, np.nan)
    bandwidth = spread / middle.replace(0, np.nan)
    percent_b = (series - lower) / spread
    return pd.DataFrame(
        {
            "bb_bandwidth": bandwidth,
            "bb_percent_b": percent_b,
        },
        index=series.index,
    )


def build_feature_timeseries(
    close_series: pd.Series,
    sentiment_score: float,
    liquidity_ratio: float,
) -> pd.DataFrame:
    close = pd.to_numeric(close_series, errors="coerce").dropna()
    if close.empty:
        return pd.DataFrame(columns=list(BASE_FEATURE_COLUMNS))

    features = compute_bollinger_features(close)
    features["rsi_14"] = compute_rsi_series(close, period=14)
    features["sentiment_score"] = float(sentiment_score)
    features["liquidity_ratio"] = float(liquidity_ratio)
    return features[list(BASE_FEATURE_COLUMNS)].dropna()


def build_sequence_frame(
    feature_timeseries: pd.DataFrame,
    window_size: int = DEFAULT_SEQUENCE_WINDOW,
    feature_columns: Sequence[str] = BASE_FEATURE_COLUMNS,
) -> pd.DataFrame:
    if feature_timeseries.empty or len(feature_timeseries) < window_size:
        columns = make_flat_feature_columns(
            feature_columns,
            window_size,
        )
        return pd.DataFrame(columns=columns)

    rows: List[Dict[str, float]] = []
    indices: List[Any] = []
    ordered_columns = list(feature_columns)

    for end_index in range(window_size - 1, len(feature_timeseries)):
        window = feature_timeseries.iloc[end_index - window_size + 1 : end_index + 1]
        flattened: Dict[str, float] = {}
        for offset, (_, row) in enumerate(window.iterrows()):
            step_label = f"t_minus_{window_size - offset - 1}"
            for feature_name in ordered_columns:
                flattened[f"{feature_name}_{step_label}"] = float(row[feature_name])
        rows.append(flattened)
        indices.append(feature_timeseries.index[end_index])

    return pd.DataFrame(rows, index=indices)


def build_neutral_feature_row(
    sentiment_score: float,
    liquidity_ratio: float,
    window_size: int = DEFAULT_SEQUENCE_WINDOW,
    feature_columns: Sequence[str] = BASE_FEATURE_COLUMNS,
) -> Dict[str, float]:
    defaults = {
        "rsi_14": 50.0,
        "bb_bandwidth": 0.05,
        "bb_percent_b": 0.50,
        "sentiment_score": float(sentiment_score),
        "liquidity_ratio": float(liquidity_ratio),
    }
    flattened: Dict[str, float] = {}
    for offset in range(window_size):
        step_label = f"t_minus_{window_size - offset - 1}"
        for feature_name in feature_columns:
            flattened[f"{feature_name}_{step_label}"] = float(defaults[feature_name])
    return flattened


def build_latest_sequence_features(
    close_series: pd.Series,
    sentiment_score: float,
    liquidity_ratio: float,
    window_size: int = DEFAULT_SEQUENCE_WINDOW,
    feature_columns: Sequence[str] = BASE_FEATURE_COLUMNS,
) -> Dict[str, float]:
    features = build_feature_timeseries(
        close_series=close_series,
        sentiment_score=sentiment_score,
        liquidity_ratio=liquidity_ratio,
    )
    sequence_frame = build_sequence_frame(
        feature_timeseries=features,
        window_size=window_size,
        feature_columns=feature_columns,
    )
    if sequence_frame.empty:
        return build_neutral_feature_row(
            sentiment_score=sentiment_score,
            liquidity_ratio=liquidity_ratio,
            window_size=window_size,
            feature_columns=feature_columns,
        )
    latest = sequence_frame.tail(1)
    return {
        column: float(latest.iloc[0][column])
        for column in latest.columns
    }


def sequence_tensor_from_frame(
    frame: pd.DataFrame,
    window_size: int = DEFAULT_SEQUENCE_WINDOW,
    feature_columns: Sequence[str] = BASE_FEATURE_COLUMNS,
) -> np.ndarray:
    ordered = frame.reindex(
        columns=make_flat_feature_columns(feature_columns, window_size),
        fill_value=0.0,
    )
    return ordered.to_numpy(dtype="float32").reshape(
        len(ordered),
        window_size,
        len(feature_columns),
    )


def fit_scaler_stats(sequence_tensor: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    means = sequence_tensor.mean(axis=(0, 1))
    stds = sequence_tensor.std(axis=(0, 1))
    stds = np.where(stds == 0, 1.0, stds)
    return means.astype("float32"), stds.astype("float32")


def apply_scaler(
    sequence_tensor: np.ndarray,
    means: np.ndarray,
    stds: np.ndarray,
) -> np.ndarray:
    return (sequence_tensor - means.reshape(1, 1, -1)) / stds.reshape(1, 1, -1)


def build_cnn_model(
    window_size: int = DEFAULT_SEQUENCE_WINDOW,
    feature_count: int = len(BASE_FEATURE_COLUMNS),
):
    if keras is None:
        raise RuntimeError("tensorflow is not installed")

    model = keras.Sequential(
        [
            keras.layers.Input(shape=(window_size, feature_count)),
            keras.layers.Conv1D(32, 3, padding="causal", activation="relu"),
            keras.layers.Conv1D(16, 3, padding="causal", activation="relu"),
            keras.layers.GlobalAveragePooling1D(),
            keras.layers.Dense(16, activation="relu"),
            keras.layers.Dropout(0.15),
            keras.layers.Dense(1, activation="sigmoid"),
        ]
    )
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="binary_crossentropy",
        metrics=["accuracy", keras.metrics.AUC(name="auc")],
    )
    return model


class TitanCnnPyfuncModel(_PyfuncBase):
    def load_context(self, context) -> None:
        if keras is None:
            raise RuntimeError("tensorflow is required to load Titan CNN model")

        config_path = Path(context.artifacts["model_config"])
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        self.window_size = int(payload["window_size"])
        self.feature_columns = list(payload["feature_columns"])
        self.flat_feature_columns = make_flat_feature_columns(
            self.feature_columns,
            self.window_size,
        )
        self.prediction_threshold = float(payload.get("prediction_threshold", 0.5))
        self.scaler_means = np.array(payload["scaler_means"], dtype="float32")
        self.scaler_stds = np.array(payload["scaler_stds"], dtype="float32")
        self.model = keras.models.load_model(
            context.artifacts["keras_model"],
            compile=False,
        )

    def predict(self, context, model_input):
        if isinstance(model_input, dict):
            frame = pd.DataFrame([model_input])
        elif isinstance(model_input, pd.DataFrame):
            frame = model_input.copy()
        else:
            frame = pd.DataFrame(model_input)

        ordered = frame.reindex(columns=self.flat_feature_columns, fill_value=0.0)
        tensor = ordered.to_numpy(dtype="float32").reshape(
            len(ordered),
            self.window_size,
            len(self.feature_columns),
        )
        scaled = apply_scaler(tensor, self.scaler_means, self.scaler_stds)
        probabilities = self.model.predict(scaled, verbose=0).reshape(-1)
        predictions = (probabilities >= self.prediction_threshold).astype(int)
        return pd.DataFrame(
            {
                "prediction": predictions.astype(int),
                "probability": probabilities.astype(float),
            }
        )