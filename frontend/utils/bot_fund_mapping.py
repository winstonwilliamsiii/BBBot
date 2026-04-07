"""Shared bot/fund/strategy catalog for Bentley dashboard surfaces."""

from __future__ import annotations

from typing import Dict, List


BOT_CATALOG: List[Dict[str, str]] = [
    {
        "bot": "Titan",
        "fund": "Mansa Tech",
        "strategy": "CNN with Deep Learning",
    },
    {
        "bot": "Vega",
        "display_bot": "Vega_Bot",
        "fund": "Mansa_Retail",
        "strategy": "Breakout Strategy",
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
        "strategy": "Pending",
    },
    {
        "bot": "Dione",
        "fund": "Mansa Options",
        "strategy": "Put Call Parity",
    },
    {
        "bot": "Dogon",
        "fund": "Mansa ETF",
        "strategy": "Portfolio Optimizer",
    },
    {
        "bot": "Rigel",
        "fund": "Mansa FOREX",
        "strategy": "Mean Reversion",
    },
    {
        "bot": "Orion",
        "fund": "Mansa Minerals",
        "strategy": "GoldRSI Strategy",
    },
    {
        "bot": "Rhea",
        "fund": "Mansa ADI",
        "strategy": "Intra-Day / Swing",
    },
    {
        "bot": "Jupicita",
        "fund": "Mansa_Smalls",
        "strategy": "Pairs Trading",
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
    rows: List[Dict[str, str]] = []
    for row in BOT_CATALOG:
        display_row = dict(row)
        if row.get("display_bot"):
            display_row["bot"] = row["display_bot"]
        rows.append(display_row)
    return rows
