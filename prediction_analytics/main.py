"""Orchestrator entrypoint for prediction analytics microservices."""
import asyncio
import logging

from prediction_analytics.config import settings
from prediction_analytics.services.kalshi_client import KalshiClient
from prediction_analytics.services.polymarket_client import PolymarketClient
from prediction_analytics.services.probability_engine import ProbabilityEngine
from prediction_analytics.services.sentiment_engine import SentimentEngine
from prediction_analytics.services.db import get_session_factory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_ingestion():
    await PolymarketClient().run()
    await KalshiClient().run()


def list_active_contracts(limit: int = 50):
    session_factory = get_session_factory()
    with session_factory() as session:
        rows = session.execute(
            "SELECT contract_id FROM mansa_quant.event_contracts WHERE status = 'OPEN' LIMIT :lim",
            {"lim": limit},
        ).fetchall()
        return [r[0] for r in rows]


async def run_probability_jobs(contracts):
    engine = ProbabilityEngine()
    for cid in contracts:
        await engine.compute_and_store(cid)


async def run_sentiment_stub(contracts):
    sentiment = SentimentEngine()
    for cid in contracts[:5]:
        await sentiment.store_signal(cid, "bullish momentum building", "stub-nlp")


async def main():
    logger.info("Starting prediction analytics pipeline")
    await run_ingestion()
    contracts = list_active_contracts()
    await run_probability_jobs(contracts)
    await run_sentiment_stub(contracts)
    logger.info("Pipeline completed")


if __name__ == "__main__":
    asyncio.run(main())
