"""Shared bot-to-fund mapping for Bentley dashboard surfaces."""

from __future__ import annotations

from typing import Dict, List


BOT_FUND_ALLOCATIONS: Dict[str, str] = {
    "Titan": "Mansa_Tech",
    "Rigel": "Mansa_FOREX",
    "Dogon": "Mansa_ETF",
    "Orion": "Mansa_Minerals",
}


def get_bot_fund_rows() -> List[Dict[str, str]]:
    """Return bot/fund rows in display order."""
    return [
        {
            "bot": bot_name,
            "fund": fund_name,
        }
        for bot_name, fund_name in BOT_FUND_ALLOCATIONS.items()
    ]
