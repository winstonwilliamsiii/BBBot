from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict, List

import mlflow
import mlflow.pyfunc
import pandas as pd
import yfinance as yf
from mlflow.tracking import MlflowClient

try:
    import mysql.connector
except ImportError:
    mysql = None
else:
    mysql = mysql.connector

try:
    from scripts.load_screener_csv import load_bot_trade_candidates
    from scripts.titan_cnn_model import (
        BASE_FEATURE_COLUMNS,
        DEFAULT_SEQUENCE_WINDOW,
        TitanCnnPyfuncModel,
        apply_scaler,
        build_cnn_model,
        build_feature_timeseries,
        build_sequence_frame,
        fit_scaler_stats,
        sequence_tensor_from_frame,
    )
except ModuleNotFoundError:
    from load_screener_csv import load_bot_trade_candidates
    from titan_cnn_model import (
        BASE_FEATURE_COLUMNS,
        DEFAULT_SEQUENCE_WINDOW,
        TitanCnnPyfuncModel,
        apply_scaler,
        build_cnn_model,
        build_feature_timeseries,
        build_sequence_frame,
        fit_scaler_stats,
        sequence_tensor_from_frame,
    )

try:
    from scripts.noomo_ml_notify import notify_training_completion
except ImportError:
    from noomo_ml_notify import notify_training_completion

EXPERIMENT_NAME = "Titan Models Local"


