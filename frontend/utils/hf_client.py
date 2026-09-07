"""HTTP client for the deployed Hugging Face sentiment endpoint."""

from __future__ import annotations

import os
from typing import Any

import requests

HF_INFERENCE_URL = os.getenv(
    "HF_INFERENCE_URL",
    "http://127.0.0.1:8000/hf/sentiment",
).rstrip("/")
HF_INFERENCE_TIMEOUT_SECONDS = 30
_REQUIRED_FIELDS = ("hf_sentiment", "positive", "negative", "neutral")


def fetch_hf_sentiment(symbol: str, text: str) -> dict[str, float]:
    """Call the HF endpoint and return normalized sentiment features."""
    if not symbol.strip():
        raise ValueError("symbol must not be empty")
    if not text.strip():
        raise ValueError("text must not be empty")

    response = requests.post(
        HF_INFERENCE_URL,
        json={"symbol": symbol, "text": text},
        timeout=HF_INFERENCE_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload: Any = response.json()
    if not isinstance(payload, dict) or any(
        field not in payload for field in _REQUIRED_FIELDS
    ):
        raise ValueError("HF endpoint returned an incomplete sentiment response")

    return {
        "hf_sentiment": float(payload["hf_sentiment"]),
        "hf_positive": float(payload["positive"]),
        "hf_negative": float(payload["negative"]),
        "hf_neutral": float(payload["neutral"]),
    }
