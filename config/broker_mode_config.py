"""
Broker Mode Configuration System

Manages Live/Paper mode selection persistence across sessions.
Provides global and per-broker mode overrides with environment variable support.

Config structure:
{
    "global_mode": "paper",        # "paper" or "live" - default for all bots
    "broker_modes": {              # Per-broker overrides
        "alpaca": "paper",
        "mt5": "live",
        "axi": "paper"
    },
    "active_bots": {               # Which bots are currently active
        "Titan": true,
        "Vega": false,
        ...
    },
    "bot_broker_mapping": {        # Which broker each bot uses
        "Titan": "alpaca",
        "Vega": "ibkr",
        ...
    }
}
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Literal
import logging

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent
CONFIG_FILE = CONFIG_DIR / "broker_modes.json"


# Default bot-to-broker mapping
BOT_BROKER_MAPPING = {
    "Titan": "alpaca",
    "Vega": "axi",
    "Draco": "alpaca",
    "Altair": "alpaca",
    "Procryon": "alpaca",
    "Hydra": "alpaca",
    "Triton": "alpaca",
    "Dione": "ibkr",
    "Dogon": "alpaca",
    "Rigel": "ftmo",
    "Orion": "mt5",
    "Rhea": "alpaca",
    "Jupicita": "alpaca",
}

# Supported brokers
SUPPORTED_BROKERS = ["alpaca", "mt5", "ftmo", "axi", "ibkr"]


class BrokerModeConfig:
    """Persistent broker mode configuration manager."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config manager.

        Args:
            config_path: Path to config file (defaults to config/broker_modes.json)
        """
        self.config_path = config_path or CONFIG_FILE
        self._load_or_create()

    def _load_or_create(self):
        """Load config from file or create default if not exists."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    self.config = json.load(f)
                logger.info(f"Loaded broker mode config from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading config: {e}. Creating default config.")
                self._create_default()
        else:
            self._create_default()

    def _create_default(self):
        """Create default configuration."""
        self.config = {
            "global_mode": "paper",  # Default to paper trading
            "broker_modes": {
                "alpaca": "paper",
                "mt5": "paper",
                "ftmo": "paper",
                "axi": "paper",
                "ibkr": "paper",
            },
            "active_bots": {bot: False for bot in BOT_BROKER_MAPPING.keys()},
            "bot_broker_mapping": BOT_BROKER_MAPPING.copy(),
        }
        self.save()

    def save(self):
        """Persist config to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved broker mode config to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise

    def get_global_mode(self) -> Literal["paper", "live"]:
        """Get global mode setting."""
        return self.config.get("global_mode", "paper")

    def set_global_mode(self, mode: Literal["paper", "live"]):
        """Set global mode for all brokers."""
        if mode not in ("paper", "live"):
            raise ValueError(f"Invalid mode: {mode}. Must be 'paper' or 'live'.")
        self.config["global_mode"] = mode
        self.save()
        logger.info(f"Set global mode to: {mode}")

    def get_broker_mode(self, broker: str) -> Literal["paper", "live"]:
        """
        Get effective mode for a broker (respects overrides).

        Args:
            broker: Broker name (alpaca, mt5, axi, ibkr)

        Returns:
            "paper" or "live"
        """
        # Check for env var override first
        env_var = f"{broker.upper()}_MODE"
        env_mode = os.getenv(env_var, "").lower()
        if env_mode in ("paper", "live"):
            return env_mode

        # Check broker-specific override
        broker_modes = self.config.get("broker_modes", {})
        if broker in broker_modes:
            return broker_modes[broker]

        # Fall back to global mode
        return self.get_global_mode()

    def set_broker_mode(self, broker: str, mode: Literal["paper", "live"]):
        """Set mode override for a specific broker."""
        if broker not in SUPPORTED_BROKERS:
            raise ValueError(f"Unknown broker: {broker}")
        if mode not in ("paper", "live"):
            raise ValueError(f"Invalid mode: {mode}")

        self.config["broker_modes"][broker] = mode
        self.save()
        logger.info(f"Set {broker} mode to: {mode}")

    def get_bot_broker(self, bot_name: str) -> Optional[str]:
        """Get broker assigned to a bot."""
        mapping = self.config.get("bot_broker_mapping", {})
        return mapping.get(bot_name)

    def get_bot_mode(self, bot_name: str) -> Literal["paper", "live"]:
        """Get effective mode for a bot (via its broker)."""
        broker = self.get_bot_broker(bot_name)
        if not broker:
            return self.get_global_mode()
        return self.get_broker_mode(broker)

    def is_bot_active(self, bot_name: str) -> bool:
        """Check if a bot is running."""
        return self.config.get("active_bots", {}).get(bot_name, False)

    def set_bot_active(self, bot_name: str, active: bool):
        """Set bot running status."""
        if bot_name not in BOT_BROKER_MAPPING:
            raise ValueError(f"Unknown bot: {bot_name}")
        self.config["active_bots"][bot_name] = active
        self.save()
        logger.info(f"Bot {bot_name} set to: {'ACTIVE' if active else 'INACTIVE'}")

    def get_all_bots_status(self) -> Dict[str, Dict]:
        """Get status of all bots."""
        result = {}
        for bot_name in BOT_BROKER_MAPPING.keys():
            result[bot_name] = {
                "active": self.is_bot_active(bot_name),
                "broker": self.get_bot_broker(bot_name),
                "mode": self.get_bot_mode(bot_name),
            }
        return result

    def get_config_dict(self) -> Dict:
        """Get full config dictionary."""
        return self.config.copy()


# Global instance
_config_instance = None


def get_config() -> BrokerModeConfig:
    """Get or create global config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = BrokerModeConfig()
    return _config_instance


def sync_modes_from_env():
    """
    Sync environment variable mode overrides into config.

    Useful when environment variables change at runtime.
    """
    config = get_config()
    for broker in SUPPORTED_BROKERS:
        env_var = f"{broker.upper()}_MODE"
        env_mode = os.getenv(env_var, "").lower()
        if env_mode in ("paper", "live"):
            config.set_broker_mode(broker, env_mode)
