"""Shared bot/fund/strategy catalog for Bentley dashboard surfaces."""

from __future__ import annotations

from typing import Dict, List


BOT_CATALOG: List[Dict[str, str]] = [
    {
        "bot": "Titan",
        "fund": "Mansa Tech",
        "strategy": "ML Ensemble - CNN with Deep Learning approaches for further accuracy",
    },
    {
        "bot": "Vega",
        "fund": "Mansa Retail",
        "strategy": "Multi-timeframe Strategy",
    },
    {
        "bot": "Draco",
        "fund": "Mansa Money Bag",
        "strategy": "Sentiment Analyzer",
    },
    {
        "bot": "Altair",
        "fund": "Mansa AI",
        "strategy": "News Trading",
    },
    {
        "bot": "Procryon",
        "fund": "Crypto Fund",
        "strategy": "Crypto Arbitrage",
    },
    {
        "bot": "Hydra",
        "fund": "Mansa Health",
        "strategy": "Momentum Strategy",
    },
    {
        "bot": "Triton",
        "fund": "Mansa Transportation",
        "strategy": "Portfolio Optimizer",
    },
    {
        "bot": "Dione",
        "fund": "Mansa Diversify Dominance",
        "strategy": "Technical Indicator Bot",
    },
    {
        "bot": "Dogon",
        "fund": "Mansa ETF",
        "strategy": "USD/COP Short",
    },
    {
        "bot": "Cephei",
        "fund": "Mansa Shorts",
        "strategy": "Mean Reversion",
    },
    {
        "bot": "Rigel",
        "fund": "Mansa FOREX",
        "strategy": "GoldRSI Strategy",
    },
    {
        "bot": "Orion",
        "fund": "Mansa Minerals",
        "strategy": "Options Strategy",
    },
    {
        "bot": "Rhea",
        "fund": "Mansa Real Estate",
        "strategy": "Pairs Trading",
    },
    {
        "bot": "Jupicita",
        "fund": "Mansa_Smalls",
        "strategy": "Small-cap alpha forecasting with liquidity-aware execution",
    },
]


BOT_FUND_ALLOCATIONS: Dict[str, str] = {
    row["bot"]: row["fund"] for row in BOT_CATALOG
}


def get_bot_fund_rows() -> List[Dict[str, str]]:
    """Return bot/fund rows in display order."""
    return [{"bot": row["bot"], "fund": row["fund"]} for row in BOT_CATALOG]


def get_bot_catalog_rows() -> List[Dict[str, str]]:
    """Return full bot catalog rows in display order."""
    return [dict(row) for row in BOT_CATALOG]
