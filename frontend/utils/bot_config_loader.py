"""
Bot Config Loader
─────────────────────────────────────────────────────────────────────────────
Loads bot strategy configuration from config/bots_config.yaml.
Switch the active bot without editing code — just change `active_bot` in the
YAML file (or pass `bot_name` explicitly to any loader function).

Usage:
    from frontend.utils.bot_config_loader import load_active_bot_config, load_bot_config

    # Load whichever bot is set as active_bot in bots_config.yaml
    cfg = load_active_bot_config()
    print(cfg["display_name"], cfg["strategy_name"])

    # Load a specific bot by name
    rhea = load_bot_config("Rhea_Bot")
    print(rhea["market_data"]["provider"])
─────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import os
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Resolve config file relative to this module so it works regardless of cwd.
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "bots_config.yaml"


def _load_yaml(config_path: Path) -> dict[str, Any]:
    """Parse a YAML file and return its contents as a dict."""
    try:
        import yaml  # PyYAML — already in requirements.txt
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required for bot_config_loader. "
            "Install it with: pip install pyyaml"
        ) from exc

    with open(config_path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise ValueError(f"Unexpected YAML structure in {config_path}")
    return data


@lru_cache(maxsize=4)
def _cached_config(config_path: str) -> dict[str, Any]:
    """Cached YAML parse — busted on process restart."""
    return _load_yaml(Path(config_path))


def load_bot_config(
    bot_name: str,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Return the config dict for the named bot.

    Parameters
    ----------
    bot_name:
        Key as it appears in the YAML `bots` block, e.g. ``"Titan_Bot"``.
    config_path:
        Override path to bots_config.yaml.  Defaults to
        ``config/bots_config.yaml`` at the workspace root.

    Raises
    ------
    KeyError
        If *bot_name* is not found in the config file.
    """
    path = str(config_path or _DEFAULT_CONFIG_PATH)
    data = _cached_config(path)
    bots: dict[str, Any] = data.get("bots", {})

    if bot_name not in bots:
        available = ", ".join(bots.keys())
        raise KeyError(
            f"Bot '{bot_name}' not found in {path}. "
            f"Available bots: {available}"
        )

    cfg = dict(bots[bot_name])  # shallow copy so callers can't mutate cache
    cfg.setdefault("_config_path", path)
    cfg.setdefault("_bot_key", bot_name)
    return cfg


def load_active_bot_config(
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Return the config dict for the bot listed under ``active_bot`` in the YAML.

    The environment variable ``ACTIVE_BOT`` can override the YAML value at
    runtime without touching any file.

    Example::

        # In your shell:
        #   $env:ACTIVE_BOT = "Rhea_Bot"
        cfg = load_active_bot_config()
    """
    path = str(config_path or _DEFAULT_CONFIG_PATH)
    data = _cached_config(path)

    # Env var takes precedence over YAML so ops can switch without file edits.
    active = os.environ.get("ACTIVE_BOT") or data.get("active_bot")
    if not active:
        raise ValueError(
            f"No active_bot defined in {path} and ACTIVE_BOT env var is not set."
        )

    logger.info("Loading active bot config: %s", active)
    return load_bot_config(active, config_path=path)


def list_available_bots(config_path: str | Path | None = None) -> list[str]:
    """Return the list of bot keys defined in bots_config.yaml."""
    path = str(config_path or _DEFAULT_CONFIG_PATH)
    data = _cached_config(path)
    return list(data.get("bots", {}).keys())


def get_active_bot_name(config_path: str | Path | None = None) -> str:
    """Return the currently active bot name (env override or YAML value)."""
    path = str(config_path or _DEFAULT_CONFIG_PATH)
    data = _cached_config(path)
    return os.environ.get("ACTIVE_BOT") or data.get("active_bot", "")


def reload_config(config_path: str | Path | None = None) -> None:
    """
    Clear the loader cache so the next call re-reads the YAML from disk.
    Useful in long-running processes (e.g. Streamlit, Airflow) when the
    config file changes at runtime.
    """
    _cached_config.cache_clear()
    logger.info("Bot config cache cleared — will reload from %s on next access.", config_path or _DEFAULT_CONFIG_PATH)
