import pandas as pd
from fastapi.testclient import TestClient

import Main
import rhea_bot
from rhea_bot import RheaBot, RheaConfig


class _FakeYFinance:
    @staticmethod
    def download(*_args, **_kwargs):
        rows = 200
        base = [100 + (i * 0.4) for i in range(rows)]
        return pd.DataFrame(
            {
                "Open": [value - 0.5 for value in base],
                "High": [value + 1.0 for value in base],
                "Low": [value - 1.0 for value in base],
                "Close": base,
                "Volume": [1_000_000 + (i * 1000) for i in range(rows)],
            }
        )


def _build_rhea_bot() -> RheaBot:
    return RheaBot(
        RheaConfig(
            id=12,
            name="Rhea",
            runtime_name="Rhea_Bot",
            fund="Mansa ADI",
            strategy="Intra-Day / Swing",
            screener_file="rhea_adi_swing.csv",
            universe="Aerospace_Defense_Industrials",
            timeframe="30m",
            position_size=1800.0,
            route_prefix="/rhea",
            health_endpoint="/rhea/health",
            analyze_endpoint="/rhea/analyze",
            trade_endpoint="/rhea/trade",
            airflow_dag_id="rhea_mansa_adi",
            airflow_schedule="20 8 * * 1-5",
            airflow_base_url="http://localhost:8080",
            airbyte_source="stocktwits",
            airbyte_source_config="airbyte/sources/stocktwits/rhea_mansa_config.json",
            airbyte_connection_id_env="RHEA_AIRBYTE_CONNECTION_ID",
            mlflow_experiment="Rhea_Mansa_ADI",
            mlflow_tracking_uri="http://localhost:5000",
            enable_mlflow_logging=False,
            fastapi_base_url="http://127.0.0.1:5001",
            dashboard_url="http://127.0.0.1:8501",
            enable_trading=False,
            buy_threshold=0.18,
            sell_threshold=-0.18,
            mysql_signal_table="rhea_trade_events",
            required_indicators=("FVFI", "ROVL"),
            broker_allowlist=("ibkr", "alpaca"),
            default_universe=("SIDU", "AXON", "NNE", "GD"),
        )
    )


def test_rhea_analysis_and_dry_run(monkeypatch):
    monkeypatch.setattr(rhea_bot, "yf", _FakeYFinance)

    bot = _build_rhea_bot()
    analysis = bot.analyze_ticker(
        "GD",
        headlines=["Defense contract award improves industrial demand"],
        log_to_mlflow=False,
    )

    assert analysis["ticker"] == "GD"
    assert analysis["action"] in {"BUY", "HOLD", "SELL"}
    assert "composite_score" in analysis

    trade_action = analysis["action"] if analysis["action"] != "HOLD" else "BUY"
    order = bot.execute_trade(
        "ibkr",
        "GD",
        trade_action,
        qty=3,
        dry_run=True,
    )
    assert order["status"] == "simulated"
    assert order["dry_run"] is True


def test_rhea_fastapi_routes(monkeypatch):
    monkeypatch.setattr(rhea_bot, "yf", _FakeYFinance)

    bot = _build_rhea_bot()

    monkeypatch.setattr(Main, "get_rhea_bot", lambda: bot)
    monkeypatch.setattr(Main, "RheaBot", RheaBot)

    client = TestClient(Main.app)

    status_response = client.get("/rhea/status")
    assert status_response.status_code == 200
    assert status_response.json()["name"] == "Rhea"
    assert "first_successful_ibkr_paper_trade" in status_response.json()

    health_response = client.get("/rhea/health")
    assert health_response.status_code == 200
    assert "dependencies" in health_response.json()

    analyze_response = client.post(
        "/rhea/analyze",
        json={
            "ticker": "GD",
            "news_headlines": ["Aerospace demand remains strong"],
        },
    )
    assert analyze_response.status_code == 200
    assert "composite_score" in analyze_response.json()

    trade_response = client.post(
        "/rhea/trade",
        json={
            "broker": "ibkr",
            "ticker": "GD",
            "action": "BUY",
            "qty": 2,
            "dry_run": True,
        },
    )
    assert trade_response.status_code == 200
    assert trade_response.json()["status"] == "simulated"


def test_rhea_execute_trade_marks_first_ibkr_paper_success(monkeypatch):
    bot = _build_rhea_bot()

    monkeypatch.setattr(
        bot,
        "_persist_trade_event",
        lambda *_args, **_kwargs: {
            "persisted": True,
            "table": "rhea_trade_events",
            "first_successful_ibkr_paper_trade": True,
            "successful_ibkr_paper_trade_count": 1,
            "first_successful_trade": {
                "id": 1,
                "ticker": "GD",
                "action": "BUY",
                "qty": 2.0,
                "status": "simulated",
                "created_at": "2026-04-22 09:30:00",
            },
        },
    )
    monkeypatch.setattr(
        bot,
        "_notify_first_successful_ibkr_paper_trade",
        lambda *_args, **_kwargs: True,
    )

    trade = bot.execute_trade(
        "ibkr",
        "GD",
        "BUY",
        qty=2,
        dry_run=True,
    )

    assert trade["first_successful_ibkr_paper_trade"] is True
    assert trade["milestone_discord_notified"] is True


def test_rhea_status_includes_trade_summary(monkeypatch):
    bot = _build_rhea_bot()

    monkeypatch.setattr(
        bot,
        "_fetch_trade_status_summary",
        lambda: {
            "latest_trade": {
                "id": 5,
                "broker": "ibkr",
                "ticker": "GD",
                "action": "BUY",
                "qty": 3.0,
                "mode": "paper",
                "status": "simulated",
                "discord_notified": True,
                "created_at": "2026-04-22 09:31:00",
            },
            "successful_ibkr_paper_trade_count": 1,
            "first_successful_ibkr_paper_trade": {
                "recognized": True,
                "trade": {
                    "id": 5,
                    "broker": "ibkr",
                    "ticker": "GD",
                    "action": "BUY",
                    "qty": 3.0,
                    "mode": "paper",
                    "status": "simulated",
                    "discord_notified": True,
                    "created_at": "2026-04-22 09:31:00",
                },
            },
        },
    )

    status = bot.status()

    assert status["successful_ibkr_paper_trade_count"] == 1
    assert status["first_successful_ibkr_paper_trade"]["recognized"] is True
    assert status["latest_trade"]["ticker"] == "GD"
