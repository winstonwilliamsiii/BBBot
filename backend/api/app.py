"""Compatibility launcher for the unified Bentley FastAPI app."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from Main import app  # noqa: E402

__all__ = ["app"]


def _host() -> str:
    return os.getenv("CONTROL_CENTER_API_HOST", "0.0.0.0")


def _port() -> int:
    for name in ("CONTROL_CENTER_API_PORT", "PORT"):
        value = os.getenv(name)
        if value:
            try:
                return int(value)
            except ValueError:
                continue
    return 5001


if __name__ == "__main__":
    print("Starting Bentley Bot FastAPI control center...")
    print(f"API available at: http://localhost:{_port()}")
    print(f"Docs available at: http://localhost:{_port()}/docs")
    uvicorn.run("Main:app", host=_host(), port=_port(), reload=False)
