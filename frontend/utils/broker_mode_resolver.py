"""
Broker Mode Resolver - Unified mode resolution for all brokers

Provides consistent way to:
1. Get the effective mode for a broker (Live/Paper)
2. Get mode-specific credentials
3. Resolve credentials based on current mode

Used by all broker connectors to ensure they respect global/per-broker mode settings.
"""

from typing import Literal, Optional
from config.broker_mode_config import get_config
import os
import logging

logger = logging.getLogger(__name__)


def get_effective_mode(broker: str) -> Literal["paper", "live"]:
    """
    Get effective trading mode for a broker.

    Priority order:
    1. Environment variable (ALPACA_MODE, MT5_MODE, etc.)
    2. Broker config file setting
    3. Global default (paper)

    Args:
        broker: Broker name (alpaca, mt5, axi, ibkr)

    Returns:
        "paper" or "live"
    """
    try:
        config = get_config()
        return config.get_broker_mode(broker)
    except Exception as e:
        logger.warning(f"Could not get mode for {broker}: {e}. Defaulting to paper.")
        return "paper"


def resolve_mt5_credentials(broker: str = "mt5") -> dict:
    """
    Get MT5 trading credentials with mode-aware defaults.

    Resolves credentials based on current mode setting for the broker.

    Args:
        broker: Broker key (mt5, axi, etc.)

    Returns:
        dict with user, password, server, port
    """
    from frontend.utils.secrets_helper import get_secret

    mode = get_effective_mode(broker)

    # Get base credentials
    user = (
        get_secret(f"{broker.upper()}_USER", default=None)
        or get_secret(f"{broker.upper()}_ACCOUNT", default=None)
        or get_secret("MT5_USER", default=None)
    )

    password = (
        get_secret(f"{broker.upper()}_PASSWORD", default=None)
        or get_secret("MT5_PASSWORD", default=None)
    )

    # Mode-specific server (user can specify different servers per mode)
    server_env_paper = f"{broker.upper()}_SERVER_PAPER"
    server_env_live = f"{broker.upper()}_SERVER_LIVE"
    server_env = server_env_paper if mode == "paper" else server_env_live

    server = (
        get_secret(server_env, default=None)
        or get_secret(f"{broker.upper()}_SERVER", default=None)
        or get_secret(f"{broker.upper()}_HOST", default=None)
        or get_secret("MT5_SERVER", default=None)
        or get_secret("MT5_HOST", default=None)
    )

    # Port (typically same for paper and live)
    port = int(
        get_secret(f"{broker.upper()}_PORT", default=None)
        or get_secret("MT5_PORT", default="443")
    )

    return {
        "user": user,
        "password": password,
        "server": server,
        "port": port,
        "mode": mode,
    }


def resolve_broker_base_url(broker: str) -> dict:
    """
    Get base URLs for a broker, with mode awareness.

    Args:
        broker: Broker name (alpaca, etc.)

    Returns:
        dict with base_url and mode
    """
    from frontend.utils.secrets_helper import get_secret

    mode = get_effective_mode(broker)

    if broker.lower() == "alpaca":
        if mode == "paper":
            base_url = (
                get_secret("ALPACA_PAPER_BASE_URL", default=None)
                or get_secret("ALPACA_BASE_URL", default=None)
                or "https://paper-api.alpaca.markets"
            )
        else:
            base_url = (
                get_secret("ALPACA_LIVE_BASE_URL", default=None)
                or get_secret("ALPACA_BASE_URL", default=None)
                or "https://api.alpaca.markets"
            )

        return {"base_url": base_url, "mode": mode}

    return {"base_url": None, "mode": mode}


def log_mode_switch(broker: str, new_mode: Literal["paper", "live"]):
    """Log a broker mode switch event for audit trail."""
    logger.info(f"🔄 Broker mode changed: {broker.upper()} → {new_mode.upper()}")
