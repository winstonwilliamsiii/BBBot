from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

try:
    import mlflow
except ImportError:
    mlflow = None

try:
    import mysql.connector
except ImportError:
    mysql = None

try:
    from transformers import pipeline
except ImportError:
    pipeline = None


logger = logging.getLogger(__name__)

DEFAULT_WSJ_MODEL = (
    "distilbert-base-uncased-finetuned-sst-2-english"
)
DEFAULT_SYMBOL_ALIASES: Dict[str, tuple[str, ...]] = {
    "AAPL": ("apple", "iphone", "ipad", "mac"),
    "MSFT": ("microsoft", "azure", "xbox", "openai"),
    "NVDA": ("nvidia", "geforce", "cuda"),
    "META": ("meta", "facebook", "instagram", "whatsapp"),
    "GOOGL": ("alphabet", "google", "youtube", "gemini"),
    "AMZN": ("amazon", "aws", "prime"),
    "AMD": ("amd", "advanced micro devices", "ryzen"),
    "AVGO": ("broadcom",),
}


class WsjSentimentService:
    def __init__(
        self,
        model_name: str | None = None,
        neutral_band: float = 0.15,
    ) -> None:
        self.model_name = model_name or os.getenv(
            "WSJ_SENTIMENT_MODEL",
            DEFAULT_WSJ_MODEL,
        )
        self.neutral_band = float(
            os.getenv("WSJ_SENTIMENT_NEUTRAL_BAND", str(neutral_band))
        )
        self._classifier = None

    def _get_classifier(self):
        if self._classifier is not None:
            return self._classifier
        if pipeline is None:
            raise RuntimeError(
                "transformers is not installed for WSJ sentiment analysis"
            )
        self._classifier = pipeline(
            "sentiment-analysis",
            model=self.model_name,
        )
        return self._classifier

    def analyze_headline(self, headline: str) -> Dict[str, Any]:
        text = str(headline or "").strip()
        if not text:
            raise ValueError("headline is required")

        result = self._get_classifier()(text)[0]
        raw_label = str(result.get("label") or "").upper()
        confidence = float(result.get("score") or 0.0)
        signed_score = confidence if raw_label == "POSITIVE" else -confidence

        if abs(signed_score) < self.neutral_band:
            sentiment_label = "neutral"
            normalized_score = 0.0
        elif signed_score > 0:
            sentiment_label = "bullish"
            normalized_score = min(1.0, signed_score)
        else:
            sentiment_label = "bearish"
            normalized_score = max(-1.0, signed_score)

        return {
            "headline": text,
            "sentiment_score": float(normalized_score),
            "sentiment_label": sentiment_label,
            "confidence_score": confidence,
            "raw_label": raw_label,
            "model_name": self.model_name,
        }

    def infer_tickers(
        self,
        headline: str,
        explicit_tickers: Optional[Sequence[str]] = None,
    ) -> List[str]:
        if explicit_tickers:
            return sorted(
                {
                    str(symbol).strip().upper()
                    for symbol in explicit_tickers
                    if str(symbol).strip()
                }
            )

        text = str(headline or "").lower()
        matches = []
        for symbol, aliases in DEFAULT_SYMBOL_ALIASES.items():
            if symbol.lower() in text:
                matches.append(symbol)
                continue
            if any(alias in text for alias in aliases):
                matches.append(symbol)
        return sorted(set(matches))

    def message_id(
        self,
        headline: str,
        article_id: Optional[str] = None,
    ) -> str:
        base = str(article_id or headline).strip()
        return hashlib.sha256(base.encode("utf-8")).hexdigest()[:32]

    def log_to_mlflow(
        self,
        analysis: Dict[str, Any],
        tickers: Sequence[str],
    ) -> None:
        if mlflow is None:
            return
        try:
            mlflow.set_tracking_uri(
                os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
            )
            with mlflow.start_run(run_name="wsj-headline-sentiment"):
                mlflow.log_param("source", "wsj")
                mlflow.log_param("tickers", ",".join(tickers))
                mlflow.log_param("sentiment_label", analysis["sentiment_label"])
                mlflow.log_param("model_name", analysis["model_name"])
                mlflow.log_metric(
                    "wsj_sentiment_score",
                    float(analysis["sentiment_score"]),
                )
                mlflow.log_metric(
                    "wsj_confidence_score",
                    float(analysis["confidence_score"]),
                )
        except Exception as exc:
            logger.warning("WSJ MLflow logging failed: %s", exc)

    def store_sentiment_message(
        self,
        tickers: Sequence[str],
        headline: str,
        analysis: Dict[str, Any],
        article_id: Optional[str] = None,
        article_url: Optional[str] = None,
        published_at: Optional[datetime] = None,
        author: Optional[str] = None,
    ) -> int:
        if mysql is None or not tickers:
            return 0

        try:
            conn = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST", "127.0.0.1"),
                port=int(os.getenv("MYSQL_PORT", "3307")),
                user=os.getenv("MYSQL_USER", "root"),
                password=os.getenv("MYSQL_PASSWORD", "root"),
                database=os.getenv("MYSQL_DATABASE", "mansa_bot"),
            )
        except Exception as exc:
            logger.warning("WSJ sentiment DB connection failed: %s", exc)
            return 0

        inserted = 0
        timestamp = published_at or datetime.now(timezone.utc)
        text = headline if not article_url else f"{headline}\n{article_url}"
        try:
            cursor = conn.cursor()
            for ticker in tickers:
                message_id = self.message_id(
                    f"{ticker}:{headline}",
                    article_id=article_id,
                )
                cursor.execute(
                    """
                    INSERT INTO sentiment_msgs (
                        ticker,
                        timestamp,
                        message_id,
                        message_text,
                        sentiment_score,
                        sentiment_label,
                        likes_count,
                        retweets_count,
                        replies_count,
                        user_id,
                        username,
                        user_followers,
                        user_verified,
                        source,
                        language,
                        has_link,
                        has_media,
                        message_count,
                        bullish_count,
                        bearish_count
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        sentiment_score = VALUES(sentiment_score),
                        sentiment_label = VALUES(sentiment_label),
                        message_text = VALUES(message_text),
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        ticker,
                        timestamp.replace(tzinfo=None),
                        message_id,
                        text,
                        float(analysis["sentiment_score"]),
                        analysis["sentiment_label"],
                        0,
                        0,
                        0,
                        article_id,
                        author or "wsj",
                        0,
                        False,
                        "wsj",
                        "en",
                        bool(article_url),
                        False,
                        1,
                        int(analysis["sentiment_score"] > 0),
                        int(analysis["sentiment_score"] < 0),
                    ),
                )
                inserted += 1
            conn.commit()
        except Exception as exc:
            logger.warning("WSJ sentiment persistence failed: %s", exc)
        finally:
            conn.close()

        return inserted