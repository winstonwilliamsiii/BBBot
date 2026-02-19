from types import SimpleNamespace

import pandas as pd

from scripts.mansa_titan_bot import TitanBot, TitanConfig


def _build_config() -> TitanConfig:
    return TitanConfig(
        alpaca_api_key=None,
        alpaca_secret_key=None,
        alpaca_base_url="https://paper-api.alpaca.markets",
        discord_webhook_url=None,
        mysql_host="127.0.0.1",
        mysql_port=3307,
        mysql_user="root",
        mysql_password="root",
        mysql_database="mansa_bot",
        titan_trades_table="titan_trades",
        titan_service_table="titan_service_health",
        mlflow_tracking_uri="http://localhost:5000",
        titan_model_uri="models:/TitanRiskModel/Production",
        airflow_base_url="http://localhost:8080",
        airbyte_base_url="http://localhost:8001",
        airbyte_connection_id=None,
        liquidity_buffer_threshold=0.20,
        prediction_threshold=0.50,
        dry_run=True,
        enable_trading=False,
        strategy_name="Mansa Tech - Titan Bot",
    )


def test_titan_config_defaults(monkeypatch):
    for key in [
        "MYSQL_HOST",
        "MYSQL_PORT",
        "MYSQL_DATABASE",
        "TITAN_DRY_RUN",
        "TITAN_ENABLE_TRADING",
    ]:
        monkeypatch.delenv(key, raising=False)

    config = TitanConfig.from_env()
    assert config.mysql_host == "127.0.0.1"
    assert config.mysql_port == 3307
    assert config.mysql_database == "mansa_bot"
    assert config.dry_run is True
    assert config.enable_trading is False


def test_titan_guard_blocks_on_low_buffer(monkeypatch):
    bot = TitanBot(_build_config())
    monkeypatch.setattr(
        bot,
        "get_account_snapshot",
        lambda: {"cash": 100.0, "equity": 1000.0},
    )
    assert bot.titan_guard() is False


def test_collect_service_health_returns_three_rows(monkeypatch):
    bot = TitanBot(_build_config())

    def fake_http_health(url, _timeout=8):
        return "healthy", f"ok:{url}"

    monkeypatch.setattr(bot, "_http_health", fake_http_health)
    monkeypatch.setattr(bot, "log_service_health", lambda rows: None)

    health = bot.collect_service_health()
    assert len(health) == 3
    assert {row["service_name"] for row in health} == {
        "mlflow",
        "airflow",
        "airbyte",
    }


def test_log_trade_executes_insert(monkeypatch):
    bot = TitanBot(_build_config())

    executed_queries = []

    class FakeCursor:
        def execute(self, query, params=None):
            executed_queries.append((query, params))

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def commit(self):
            return None

        def close(self):
            return None

    fake_mysql = SimpleNamespace(
        connector=SimpleNamespace(connect=lambda **kwargs: FakeConnection())
    )

    monkeypatch.setattr("scripts.mansa_titan_bot.mysql", fake_mysql)

    bot.log_trade("NVDA", "buy", 5, "MARKET", "submitted")
    assert executed_queries
    assert "INSERT INTO titan_trades" in executed_queries[0][0]


def test_dashboard_snapshot_counts(monkeypatch):
    bot = TitanBot(_build_config())

    trades_df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime([
                "2026-01-01T10:00:00",
                "2026-01-01T11:00:00",
                "2026-01-01T12:00:00",
            ]),
            "symbol": ["NVDA", "MSFT", "AMZN"],
            "side": ["buy", "sell", "buy"],
            "qty": [1, 1, 1],
            "status": ["submitted", "simulated", "blocked"],
            "prediction_probability": [0.82, 0.65, 0.31],
        }
    )

    monkeypatch.setattr(bot, "get_recent_trades", lambda limit=100: trades_df)
    monkeypatch.setattr(
        bot,
        "collect_service_health",
        lambda: [
            {
                "service_name": "mlflow",
                "status": "healthy",
                "endpoint": "x",
                "detail": "ok",
            }
        ],
    )

    snapshot = bot.dashboard_snapshot()

    assert snapshot["total_trades"] == 3
    assert snapshot["submitted_trades"] == 1
    assert snapshot["simulated_trades"] == 1
    assert snapshot["blocked_trades"] == 1
    assert snapshot["avg_prediction_probability"] > 0
