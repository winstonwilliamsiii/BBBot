"""Project settings helpers."""

import os


def get_env(name: str, default: str = "") -> str:
    """Read an environment variable with a safe default."""
    return os.getenv(name, default)