def _load_sentiment_map(table_name: str) -> Dict[str, float]:
    if mysql is None:
        return {}

    conn = mysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3307")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "root"),
        database=os.getenv("MYSQL_DATABASE", "mansa_bot"),
    )
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT UPPER(ticker) AS ticker, AVG(sentiment_score) AS avg_sentiment
            FROM {table_name}
            GROUP BY UPPER(ticker)
            """
        )
        return {
            str(ticker).strip().upper(): float(score)
            for ticker, score in cursor.fetchall()
            if ticker is not None and score is not None
        }
    except Exception:
        return {}
    finally:
        conn.close()


def _fetch_close_history(symbol: str, history_days: int) -> pd.Series:
    data = yf.download(symbol, period=f"{history_days}d", progress=False)
    if data is None or data.empty or "Close" not in data:
        return pd.Series(dtype="float64")

    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return pd.to_numeric(close, errors="coerce").dropna()


def build_training_frame(
    window_size: int,
    history_days: int,
    forward_days: int,
    return_threshold: float,
    liquidity_ratio: float,
    sentiment_table: str,
) -> tuple[pd.DataFrame, pd.Series]:
    rows: List[Dict[str, Any]] = load_bot_trade_candidates("Titan_Bot")
    sentiment_map = _load_sentiment_map(sentiment_table)
    frames: List[pd.DataFrame] = []
    labels: List[pd.Series] = []
    fallback_positive = build_sequence_frame(
        build_feature_timeseries(
            pd.Series(
                [100 + idx * 0.5 for idx in range(window_size + 25)],
                dtype="float64",
            ),
            sentiment_score=0.35,
            liquidity_ratio=0.45,
        ),
        window_size=window_size,
        feature_columns=BASE_FEATURE_COLUMNS,
    )
    fallback_negative = build_sequence_frame(
        build_feature_timeseries(
            pd.Series(
                [130 - idx * 0.8 for idx in range(window_size + 25)],
                dtype="float64",
            ),
            sentiment_score=-0.45,
            liquidity_ratio=0.18,
        ),
        window_size=window_size,
        feature_columns=BASE_FEATURE_COLUMNS,
    )

    for row in rows:
        symbol = str(row.get("symbol") or "").strip().upper()
        if not symbol:
            continue

        close = _fetch_close_history(
            symbol,
            history_days=history_days + forward_days + window_size,
        )
        if close.empty:
            continue

        feature_timeseries = build_feature_timeseries(
            close_series=close,
            sentiment_score=float(sentiment_map.get(symbol, 0.0)),
            liquidity_ratio=liquidity_ratio,
        )
        sequence_frame = build_sequence_frame(
            feature_timeseries=feature_timeseries,
            window_size=window_size,
            feature_columns=BASE_FEATURE_COLUMNS,
        )
        if sequence_frame.empty:
            continue

        forward_returns = (close.shift(-forward_days) / close) - 1.0
        aligned_returns = forward_returns.reindex(sequence_frame.index)
        valid_mask = aligned_returns.notna()
        if not valid_mask.any():
            continue

        frames.append(sequence_frame.loc[valid_mask])
        labels.append((aligned_returns.loc[valid_mask] >= return_threshold).astype(int))

    if not frames or not labels:
        fallback = pd.concat(
            [fallback_positive.tail(1), fallback_negative.tail(1)],
            axis=0,
        ).reset_index(drop=True)
        return fallback, pd.Series([1, 0], dtype="int64")

    return pd.concat(frames, axis=0), pd.concat(labels, axis=0).astype("int64")


def main() -> None:
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient(tracking_uri=tracking_uri)
    window_size = int(os.getenv("TITAN_SEQUENCE_WINDOW", str(DEFAULT_SEQUENCE_WINDOW)))
    history_days = int(os.getenv("TITAN_TRAINING_HISTORY_DAYS", "260"))
    forward_days = int(os.getenv("TITAN_TRAINING_FORWARD_DAYS", "5"))
    return_threshold = float(os.getenv("TITAN_TRAINING_RETURN_THRESHOLD", "0.02"))
    training_liquidity_ratio = float(
        os.getenv("TITAN_TRAINING_LIQUIDITY_RATIO", "0.35")
    )
    sentiment_table = os.getenv("TITAN_SENTIMENT_TABLE", "sentiment_msgs")
    artifact_root = (
        "file:///c:/Users/winst/BentleyBudgetBot/data/mlflow/artifacts/"
        "titan-models"
    )
    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        experiment_id = client.create_experiment(
            EXPERIMENT_NAME,
            artifact_location=artifact_root,
        )
    else:
        experiment_id = experiment.experiment_id

    mlflow.set_experiment(experiment_id=experiment_id)

    training_frame, target = build_training_frame(
        window_size=window_size,
        history_days=history_days,
        forward_days=forward_days,
        return_threshold=return_threshold,
        liquidity_ratio=training_liquidity_ratio,
        sentiment_table=sentiment_table,
    )
    sequence_tensor = sequence_tensor_from_frame(
        training_frame,
        window_size=window_size,
        feature_columns=BASE_FEATURE_COLUMNS,
    )
    scaler_means, scaler_stds = fit_scaler_stats(sequence_tensor)
    scaled_tensor = apply_scaler(sequence_tensor, scaler_means, scaler_stds)

    model = build_cnn_model(
        window_size=window_size,
        feature_count=len(BASE_FEATURE_COLUMNS),
    )
    history = model.fit(
        scaled_tensor,
        target.to_numpy(dtype="float32"),
        epochs=int(os.getenv("TITAN_TRAINING_EPOCHS", "25")),
        batch_size=int(os.getenv("TITAN_TRAINING_BATCH_SIZE", "16")),
        validation_split=0.2 if len(training_frame) >= 10 else 0.0,
        verbose=0,
    )

    probabilities = model.predict(scaled_tensor, verbose=0).reshape(-1)
    predictions = (probabilities >= 0.5).astype(int)
    accuracy = float((predictions == target.to_numpy(dtype="int64")).mean())

    with tempfile.TemporaryDirectory() as tmp_dir:
        keras_model_path = os.path.join(tmp_dir, "titan_cnn.keras")
        model.save(keras_model_path)
        config_payload = {
            "window_size": window_size,
            "feature_columns": list(BASE_FEATURE_COLUMNS),
            "prediction_threshold": 0.5,
            "scaler_means": scaler_means.tolist(),
            "scaler_stds": scaler_stds.tolist(),
        }
        config_path = os.path.join(tmp_dir, "titan_cnn_config.json")
        with open(config_path, "w", encoding="utf-8") as handle:
            json.dump(config_payload, handle, indent=2)

        run_id = "n/a"
        with mlflow.start_run(run_name="TitanRiskModel-cnn") as run:
            run_id = run.info.run_id
            mlflow.log_param("model_name", "TitanRiskModel")
            mlflow.log_param("model_architecture", "cnn_1d")
            mlflow.log_param(
                "feature_columns",
                ",".join(BASE_FEATURE_COLUMNS),
            )
            mlflow.log_param("sequence_window", window_size)
            mlflow.log_param("forward_days", forward_days)
            mlflow.log_param("sentiment_table", sentiment_table)
            mlflow.log_metric("training_rows", float(len(training_frame)))
            mlflow.log_metric("positive_labels", float(target.sum()))
            mlflow.log_metric("train_accuracy", accuracy)
            if history.history.get("loss"):
                mlflow.log_metric(
                    "final_loss",
                    float(history.history["loss"][-1]),
                )
            if history.history.get("auc"):
                mlflow.log_metric(
                    "final_auc",
                    float(history.history["auc"][-1]),
                )

            mlflow.pyfunc.log_model(
                artifact_path="model",
                python_model=TitanCnnPyfuncModel(),
                code_paths=["scripts/titan_cnn_model.py"],
                artifacts={
                    "keras_model": keras_model_path,
                    "model_config": config_path,
                },
            )

            model_uri = f"runs:/{run.info.run_id}/model"
            registered = mlflow.register_model(
                model_uri=model_uri,
                name="TitanRiskModel",
            )

    client.transition_model_version_stage(
        name="TitanRiskModel",
        version=registered.version,
        stage="Production",
        archive_existing_versions=True,
    )

    print(f"Registered TitanRiskModel version {registered.version}")
    print("Production URI: models:/TitanRiskModel/Production")
    notify_training_completion(
        bot_name="Titan",
        model_label="CNN",
        fields={
            "symbol": "Titan_Bot",
            "run_id": run_id,
            "accuracy": f"{accuracy:.4f}",
        },
    )


if __name__ == "__main__":
    main()