from __future__ import annotations

import json
from typing import Any, Dict, Optional

try:
    import mlflow
    from mlflow.exceptions import MlflowException
except ImportError:
    mlflow = None
    MlflowException = RuntimeError

try:
    from bbbot1_pipeline.mlflow_config import get_mlflow_tracking_uri
except ImportError:
    def get_mlflow_tracking_uri() -> str:
        return "http://localhost:5000"


BENCHMARK_GROUP = "Titan_vs_Orion_Rigel_Dogon"


def _safe_set_tags(tags: Dict[str, Any]) -> None:
    if mlflow is None or not tags:
        return

    if hasattr(mlflow, "set_tags"):
        mlflow.set_tags(tags)
        return

    for key, value in tags.items():
        mlflow.set_tag(key, value)


def _safe_log_params(params: Dict[str, Any]) -> None:
    if mlflow is None or not params:
        return

    if hasattr(mlflow, "log_params"):
        mlflow.log_params(params)
        return

    for key, value in params.items():
        mlflow.log_param(key, value)


def _safe_log_metrics(metrics: Dict[str, float]) -> None:
    if mlflow is None or not metrics:
        return

    for key, value in metrics.items():
        mlflow.log_metric(key, float(value))


def _coerce_numeric_metrics(payload: Dict[str, Any]) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    for key, value in payload.items():
        if isinstance(value, bool):
            metrics[key] = float(value)
        elif isinstance(value, (int, float)):
            metrics[key] = float(value)
    return metrics


def log_bot_benchmark_run(
    *,
    bot_name: str,
    experiment_name: str,
    run_name: str,
    payload: Dict[str, Any],
    strategy_label: str,
    discipline_mode: str,
    extra_params: Optional[Dict[str, Any]] = None,
    extra_tags: Optional[Dict[str, Any]] = None,
    tracking_uri: Optional[str] = None,
) -> bool:
    if mlflow is None:
        return False

    resolved_tracking_uri = tracking_uri or get_mlflow_tracking_uri()
    try:
        mlflow.set_tracking_uri(resolved_tracking_uri)
        mlflow.set_experiment(experiment_name)

        # End any lingering active run before starting a new one (e.g. from a
        # previous crashed invocation in the same process).
        if mlflow.active_run() is not None:
            mlflow.end_run()

        with mlflow.start_run(run_name=run_name):
            _safe_set_tags(
                {
                    "bot": bot_name,
                    "strategy": strategy_label,
                    "discipline_mode": discipline_mode,
                    "benchmark_group": BENCHMARK_GROUP,
                    **(extra_tags or {}),
                }
            )
            _safe_log_params(
                {
                    "bot_name": bot_name,
                    "strategy_label": strategy_label,
                    "discipline_mode": discipline_mode,
                    **(extra_params or {}),
                }
            )
            _safe_log_metrics(_coerce_numeric_metrics(payload))

            if hasattr(mlflow, "log_dict"):
                mlflow.log_dict(payload, f"{bot_name.lower()}_benchmark_run.json")
            elif hasattr(mlflow, "log_text"):
                mlflow.log_text(
                    json.dumps(payload, indent=2, default=str),
                    f"{bot_name.lower()}_benchmark_run.json",
                )
        return True
    except (
        RuntimeError,
        TypeError,
        ValueError,
        MlflowException,
    ):
        return False