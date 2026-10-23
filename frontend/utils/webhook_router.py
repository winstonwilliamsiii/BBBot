# Webhook configuration for various bots

import os
from typing import Optional

_WEBHOOK_ENV_MAP = {
    "Titan": "WEBHOOK_TITAN",
    "Vega": "WEBHOOK_VEGA",
    "Rigel": "WEBHOOK_RIGEL",
    "Dogon": "WEBHOOK_DOGON",
    "Orion": "WEBHOOK_ORION",
    "Draco": "WEBHOOK_DRACO",
    "Altair": "WEBHOOK_ALTAIR",
    "Procryon": "WEBHOOK_PROCRYON",
    "Hydra": "WEBHOOK_HYDRA",
    "Triton": "WEBHOOK_TRITON",
    "Dione": "WEBHOOK_DIONE",
    "Cephei": "WEBHOOK_CEPHEI",
    "Rhea": "WEBHOOK_RHEA",
    "Jupicita": "WEBHOOK_JUPICITA",
    "Cygnus": "WEBHOOK_CYGNUS",
}

WEBHOOK_MAP = {
    bot_name: os.getenv(env_name)
    for bot_name, env_name in _WEBHOOK_ENV_MAP.items()
}
WEBHOOK_CONTROL_CENTER = os.getenv("WEBHOOK_CONTROL_CENTER")


def get_webhook(bot_name: Optional[str]) -> Optional[str]:
    """Return the current configured webhook URL for a bot, if present."""
    env_name = _WEBHOOK_ENV_MAP.get(bot_name)
    if not env_name:
        return None
    return os.getenv(env_name, "").strip() or None
