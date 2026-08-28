"""Optional Hugging Face sentiment features for market news."""

from __future__ import annotations

from functools import lru_cache
import logging
from typing import Any

from frontend.utils.economic_data import get_economic_fetcher

logger = logging.getLogger(__name__)
MODEL_NAME = "ProsusAI/finbert"


@lru_cache(maxsize=1)
def _load_model() -> tuple[Any, Any, Any] | None:
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as exc:
        logger.warning("Hugging Face sentiment dependencies are unavailable: %s", exc)
        return None

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval()
    return tokenizer, model, torch


def _neutral_features() -> dict[str, float]:
    return {
        "hf_sentiment": 0.0,
        "hf_positive": 0.0,
        "hf_negative": 0.0,
        "hf_neutral": 1.0,
    }


def compute_hf_features(symbol: str) -> dict[str, float]:
    """Return FinBERT sentiment features, or neutral values if unavailable."""
    loaded = _load_model()
    if loaded is None:
        return _neutral_features()

    tokenizer, model, torch = loaded
    normalized_symbol = symbol.strip().upper()
    articles = get_economic_fetcher().get_economic_news(
        keywords=normalized_symbol,
        limit=5,
    ) or []
    article_text = [
        " ".join(
            part.strip()
            for part in (article.get("title"), article.get("description"))
            if isinstance(part, str) and part.strip()
        )
        for article in articles
        if isinstance(article, dict)
    ]
    text = " ".join(part for part in article_text if part)
    if not text:
        text = f"No recent financial news available for {normalized_symbol}"

    inputs = tokenizer(text, return_tensors="pt", truncation=True)
    with torch.inference_mode():
        outputs = model(**inputs)
    scores = torch.softmax(outputs.logits, dim=1).tolist()[0]

    return {
        "hf_sentiment": float(scores[2] - scores[0]),
        "hf_positive": float(scores[2]),
        "hf_negative": float(scores[0]),
        "hf_neutral": float(scores[1]),
    }
