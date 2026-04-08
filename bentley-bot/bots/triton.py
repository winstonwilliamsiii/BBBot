"""Triton bot compatibility wrapper for the shared runtime module."""

from triton_bot import TritonBot


_BOT = TritonBot()


def start():
    """Start the bot."""
    return _BOT.bootstrap_demo_state()


def stop():
    """Stop the bot."""
    return {"status": "stopped", "name": "Triton"}


def get_status():
    """Get bot status."""
    return _BOT.status()


def configure(config):
    """Configure bot parameters."""
    return _BOT.configure(config)


if __name__ == "__main__":
    print(_BOT.bootstrap_demo_state())
