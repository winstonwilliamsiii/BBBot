from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

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
        titan_orchestration_table="titan_orchestration_runs",
        mlflow_tracking_uri="http://localhost:5000",
        titan_model_uri="models:/TitanRiskModel/Production",
        airflow_base_url="http://localhost:8080",
        airbyte_base_url="http://localhost:8001",
        airbyte_connection_id=None,
        sentiment_table="sentiment_msgs",
        liquidity_buffer_threshold=0.20,
        liquidity_buffer_positive_delta=0.05,
        liquidity_buffer_negative_delta=0.10,
        sentiment_trade_bias_threshold=0.20,
        prediction_threshold=0.50,
        order_timeout_seconds=15.0,
        dry_run=True,
        enable_trading=False,
        strategy_name="Mansa Tech - Titan Bot",
        sequence_window=20,
    )


class _FakeMlflowRunLogger:
    def __init__(self):
        self.current_run = None
        self.tags = {}
        self.params = {}
        self.metrics = {}
        self.logged_dict = None
        self.logged_dict_path = None
        self.started_run_name = None

    def set_tracking_uri(self, _uri):
        return None

    def active_run(self):
        return self.current_run

    def start_run(self, run_name=None):
        self.started_run_name = run_name
        self.current_run = object()
        return self.current_run

    def set_tags(self, tags):
        self.tags.update(tags)

    def set_tag(self, key, value):
        self.tags[key] = value

    def log_params(self, params):
        self.params.update(params)

    def log_param(self, key, value):
        self.params[key] = value

    def log_metric(self, key, value):
        self.metrics[key] = value

    def log_dict(self, payload, path):
        self.logged_dict = payload
        self.logged_dict_path = path

    def end_run(self):
        self.current_run = None


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


