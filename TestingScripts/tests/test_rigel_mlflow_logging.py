import os
from pathlib import Path

import pandas as pd

import scripts.train_rigel_models as trm


class _DummyRun:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeMlflow:
    def __init__(self):
        self.params = {}
        self.metrics = {}
        self.artifacts = []
        self.experiments = []

    def set_tracking_uri(self, _uri):
        return None

    def set_experiment(self, name):
        self.experiments.append(name)

    def start_run(self, run_name=None):
        self.params["run_name"] = run_name
        return _DummyRun()

    def set_tag(self, _k, _v):
        return None

    def log_param(self, k, v):
        self.params[k] = v

    def log_metric(self, k, v):
        self.metrics[k] = v

    def log_artifact(self, path):
        self.artifacts.append(path)


def test_rigel_training_logs_to_mlflow(monkeypatch, tmp_path):
    monkeypatch.setattr(trm, "REST", lambda *args, **kwargs: object())

    fake_mlflow = _FakeMlflow()
    monkeypatch.setattr(trm, "MLFLOW_AVAILABLE", True)
    monkeypatch.setattr(trm, "mlflow", fake_mlflow)
    monkeypatch.setattr(trm, "LSTM_AVAILABLE", True)
    monkeypatch.setattr(trm, "XGB_AVAILABLE", True)
    monkeypatch.setattr(trm, "get_mlflow_tracking_uri", lambda: "file://" + str(tmp_path / "mlruns"))

    trainer = trm.RigelModelTrainer("k", "s")

    trainer.fetch_training_data = lambda symbol, days: pd.DataFrame({"close": [1.0, 1.1, 1.2]})
    trainer.prepare_features = lambda df: df
    trainer.create_labels = lambda df, lookahead=10: pd.Series([0] * len(df))
    trainer.train_lstm_model = lambda df, epochs=50: (object(), object(), {"lstm_test_accuracy": 0.91})
    trainer.train_xgboost_model = lambda df, n_estimators=100: (object(), {"xgb_test_accuracy": 0.88})

    artifact_file = tmp_path / "artifact.txt"
    artifact_file.write_text("ok", encoding="utf-8")
    trainer.save_models = lambda symbol, lstm_model, xgb_model, scaler: {
        "artifact": str(artifact_file)
    }

    trainer.train_symbol("EUR/USD", days=5, lstm_epochs=1, xgb_estimators=1, synthetic_data=True)

    assert "Rigel_FOREX_Training" in fake_mlflow.experiments
    assert fake_mlflow.params.get("symbol") == "EUR/USD"
    assert "bars_fetched" in fake_mlflow.metrics
    assert "lstm_test_accuracy" in fake_mlflow.metrics
    assert "xgb_test_accuracy" in fake_mlflow.metrics
    assert str(artifact_file) in fake_mlflow.artifacts
