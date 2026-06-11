"""
MLflow Training Pipeline

Handles training pipeline operations.
"""
from __future__ import annotations

import importlib
from typing import Any

mlflow = importlib.import_module("mlflow")

from frontend.utils.optuna_config_loader import (
    build_optuna_trial_params,
    flatten_optuna_config_for_mlflow,
    load_optuna_bot_config,
)

def suggest_optuna_params_for_bot(trial: Any, bot_name: str, config_path: str | None = None) -> dict[str, Any]:
    """Build Optuna trial suggestions from the shared bot hyperparameter YAML."""
    config = load_optuna_bot_config(bot_name, config_path=config_path)
    return build_optuna_trial_params(trial, config)


def train_model(bot_id, data, params, bot_name: str | None = None, config_path: str | None = None):
    """Training Pipeline for bot."""
    _ = data
    run_params = dict(params or {})
    run_tags: dict[str, str] = {}

    if bot_name:
        bot_config = load_optuna_bot_config(bot_name, config_path=config_path)
        run_params.update(flatten_optuna_config_for_mlflow(bot_config))
        run_tags = {
            "bot_name": str(bot_config["name"]),
            "bot_domain": str(bot_config.get("domain", "unknown")),
            "algorithm_type": str(bot_config["algorithm"]["type"]),
        }

    print(f"Training Pipeline: Bot {bot_id}")
    with mlflow.start_run():
        if run_tags:
            mlflow.set_tags(run_tags)
        mlflow.log_params(run_params)
        # Model training/backtesting logic here
        mlflow.log_metric("accuracy", 0.85)
    return {"status": "success", "bot_id": bot_id}

if __name__ == "__main__":
    print("MLflow Training Pipeline - Ready")
