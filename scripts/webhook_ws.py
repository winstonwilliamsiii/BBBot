from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from scripts.sentiment_utils import (
    WsjSentimentService,
    notify_discord,
    parse_published_at,
)


router = APIRouter(tags=["sentiment"])


class WSJWebhookPayload(BaseModel):
    headline: str = Field(min_length=1)
    tickers: Optional[List[str]] = None
    article_id: Optional[str] = None
    article_url: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[str] = None


@lru_cache(maxsize=1)
def get_wsj_sentiment_service() -> WsjSentimentService:
    return WsjSentimentService()


@router.post("/wsj-webhook")
async def wsj_webhook(payload: WSJWebhookPayload):
    service = get_wsj_sentiment_service()

    try:
        analysis = service.analyze_headline(payload.headline)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    tickers = service.infer_tickers(payload.headline, payload.tickers)
    stored_rows = service.store_sentiment_message(
        tickers=tickers,
        headline=payload.headline,
        analysis=analysis,
        article_id=payload.article_id,
        article_url=payload.article_url,
        published_at=parse_published_at(payload.published_at),
        author=payload.author,
    )
    service.log_to_mlflow(analysis, tickers)
    notify_discord(
        service.build_discord_message(
            payload.headline,
            analysis,
            tickers,
        )
    )

    return {
        "status": "processed",
        "source": "wsj",
        "tickers": tickers,
        "stored_rows": stored_rows,
        "analysis": analysis,
    }