"""Lightweight sentiment engine placeholder."""
import logging
from typing import Dict, Optional

from sqlalchemy import text

from prediction_analytics.services.db import get_session_factory

logger = logging.getLogger(__name__)


class SentimentEngine:
    def __init__(self):
        self.session_factory = get_session_factory()

    def _score_text(self, text_value: str) -> float:
        bullish = sum(text_value.lower().count(word) for word in ["bullish", "buy", "long", "up", "profit"])
        bearish = sum(text_value.lower().count(word) for word in ["bearish", "sell", "short", "down", "loss"])
        total = bullish + bearish
        if total == 0:
            return 0.0
        return (bullish - bearish) / total

    async def store_signal(self, contract_id: str, text_value: str, source: str) -> Optional[Dict]:
        score = self._score_text(text_value)
        strength = "weak"
        if abs(score) >= 0.7:
            strength = "strong"
        elif abs(score) >= 0.3:
            strength = "moderate"

        with self.session_factory() as session:
            session.execute(text(
                """
                INSERT INTO mansa_quant.sentiment_signals
                (contract_id, sentiment_score, signal_strength, source)
                VALUES (:cid, :score, :strength, :source)
                """
            ), {
                "cid": contract_id,
                "score": round(score, 2),
                "strength": strength,
                "source": source,
            })
            session.commit()
            logger.info("Stored sentiment for %s score %.2f", contract_id, score)
            return {"contract_id": contract_id, "sentiment_score": score, "signal_strength": strength}
