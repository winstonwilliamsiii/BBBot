from types import SimpleNamespace

import pandas as pd

from scripts.mansa_titan_bot import TitanBot, TitanConfig
from scripts.load_screener_csv import load_bot_trade_candidates


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
        "BOT_CONFIG_PATH",
        "ACTIVE_BOT",
        "BOT_NAME",
    ]:
        monkeypatch.delenv(key, raising=False)

    config = TitanConfig.from_env()
    assert config.mysql_host == "127.0.0.1"
    assert config.mysql_port == 3307
    assert config.mysql_database == "mansa_bot"
    assert config.dry_run is True
    assert config.enable_trading is False


def test_titan_config_loads_active_bot_profile_from_yaml(tmp_path, monkeypatch):
        config_file = tmp_path / "fundamentals_bots.yml"
        config_file.write_text(
                """
active_bot: Vega_Bot
bots:
    Titan_Bot:
        screener_file: titan_tech_fundamentals.csv
        universe: Mag7+Tech
        position_size: 5000
        strategy_label: Tech_Fundamentals_Mag7
        risk_rules:
            min_volume: 5000000
            max_pe: 40
            min_roe: 15
            max_debt_to_equity: 0.8
    Vega_Bot:
        screener_file: vega_fundamentals.csv
        universe: Retail_Fundamentals
        position_size: 1000
        strategy_label: Retail_Fundamentals
        risk_rules:
            min_volume: 1000000
            max_pe: 25
            min_roe: 12
            max_debt_to_equity: 0.5
            min_dividend_yield: 2
""".strip(),
                encoding="utf-8",
        )

        monkeypatch.setenv("BOT_CONFIG_PATH", str(config_file))
        monkeypatch.delenv("ACTIVE_BOT", raising=False)
        monkeypatch.delenv("BOT_NAME", raising=False)
        monkeypatch.delenv("TITAN_STRATEGY_NAME", raising=False)

        config = TitanConfig.from_env()

        assert config.active_bot_name == "Vega_Bot"
        assert config.strategy_name == "Retail_Fundamentals"
        assert config.screener_file == "vega_fundamentals.csv"
        assert config.universe == "Retail_Fundamentals"
        assert config.position_size == 1000.0
        assert config.risk_rules["max_pe"] == 25


def test_titan_config_switches_bot_with_active_bot_env(tmp_path, monkeypatch):
        config_file = tmp_path / "fundamentals_bots.yml"
        config_file.write_text(
                """
active_bot: Vega_Bot
bots:
    Titan_Bot:
        screener_file: titan_tech_fundamentals.csv
        universe: Mag7+Tech
        position_size: 5000
        strategy_label: Tech_Fundamentals_Mag7
        risk_rules:
            min_volume: 5000000
    Vega_Bot:
        screener_file: vega_fundamentals.csv
        universe: Retail_Fundamentals
        position_size: 1000
        strategy_label: Retail_Fundamentals
        risk_rules:
            min_volume: 1000000
""".strip(),
                encoding="utf-8",
        )

        monkeypatch.setenv("BOT_CONFIG_PATH", str(config_file))
        monkeypatch.setenv("ACTIVE_BOT", "Titan_Bot")
        monkeypatch.delenv("TITAN_STRATEGY_NAME", raising=False)

        config = TitanConfig.from_env()

        assert config.active_bot_name == "Titan_Bot"
        assert config.strategy_name == "Tech_Fundamentals_Mag7"
        assert config.position_size == 5000.0


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


def test_execute_trade_uses_config_position_size_when_qty_missing(monkeypatch):
    config = _build_config()
    config.position_size = 1234.0
    bot = TitanBot(config)

    captured = {}

    class FakeOrder:
        id = "order-123"

    class FakeApi:
        def submit_order(self, **kwargs):
            captured.update(kwargs)
            return FakeOrder()

    bot.api = FakeApi()

    monkeypatch.setattr(bot, "titan_predict", lambda _features: (1, 0.9))
    monkeypatch.setattr(bot, "titan_guard", lambda buffer_threshold=None: True)
    monkeypatch.setattr(bot, "log_trade", lambda *args, **kwargs: None)
    monkeypatch.setattr(bot, "_notify_discord", lambda _msg: None)

    config.dry_run = False
    config.enable_trading = True

    result = bot.execute_trade(
        symbol="NVDA",
        side="buy",
        qty=None,
        features=[0.1, 0.2],
    )

    assert result is not None
    assert captured["qty"] == 1234.0


