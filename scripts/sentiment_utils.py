from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

import requests

mlflow = None  # loaded lazily in log_to_mlflow() to avoid blocking startup

try:
    import mysql.connector
except ImportError:
    mysql = None

pipeline = None  # loaded lazily in _get_classifier() to avoid blocking startup


logger = logging.getLogger(__name__)

DEFAULT_SENTIMENT_MODEL = (
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


def notify_discord(
    message: str,
    webhook_url: Optional[str] = None,
    timeout: int = 8,
) -> bool:
    resolved_webhook = (
        webhook_url
        or os.getenv("DISCORD_WEBHOOK_URL")
        or os.getenv("DISCORD_WEBHOOK")
        or os.getenv("DISCORD_WEBHOOK_PROD")
    )
    if not resolved_webhook:
        return False

    try:
        requests.post(
            resolved_webhook,
            json={"content": message},
            timeout=timeout,
        )
        return True
    except requests.RequestException as exc:
        logger.warning("Discord notification failed: %s", exc)
        return False


def parse_published_at(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.now(timezone.utc)


class HeadlineSentimentService:
    def __init__(
        self,
        source_name: str,
        model_name: str | None = None,
        neutral_band: float = 0.15,
        symbol_aliases: Optional[Dict[str, tuple[str, ...]]] = None,
        sentiment_table: str = "sentiment_msgs",
    ) -> None:
        self.source_name = source_name.lower().strip()
        self.model_name = model_name or os.getenv(
            f"{self.source_name.upper()}_SENTIMENT_MODEL",
            os.getenv("DEFAULT_SENTIMENT_MODEL", DEFAULT_SENTIMENT_MODEL),
        )
        self.neutral_band = float(
            os.getenv(
                f"{self.source_name.upper()}_SENTIMENT_NEUTRAL_BAND",
                str(neutral_band),
            )
        )
        self.symbol_aliases = symbol_aliases or DEFAULT_SYMBOL_ALIASES
        self.sentiment_table = sentiment_table
        self._classifier = None

    def _get_classifier(self):
        if self._classifier is not None:
            return self._classifier
        try:
            from transformers import pipeline as _pipeline
        except ImportError:
            _pipeline = None
        if _pipeline is None:
            raise RuntimeError(
                "transformers is not installed for sentiment analysis"
            )
        self._classifier = _pipeline(
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
            "source": self.source_name,
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
        for symbol, aliases in self.symbol_aliases.items():
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
        try:
            import mlflow as _mlflow
        except ImportError:
            return
        try:
            _mlflow.set_tracking_uri(
                os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
            )
            with _mlflow.start_run(
                run_name=f"{self.source_name}-headline-sentiment"
            ):
                _mlflow.log_param("source", self.source_name)
                _mlflow.log_param("tickers", ",".join(tickers))
                _mlflow.log_param(
                    "sentiment_label",
                    analysis["sentiment_label"],
                )
                _mlflow.log_param("model_name", analysis["model_name"])
                _mlflow.log_metric(
                    f"{self.source_name}_sentiment_score",
                    float(analysis["sentiment_score"]),
                )
                _mlflow.log_metric(
                    f"{self.source_name}_confidence_score",
                    float(analysis["confidence_score"]),
                )
        except Exception as exc:
            logger.warning(
                "%s MLflow logging failed: %s",
                self.source_name.upper(),
                exc,
            )

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
            logger.warning(
                "%s sentiment DB connection failed: %s",
                self.source_name.upper(),
                exc,
            )
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
                    f"""
                    INSERT INTO {self.sentiment_table} (
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
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
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
                        author or self.source_name,
                        0,
                        False,
                        self.source_name,
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
            logger.warning(
                "%s sentiment persistence failed: %s",
                self.source_name.upper(),
                exc,
            )
        finally:
            conn.close()

        return inserted

    def build_discord_message(
        self,
        headline: str,
        analysis: Dict[str, Any],
        tickers: Sequence[str],
    ) -> str:
        rendered_tickers = ", ".join(tickers) if tickers else "unmapped"
        return (
            f"{self.source_name.upper()} Headline: {headline}\n"
            f"Tickers: {rendered_tickers}\n"
            f"Sentiment: {analysis['sentiment_label']} "
            f"({analysis['sentiment_score']:.2f})"
        )


class WsjSentimentService(HeadlineSentimentService):
    def __init__(
        self,
        model_name: str | None = None,
        neutral_band: float = 0.15,
    ) -> None:
        super().__init__(
            source_name="wsj",
            model_name=model_name,
            neutral_band=neutral_band,
        )