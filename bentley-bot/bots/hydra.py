"""Hydra bot compatibility wrapper for the control center package."""

from hydra_bot import HydraBot


_BOT = HydraBot()


def start():
    """Start the bot."""
    print("Starting Hydra (Mansa Health)")
    return _BOT.bootstrap_demo_state()


def stop():
    """Stop the bot."""
    print("Stopping Hydra (Mansa Health)")
    return {"status": "stopped", "name": "Hydra"}


def get_status():
    """Get bot status."""
    return _BOT.status()


def configure(config):
    """Configure bot parameters."""
    print(f"Configuring Hydra with: {config}")
    return _BOT.configure(config)


if __name__ == "__main__":
    print(_BOT.bootstrap_demo_state())