def test_execute_trade_blocks_on_configured_risk_rules(monkeypatch):
    config = _build_config()
    config.risk_rules = {"max_pe": 20}
    bot = TitanBot(config)

    log_calls = []

    monkeypatch.setattr(bot, "titan_predict", lambda _features: (1, 0.9))
    monkeypatch.setattr(bot, "titan_guard", lambda buffer_threshold=None: True)
    monkeypatch.setattr(bot, "log_trade", lambda *args, **kwargs: log_calls.append((args, kwargs)))

    result = bot.execute_trade(
        symbol="AAPL",
        side="buy",
        qty=5,
        features=[0.2],
        fundamentals={"pe": 35},
    )

    assert result is None
    assert log_calls
    args, kwargs = log_calls[0]
    assert args[4] == "blocked"
    assert "Risk rule blocked trade" in kwargs["notes"]


def test_load_bot_trade_candidates_extracts_fundamentals(tmp_path):
    csv_file = tmp_path / "vega.csv"
    csv_file.write_text(
        "Ticker,volume,pe,roe,debt_to_equity,dividend_yield\n"
        "AAPL,1200000,22,18,0.4,1.5\n"
        "MSFT,1500000,30,20,0.3,0.8\n",
        encoding="utf-8",
    )

    config_file = tmp_path / "fundamentals_bots.yml"
    config_file.write_text(
        f"""
active_bot: Vega_Bot
bots:
  Vega_Bot:
    screener_file: {csv_file.name}
    universe: Retail_Fundamentals
    position_size: 1000
    strategy_label: Retail_Fundamentals
    risk_rules:
      min_volume: 1000000
""".strip(),
        encoding="utf-8",
    )

    candidates = load_bot_trade_candidates("Vega_Bot", config_path=config_file)

    assert len(candidates) == 2
    assert candidates[0]["symbol"] == "AAPL"
    assert candidates[0]["fundamentals"]["pe"] == 22.0
    assert candidates[0]["fundamentals"]["volume"] == 1200000.0


def test_execute_from_screener_passes_fundamentals(monkeypatch):
    bot = TitanBot(_build_config())

    monkeypatch.setattr(
        "scripts.mansa_titan_bot.load_bot_trade_candidates",
        lambda _bot_name: [
            {
                "symbol": "AAPL",
                "fundamentals": {"pe": 18.0, "volume": 2000000.0},
                "raw": {},
            }
        ],
    )

    captured = {}

    def fake_execute_trade(symbol, side, qty, features, fundamentals=None):
        captured["symbol"] = symbol
        captured["side"] = side
        captured["qty"] = qty
        captured["fundamentals"] = fundamentals
        return None

    monkeypatch.setattr(bot, "execute_trade", fake_execute_trade)

    results = bot.execute_from_screener(side="buy", max_trades=1)

    assert len(results) == 1
    assert captured["symbol"] == "AAPL"
    assert captured["qty"] is None
    assert captured["fundamentals"]["pe"] == 18.0


def test_execute_from_screener_manual_selection(monkeypatch):
    config = _build_config()
    config.selection_mode = "manual"
    config.manual_symbols = ["MSFT", "NVDA"]
    bot = TitanBot(config)

    monkeypatch.setattr(
        "scripts.mansa_titan_bot.load_bot_trade_candidates",
        lambda _bot_name: [
            {"symbol": "AAPL", "fundamentals": {}, "raw": {}},
            {"symbol": "NVDA", "fundamentals": {}, "raw": {}},
            {"symbol": "MSFT", "fundamentals": {}, "raw": {}},
        ],
    )

    seen = []

    def fake_execute_trade(symbol, side, qty, features, fundamentals=None):
        seen.append(symbol)
        return None

    monkeypatch.setattr(bot, "execute_trade", fake_execute_trade)

    results = bot.execute_from_screener(side="buy", max_trades=2)

    assert [row["symbol"] for row in results] == ["MSFT", "NVDA"]
    assert seen == ["MSFT", "NVDA"]


def test_execute_from_screener_technical_mode_without_api_keeps_csv_order(monkeypatch):
    config = _build_config()
    config.selection_mode = "technical"
    bot = TitanBot(config)
    bot.api = None

    monkeypatch.setattr(
        "scripts.mansa_titan_bot.load_bot_trade_candidates",
        lambda _bot_name: [
            {"symbol": "AAPL", "fundamentals": {}, "raw": {}},
            {"symbol": "MSFT", "fundamentals": {}, "raw": {}},
        ],
    )

    seen = []

    def fake_execute_trade(symbol, side, qty, features, fundamentals=None):
        seen.append(symbol)
        return None

    monkeypatch.setattr(bot, "execute_trade", fake_execute_trade)

    results = bot.execute_from_screener(side="buy", max_trades=1)

    assert len(results) == 1
    assert results[0]["symbol"] == "AAPL"
    assert seen == ["AAPL"]