def test_titan_config_loads_single_bot_profile_yaml(tmp_path, monkeypatch):
    config_file = tmp_path / "titan.yml"
    config_file.write_text(
        """
bot:
    name: Titan
    fund: Mansa Tech
    strategy: CNN with Deep Learning
strategy:
    label: Titan_Profile_Label
    screener_file: titan_profile.csv
    universe: Mag7+Tech
    position_size: 777
risk:
    max_pe: 22
execution:
    primary_client: alpaca_client
notification:
    discord:
        required_indicators:
            - FVFI
            - ROVL
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("BOT_CONFIG_PATH", str(config_file))
    monkeypatch.setenv("ACTIVE_BOT", "Titan")
    monkeypatch.delenv("TITAN_STRATEGY_NAME", raising=False)

    config = TitanConfig.from_env()

    assert config.active_bot_name == "Titan_Bot"
    assert config.strategy_name == "Titan_Profile_Label"
    assert config.screener_file == "titan_profile.csv"
    assert config.universe == "Mag7+Tech"
    assert config.position_size == 777.0
    assert config.risk_rules["max_pe"] == 22
    assert config.notification["discord"]["required_indicators"] == [
        "FVFI",
        "ROVL",
    ]


def test_titan_config_loads_single_bot_profile_from_directory(tmp_path, monkeypatch):
    profile_dir = tmp_path / "bots"
    profile_dir.mkdir()
    (profile_dir / "vega.yml").write_text(
        """
bot:
    name: Vega
    runtime_name: Vega_Bot
    fund: Mansa Retail
    strategy: Breakout Strategy
strategy:
    screener_file: vega_profile.csv
    universe: Retail_Breakouts
    position_size: 222
risk:
    min_volume: 1200000
notification:
    discord:
        required_indicators:
            - FVFI
            - ROVL
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("BOT_CONFIG_PATH", str(profile_dir))
    monkeypatch.setenv("ACTIVE_BOT", "Vega")
    monkeypatch.delenv("TITAN_STRATEGY_NAME", raising=False)

    config = TitanConfig.from_env()

    assert config.active_bot_name == "Vega_Bot"
    assert config.strategy_name == "Breakout Strategy"
    assert config.screener_file == "vega_profile.csv"
    assert config.position_size == 222.0
    assert config.risk_rules["min_volume"] == 1200000
    assert config.notification["discord"]["required_indicators"] == [
        "FVFI",
        "ROVL",
    ]


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


def test_extract_mlflow_feature_metrics_includes_titan_context():
    bot = TitanBot(_build_config())

    metrics = bot._extract_mlflow_feature_metrics(
        prediction_features={
            "rsi_14_t_minus_1": 42.0,
            "rsi_14_t_minus_0": 55.0,
            "bb_bandwidth_t_minus_0": 0.18,
            "bb_percent_b_t_minus_0": 0.61,
            "sentiment_score_t_minus_0": 0.22,
            "liquidity_ratio_t_minus_0": 0.35,
        },
        sentiment_score=0.22,
        liquidity_ratio=0.35,
        effective_buffer=0.27,
    )

    assert metrics["titan_rsi_cycle_current"] == 55.0
    assert metrics["titan_volatility_bandwidth"] == 0.18
    assert metrics["titan_bollinger_percent_b"] == 0.61
    assert metrics["titan_liquidity_buffer_adjustment"] == pytest.approx(0.07)
    assert metrics["titan_rsi_cycle_span"] == pytest.approx(13.0)


def test_start_mlflow_trade_run_logs_schema_and_artifact(monkeypatch):
    bot = TitanBot(_build_config())
    fake_mlflow = _FakeMlflowRunLogger()

    monkeypatch.setattr("scripts.mansa_titan_bot.mlflow", fake_mlflow)
    monkeypatch.setattr(bot, "_mlflow_tracking_is_reachable", lambda: True)

    started = bot._start_mlflow_trade_run(
        symbol="NVDA",
        side="buy",
        qty=3.0,
        prediction_features={
            "rsi_14_t_minus_0": 58.0,
            "bb_bandwidth_t_minus_0": 0.14,
            "bb_percent_b_t_minus_0": 0.73,
        },
        sentiment_score=0.18,
        liquidity_ratio=0.41,
        effective_buffer=0.24,
    )

    assert started is True
    assert fake_mlflow.started_run_name == "Titan_Bot-NVDA-buy"
    assert fake_mlflow.tags["benchmark_peers"] == "Orion,Rigel,Dogon"
    assert fake_mlflow.params["model_registry_uri"] == "models:/TitanRiskModel/Production"
    assert fake_mlflow.params["feature_schema_version"] == "titan_cnn_sequence_v2"
    assert fake_mlflow.metrics["titan_rsi_cycle_current"] == 58.0
    assert fake_mlflow.logged_dict_path == "titan_decision_context.json"
    assert fake_mlflow.logged_dict["symbol"] == "NVDA"


def test_log_mlflow_trade_result_logs_confidence_and_outcome(monkeypatch):
    bot = TitanBot(_build_config())
    fake_mlflow = _FakeMlflowRunLogger()
    fake_mlflow.current_run = object()

    monkeypatch.setattr("scripts.mansa_titan_bot.mlflow", fake_mlflow)

    bot._log_mlflow_trade_result(
        prediction=1,
        probability=0.84,
        status="submitted",
        order_id="oid-123",
        ml_gate_passed=True,
        liquidity_gate_passed=True,
        effective_buffer=0.23,
        liquidity_ratio=0.44,
    )

    assert fake_mlflow.metrics["titan_prediction_confidence"] == pytest.approx(0.84)
    assert fake_mlflow.metrics["titan_trade_approved"] == 1.0
    assert fake_mlflow.metrics["titan_trade_blocked"] == 0.0
    assert fake_mlflow.metrics["titan_ml_gate_passed"] == 1.0
    assert fake_mlflow.tags["trade_status"] == "submitted"
    assert fake_mlflow.tags["alpaca_order_id"] == "oid-123"


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
        "get_recent_orchestration_runs",
        lambda limit=50: pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2026-01-01T09:00:00"]),
                "bot_name": ["Titan"],
                "task_name": ["execution"],
                "status": ["submitted"],
                "decision_reason": ["scheduled-cycle"],
                "candidates_considered": [1],
                "candidates_executed": [1],
                "traded_symbols": ["NVDA"],
                "detail": ["submitted"],
            }
        ),
    )
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
    assert not snapshot["orchestration_df"].empty


