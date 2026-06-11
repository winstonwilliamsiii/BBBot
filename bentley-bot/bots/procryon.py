"""Procryon bot wrapper for the shared runtime module."""

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ProcryonBot = importlib.import_module("procryon_bot").ProcryonBot
_BOT = ProcryonBot()
_BOT.bootstrap_demo_models()


def start():
    """Start the bot."""
    return {"status": "running", "details": _BOT.status()}


def stop():
    """Stop the bot."""
    return {"status": "stopped", "name": "Procryon"}


def get_status():
    """Get bot status."""
    return _BOT.status()


def configure(config):
    """Configure bot parameters."""
    return _BOT.configure(config)


if __name__ == "__main__":
    print(_BOT.status())
# End of Procryon wrapper.

