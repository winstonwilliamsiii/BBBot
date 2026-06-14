from __future__ import annotations

from datetime import datetime

import pandas as pd

import scripts.bot_mlflow_benchmark as benchmark
import scripts.dogon_bot as dogon_bot
from scripts.rigel_forex_bot import ForexConfig, RigelForexBot


class _DummyRun:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeMlflow:
    def __init__(self):
        self.tags = {}
        self.params = {}
        self.metrics = {}
        self.experiments = []
        self.run_name = None
        self.artifact_payload = None
        self.artifact_path = None

    def set_tracking_uri(self, _uri):
        return None

    def set_experiment(self, name):
        self.experiments.append(name)

    def start_run(self, run_name=None):
        self.run_name = run_name
        return _DummyRun()

    def set_tags(self, tags):
        self.tags.update(tags)

    def log_params(self, params):
        self.params.update(params)

    def log_metric(self, key, value):
        self.metrics[key] = value

    def log_dict(self, payload, path):
        self.artifact_payload = payload
        self.artifact_path = path


def test_log_bot_benchmark_run_logs_expected_payload(monkeypatch):
    fake_mlflow = _FakeMlflow()
    monkeypatch.setattr(benchmark, "mlflow", fake_mlflow)

    success = benchmark.log_bot_benchmark_run(
        bot_name="Dogon",
        experiment_name="Dogon_Runtime_Benchmark",
        run_name="Dogon-ready",
        payload={"confidence": 0.82, "signal_count": 2.0},
        strategy_label="ETF raw strategy",
        discipline_mode="raw_strategy",
        extra_params={"model_used": "gbt"},
        extra_tags={"trade_status": "ready"},
        tracking_uri="file:///tmp/mlruns",
    )

    assert success is True
    assert "Dogon_Runtime_Benchmark" in fake_mlflow.experiments
    assert fake_mlflow.tags["bot"] == "Dogon"
    assert fake_mlflow.tags["benchmark_group"] == benchmark.BENCHMARK_GROUP
    assert fake_mlflow.params["model_used"] == "gbt"
    assert fake_mlflow.metrics["confidence"] == 0.82
    assert fake_mlflow.artifact_path == "dogon_benchmark_run.json"


def test_rigel_run_cycle_logs_skipped_session(monkeypatch):
    config = ForexConfig()
    bot = RigelForexBot(config)
    calls = []

    monkeypatch.setattr(bot, "is_trading_session", lambda: False)
    monkeypatch.setattr(
        "scripts.rigel_forex_bot.log_bot_benchmark_run",
        lambda **kwargs: calls.append(kwargs) or True,
    )

    result = bot.run_cycle()

    assert result["status"] == "skipped_outside_session"
    assert calls
    assert calls[0]["bot_name"] == "Rigel"
    assert calls[0]["extra_tags"]["trade_status"] == "skipped_outside_session"


def test_dogon_run_cycle_logs_benchmark_payload(monkeypatch):
    calls = []

    monkeypatch.setattr(
        dogon_bot,
        "_load_training_summary",
        lambda _path: {"best_model": "gbt", "artifacts": {}},
    )
    monkeypatch.setattr(
        dogon_bot,
        "_fetch_prices",
        lambda symbols, days=90: pd.DataFrame(
            {
                "close_SPY": [100.0, 101.0, 102.0, 103.0],
                "close_QQQ": [200.0, 201.0, 202.0, 203.0],
            },
            index=pd.date_range("2026-01-01", periods=4, freq="D"),
        ),
    )
    monkeypatch.setattr(
        dogon_bot,
        "_build_features",
        lambda prices, symbols: pd.DataFrame(
            {"SPY_ret_1": [0.1], "QQQ_ret_1": [0.2]},
            index=[datetime(2026, 1, 4)],
        ),
    )
    monkeypatch.setattr(
        dogon_bot,
        "_run_gbt_inference",
        lambda path, features: {
            "model_used": "gbt",
            "signal": "buy",
            "predicted_class": 1,
            "confidence": 0.77,
            "raw_probability": 0.77,
        },
    )
    monkeypatch.setattr(
        "scripts.dogon_bot.log_bot_benchmark_run",
        lambda **kwargs: calls.append(kwargs) or True,
    )

    result = dogon_bot.run_cycle()

    assert result["status"] == "ready"
    assert result["model_used"] == "gbt"
    assert calls
    assert calls[0]["bot_name"] == "Dogon"
    assert calls[0]["payload"]["confidence"] == 0.77