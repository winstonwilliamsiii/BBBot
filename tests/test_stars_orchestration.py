from frontend.utils.bot_fund_mapping import (
    BOT_FUND_ALLOCATIONS,
    get_bot_catalog_rows,
    get_bot_fund_rows,
)
from scripts import stars_orchestration


def test_bot_fund_allocations_present():
    assert BOT_FUND_ALLOCATIONS["Titan"] == "Mansa Tech"
    assert BOT_FUND_ALLOCATIONS["Rigel"] == "Mansa FOREX"
    assert BOT_FUND_ALLOCATIONS["Dogon"] == "Mansa ETF"
    assert BOT_FUND_ALLOCATIONS["Orion"] == "Mansa Minerals"


def test_get_bot_fund_rows_count():
    rows = get_bot_fund_rows()
    assert len(rows) >= 4
    bot_names = {row["bot"] for row in rows}
    assert {"Titan", "Rigel", "Dogon", "Orion"}.issubset(bot_names)


def test_vega_catalog_row_uses_updated_display_values():
    rows = get_bot_catalog_rows()
    vega_row = next(row for row in rows if row["bot"] == "Vega_Bot")
    assert vega_row["fund"] == "Mansa_Retail"
    assert vega_row["strategy"] == "Breakout Strategy"


def test_run_fund_bot_rigel_ready_or_placeholder():
    result = stars_orchestration.run_fund_bot("Rigel")
    assert result["bot"] == "Rigel"
    assert result["fund"] == "Mansa FOREX"
    assert result["status"] in {"ready", "placeholder"}


def test_evaluate_titan_gate_with_mock(monkeypatch):
    class FakeTitanBot:
        def __init__(self, _cfg):
            pass

        def ensure_database_tables(self):
            return None

        def log_orchestration_run(self, **kwargs):
            return None

        def titan_guard(self, buffer_threshold=None):
            return buffer_threshold != 0.99

    monkeypatch.setattr(stars_orchestration, "TitanBot", FakeTitanBot)

    approved = stars_orchestration.evaluate_titan_gate(buffer_threshold=0.2)
    blocked = stars_orchestration.evaluate_titan_gate(buffer_threshold=0.99)

    assert approved["status"] == "approved"
    assert blocked["status"] == "blocked"


def test_run_fund_bot_titan_executes_cycle(monkeypatch):
    class FakeTitanBot:
        def __init__(self, _cfg):
            self.config = type(
                "Config",
                (),
                {
                    "active_bot_name": "Titan_Bot",
                    "dry_run": False,
                    "enable_trading": True,
                },
            )()

        def ensure_database_tables(self):
            return None

        def _rank_candidates(self, candidates):
            return candidates

        def execute_from_screener(self, max_trades=None):
            return [{"symbol": "NVDA", "executed": True}]

        def get_recent_trade_activity(self, since=None, symbols=None, limit=100):
            import pandas as pd

            return pd.DataFrame(
                {
                    "timestamp": pd.to_datetime(["2026-04-06T07:00:00"]),
                    "symbol": ["NVDA"],
                    "status": ["submitted"],
                    "notes": ["submitted"],
                }
            )

        def log_orchestration_run(self, **kwargs):
            return None

    monkeypatch.setattr(stars_orchestration, "TitanBot", FakeTitanBot)
    monkeypatch.setattr(
        stars_orchestration,
        "load_bot_trade_candidates",
        lambda _bot_name: [{"symbol": "NVDA"}],
    )

    result = stars_orchestration.run_fund_bot("Titan")

    assert result["bot"] == "Titan"
    assert result["task"] == "execution"
    assert result["status"] == "submitted"
    assert result["candidates_considered"] == 1