def test_log_orchestration_run_executes_insert(monkeypatch):
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

    bot.log_orchestration_run(
        bot_name="Titan",
        task_name="execution",
        status="submitted",
        detail="submitted",
        traded_symbols=["NVDA"],
    )

    assert executed_queries
    assert "INSERT INTO titan_orchestration_runs" in executed_queries[0][0]


def test_execute_trade_uses_config_position_size_when_qty_missing(monkeypatch):
    config = _build_config()
    config.position_size = 1234.0
    bot = TitanBot(config)

    captured = {}

    class FakeOrder:
        id = "order-123"

    monkeypatch.setattr(bot, "_fetch_sentiment_score", lambda _symbol: 0.3)
    monkeypatch.setattr(bot, "_current_liquidity_ratio", lambda: 0.4)
    monkeypatch.setattr(
        bot,
        "_build_prediction_features",
        lambda *args, **kwargs: [0.1, 0.2],
    )
    monkeypatch.setattr(bot, "titan_predict", lambda _features: (1, 0.9))
    monkeypatch.setattr(
        bot,
        "titan_guard",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(bot, "log_trade", lambda *args, **kwargs: None)
    monkeypatch.setattr(bot, "_notify_discord", lambda _msg: None)
    bot.api = object()
    monkeypatch.setattr(
        bot,
        "_submit_alpaca_order",
        lambda **kwargs: captured.update(kwargs) or FakeOrder(),
    )

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

    monkeypatch.setattr(bot, "_fetch_sentiment_score", lambda _symbol: 0.0)
    monkeypatch.setattr(bot, "_current_liquidity_ratio", lambda: 0.4)
    monkeypatch.setattr(
        bot,
        "_build_prediction_features",
        lambda *args, **kwargs: [0.2],
    )
    monkeypatch.setattr(bot, "titan_predict", lambda _features: (1, 0.9))
    monkeypatch.setattr(
        bot,
        "titan_guard",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        bot,
        "log_trade",
        lambda *args, **kwargs: log_calls.append((args, kwargs)),
    )

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


def test_titan_predict_reads_pyfunc_dataframe(monkeypatch):
    bot = TitanBot(_build_config())

    class FakeModel:
        def predict(self, payload):
            assert isinstance(payload, pd.DataFrame)
            return pd.DataFrame(
                {
                    "prediction": [1],
                    "probability": [0.87],
                }
            )

    monkeypatch.setattr(bot, "load_model", lambda: FakeModel())

    prediction, probability = bot.titan_predict({"rsi_14_t_minus_0": 55.0})

    assert prediction == 1
    assert probability == 0.87


def test_build_prediction_features_uses_neutral_fallback(monkeypatch):
    bot = TitanBot(_build_config())

    monkeypatch.setattr(bot, "_fetch_sentiment_score", lambda _symbol: 0.25)
    monkeypatch.setattr(bot, "_current_liquidity_ratio", lambda: 0.40)
    def fake_fetch_close_history(_symbol):
        bot._last_market_data_source["NVDA"] = "cache"
        return pd.Series(dtype="float64")

    monkeypatch.setattr(bot, "_fetch_close_history", fake_fetch_close_history)

    payload = bot._build_prediction_features("NVDA", [])

    assert isinstance(payload, dict)
    assert payload["sentiment_score_t_minus_0"] == 0.25
    assert payload["liquidity_ratio_t_minus_0"] == 0.40
    assert bot._last_prediction_feature_metadata["NVDA"] == {
        "market_data_source": "cache",
        "feature_source": "neutral",
        "close_history_points": 0,
        "feature_timeseries_points": 0,
    }


def test_build_prediction_features_records_sequence_metadata(monkeypatch):
    bot = TitanBot(_build_config())
    close_history = pd.Series(np.linspace(100.0, 140.0, 80))

    monkeypatch.setattr(bot, "_fetch_sentiment_score", lambda _symbol: 0.10)
    monkeypatch.setattr(bot, "_current_liquidity_ratio", lambda: 0.35)

    def fake_fetch_close_history(_symbol):
        bot._last_market_data_source["NVDA"] = "cache"
        return close_history

    monkeypatch.setattr(bot, "_fetch_close_history", fake_fetch_close_history)

    payload = bot._build_prediction_features("NVDA", [])

    assert isinstance(payload, dict)
    assert bot._last_prediction_feature_metadata["NVDA"][
        "market_data_source"
    ] == "cache"
    assert bot._last_prediction_feature_metadata["NVDA"][
        "feature_source"
    ] == "sequence"
    assert bot._last_prediction_feature_metadata["NVDA"][
        "close_history_points"
    ] == 80
    assert bot._last_prediction_feature_metadata["NVDA"][
        "feature_timeseries_points"
    ] >= bot.config.sequence_window


def test_coerce_prediction_output_handles_numpy_array():
    bot = TitanBot(_build_config())

    prediction, probability = bot._coerce_prediction_output(np.array([0.63]))

    assert prediction == 1
    assert probability == 0.63


def test_effective_liquidity_threshold_adjusts_with_sentiment():
    bot = TitanBot(_build_config())

    assert bot._effective_liquidity_threshold(
        sentiment_score=-0.6,
    ) == pytest.approx(0.30)
    assert bot._effective_liquidity_threshold(
        sentiment_score=0.6,
    ) == pytest.approx(0.15)


def test_execute_from_screener_continues_after_blocked_candidate(monkeypatch):
    config = _build_config()
    config.dry_run = False
    config.enable_trading = True
    bot = TitanBot(config)

    monkeypatch.setattr(
        "scripts.mansa_titan_bot.load_bot_trade_candidates",
        lambda _bot_name: [
            {"symbol": "AAPL", "fundamentals": {}, "raw": {}},
            {"symbol": "NVDA", "fundamentals": {}, "raw": {}},
            {"symbol": "MSFT", "fundamentals": {}, "raw": {}},
        ],
    )

    bot._rank_candidates = lambda candidates: candidates

    statuses = {
        "AAPL": {"status": "blocked", "notes": "ml gate"},
        "NVDA": {"status": "submitted", "notes": "submitted"},
        "MSFT": {"status": "submitted", "notes": "submitted"},
    }

    class FakeOrder:
        id = "order-1"

    def fake_execute_trade(symbol, side, qty, features, fundamentals=None):
        bot._last_trade_outcome = {
            "symbol": symbol,
            **statuses[symbol],
            "probability": 0.9,
            "sentiment_score": 0.25,
            "effective_buffer_threshold": 0.15,
        }
        if statuses[symbol]["status"] == "submitted":
            return FakeOrder()
        return None

    monkeypatch.setattr(bot, "execute_trade", fake_execute_trade)

    results = bot.execute_from_screener(side="buy", max_trades=1)

    assert [row["symbol"] for row in results] == ["AAPL", "NVDA"]
    assert results[0]["status"] == "blocked"
    assert results[1]["status"] == "submitted"


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


def test_load_bot_trade_candidates_from_single_bot_profile(tmp_path):
    csv_file = tmp_path / "titan_profile.csv"
    csv_file.write_text(
        "Ticker,volume,pe\nNVDA,5000000,21\n",
        encoding="utf-8",
    )

    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    (profile_dir / "titan.yml").write_text(
        f"""
bot:
    name: Titan
    fund: Mansa Tech
    strategy: CNN with Deep Learning
strategy:
    screener_file: {csv_file.name}
    universe: Mag7+Tech
    position_size: 1000
risk:
    max_pe: 25
""".strip(),
        encoding="utf-8",
    )

    candidates = load_bot_trade_candidates(
        "Titan",
        config_path=profile_dir,
    )

    assert len(candidates) == 1
    assert candidates[0]["symbol"] == "NVDA"
    assert candidates[0]["fundamentals"]["pe"] == 21.0


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
        bot._last_trade_outcome = {
            "symbol": symbol,
            "status": "simulated",
            "notes": "dry-run",
        }
        return None

    monkeypatch.setattr(bot, "execute_trade", fake_execute_trade)

    results = bot.execute_from_screener(side="buy", max_trades=1)

    assert len(results) == 1
    assert results[0]["symbol"] == "AAPL"
    assert seen == ["AAPL"]
