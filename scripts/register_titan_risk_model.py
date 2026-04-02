from __future__ import annotations

import os
from typing import Any, Dict, List

import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow.tracking import MlflowClient
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from scripts.load_screener_csv import load_bot_trade_candidates
except ModuleNotFoundError:
    from load_screener_csv import load_bot_trade_candidates


FEATURE_COLUMNS = [
    "volume",
    "pe",
    "roe",
    "debt_to_equity",
]


BASELINE_ROWS = [
    {
        "volume": 64_000_000.0,
        "pe": 35.0,
        "roe": 62.0,
        "debt_to_equity": 0.40,
        "label": 1,
    },
    {
        "volume": 21_000_000.0,
        "pe": 33.0,
        "roe": 39.0,
        "debt_to_equity": 0.35,
        "label": 1,
    },
    {
        "volume": 52_000_000.0,
        "pe": 29.0,
        "roe": 55.0,
        "debt_to_equity": 1.45,
        "label": 0,
    },
    {
        "volume": 47_000_000.0,
        "pe": 38.0,
        "roe": 21.0,
        "debt_to_equity": 0.60,
        "label": 1,
    },
    {
        "volume": 18_000_000.0,
        "pe": 24.0,
        "roe": 30.0,
        "debt_to_equity": 0.10,
        "label": 1,
    },
    {
        "volume": 17_000_000.0,
        "pe": 26.0,
        "roe": 33.0,
        "debt_to_equity": 0.20,
        "label": 1,
    },
    {
        "volume": 95_000_000.0,
        "pe": 58.0,
        "roe": 19.0,
        "debt_to_equity": 0.18,
        "label": 0,
    },
]


def build_training_frame() -> pd.DataFrame:
    rows: List[Dict[str, Any]] = load_bot_trade_candidates("Titan_Bot")
    records: List[Dict[str, float]] = []

    for row in rows:
        fundamentals = row.get("fundamentals") or {}
        volume = float(fundamentals.get("volume") or 0.0)
        pe_ratio = float(fundamentals.get("pe") or 0.0)
        roe = float(fundamentals.get("roe") or 0.0)
        debt_to_equity = float(fundamentals.get("debt_to_equity") or 0.0)

        label = int(
            volume >= 5_000_000
            and pe_ratio <= 40.0
            and roe >= 15.0
            and debt_to_equity <= 0.8
        )

        records.append(
            {
                "volume": volume,
                "pe": pe_ratio,
                "roe": roe,
                "debt_to_equity": debt_to_equity,
                "label": label,
            }
        )

    if not records:
        records = list(BASELINE_ROWS)

    return pd.DataFrame.from_records(records)


def main() -> None:
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("Titan Models")

    training_frame = build_training_frame()
    features = training_frame[FEATURE_COLUMNS]
    target = training_frame["label"]

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(random_state=42)),
        ]
    )
    model.fit(features, target)

    with mlflow.start_run(run_name="TitanRiskModel-baseline") as run:
        mlflow.log_param("model_name", "TitanRiskModel")
        mlflow.log_param("feature_columns", ",".join(FEATURE_COLUMNS))
        mlflow.log_metric("training_rows", float(len(training_frame)))
        mlflow.log_metric("positive_labels", float(target.sum()))
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
        )

        model_uri = f"runs:/{run.info.run_id}/model"
        registered = mlflow.register_model(
            model_uri=model_uri,
            name="TitanRiskModel",
        )

    client = MlflowClient(tracking_uri=tracking_uri)
    client.transition_model_version_stage(
        name="TitanRiskModel",
        version=registered.version,
        stage="Production",
        archive_existing_versions=True,
    )

    print(f"Registered TitanRiskModel version {registered.version}")
    print("Production URI: models:/TitanRiskModel/Production")


if __name__ == "__main__":
    main()