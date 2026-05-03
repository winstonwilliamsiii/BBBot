from __future__ import annotations

import json
from functools import lru_cache
from numbers import Integral, Real
from pathlib import Path
from typing import Any

import optuna

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "optuna_bot_configs.yaml"
_ALLOWED_ALGORITHMS = {
    "xgboost",
    "random_forest",
    "neural_network",
    "sentiment_nlp",
    "technical_strategy",
    "optimizer",
}


def _load_yaml(config_path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required for optuna_config_loader. Install it with: pip install pyyaml"
        ) from exc

    with open(config_path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Unexpected YAML structure in {config_path}")
    return data


@lru_cache(maxsize=4)
def _cached_config(config_path: str) -> dict[str, Any]:
    return _load_yaml(Path(config_path))


def _normalize_root(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if "bot_configs" in data:
        bot_configs = data["bot_configs"] or {}
        if not isinstance(bot_configs, dict):
            raise ValueError("optuna bot_configs must be a mapping")
        return bot_configs

    if "bot_config" in data:
        bot_config = data["bot_config"] or {}
        if not isinstance(bot_config, dict):
            raise ValueError("optuna bot_config must be a mapping")
        bot_name = str(bot_config.get("name") or "default_bot")
        return {bot_name: bot_config}

    raise ValueError("Optuna config YAML must define either 'bot_configs' or 'bot_config'")


def _validate_bot_config(bot_name: str, config: dict[str, Any]) -> dict[str, Any]:
    required_sections = ["algorithm", "risk_management", "data_sources", "logging"]
    missing_sections = [section for section in required_sections if section not in config]
    if missing_sections:
        missing = ", ".join(missing_sections)
        raise ValueError(f"Bot '{bot_name}' is missing required sections: {missing}")

    algorithm = config.get("algorithm") or {}
    algorithm_type = algorithm.get("type")
    if algorithm_type not in _ALLOWED_ALGORITHMS:
        allowed = ", ".join(sorted(_ALLOWED_ALGORITHMS))
        raise ValueError(
            f"Bot '{bot_name}' uses unsupported algorithm type '{algorithm_type}'. Allowed: {allowed}"
        )

    hyperparameters = algorithm.get("hyperparameters") or {}
    if not isinstance(hyperparameters, dict):
        raise ValueError(f"Bot '{bot_name}' hyperparameters must be a mapping")

    normalized = dict(config)
    normalized.setdefault("name", bot_name)
    return normalized


def load_optuna_bot_config(
    bot_name: str,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    path = str(config_path or _DEFAULT_CONFIG_PATH)
    data = _cached_config(path)
    bot_configs = _normalize_root(data)

    if bot_name not in bot_configs:
        available = ", ".join(bot_configs)
        raise KeyError(f"Bot '{bot_name}' not found in {path}. Available bots: {available}")

    config = dict(bot_configs[bot_name])
    config.setdefault("_config_path", path)
    return _validate_bot_config(bot_name, config)


def list_optuna_bots(config_path: str | Path | None = None) -> list[str]:
    path = str(config_path or _DEFAULT_CONFIG_PATH)
    data = _cached_config(path)
    return list(_normalize_root(data))


def reload_optuna_config() -> None:
    _cached_config.cache_clear()


def flatten_optuna_config_for_mlflow(config: dict[str, Any]) -> dict[str, str | int | float | bool]:
    flattened: dict[str, str | int | float | bool] = {}

    def _flatten(prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for key, nested_value in value.items():
                next_prefix = f"{prefix}.{key}" if prefix else str(key)
                _flatten(next_prefix, nested_value)
            return

        if isinstance(value, list):
            flattened[prefix] = json.dumps(value)
            return

        if isinstance(value, (str, bool, Integral, Real)) or value is None:
            flattened[prefix] = value if value is not None else "null"
            return

        flattened[prefix] = json.dumps(value, default=str)

    _flatten("", config)
    return flattened


def build_optuna_trial_params(trial: optuna.Trial, config: dict[str, Any]) -> dict[str, Any]:
    hyperparameters = config.get("algorithm", {}).get("hyperparameters", {})
    suggested: dict[str, Any] = {}

    for name, space in hyperparameters.items():
        if isinstance(space, list):
            if len(space) == 2 and all(isinstance(item, Integral) for item in space):
                suggested[name] = trial.suggest_int(name, int(space[0]), int(space[1]))
                continue

            if len(space) == 2 and all(isinstance(item, Real) for item in space):
                suggested[name] = trial.suggest_float(name, float(space[0]), float(space[1]))
                continue

            suggested[name] = trial.suggest_categorical(name, space)
            continue

        if isinstance(space, dict):
            space_type = space.get("type", "float")
            low = space.get("low")
            high = space.get("high")
            if space_type == "int":
                suggested[name] = trial.suggest_int(name, int(low), int(high), step=int(space.get("step", 1)))
                continue
            if space_type == "float":
                suggested[name] = trial.suggest_float(
                    name,
                    float(low),
                    float(high),
                    step=space.get("step"),
                    log=bool(space.get("log", False)),
                )
                continue
            if space_type == "categorical":
                suggested[name] = trial.suggest_categorical(name, list(space.get("choices", [])))
                continue

        raise ValueError(f"Unsupported search space for hyperparameter '{name}': {space!r}")

    return suggested