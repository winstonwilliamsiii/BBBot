"""Focused simulation validation for the Bentley ML trading DAG."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from types import ModuleType

import pandas as pd


DAG_PATH = (
    Path(__file__).resolve().parents[1] / "airflow" / "dags" / "bentleybot_trading_dag.py"
)


class FakeTaskInstance:
    def __init__(self) -> None:
        self.values: dict[tuple[str | None, str], object] = {}
        self.current_task_id: str | None = None

    def xcom_push(self, key: str, value: object) -> None:
        self.values[(self.current_task_id, key)] = value

    def xcom_pull(self, task_ids: str, key: str) -> object:
        return self.values[(task_ids, key)]


def _load_dag_module(monkeypatch):
    class StubDag:
        current: "StubDag | None" = None

        def __init__(self, **_: object) -> None:
            self.task_ids: list[str] = []

        def __enter__(self):
            StubDag.current = self
            return self

        def __exit__(self, *_: object) -> None:
            StubDag.current = None

    class StubPythonOperator:
        def __init__(self, task_id: str, python_callable: object) -> None:
            self.task_id = task_id
            self.python_callable = python_callable
            assert StubDag.current is not None
            StubDag.current.task_ids.append(task_id)

        def __rshift__(self, other: object) -> object:
            return other

    airflow = ModuleType("airflow")
    airflow.DAG = StubDag
    operators = ModuleType("airflow.operators")
    python = ModuleType("airflow.operators.python")
    python.PythonOperator = StubPythonOperator
    monkeypatch.setitem(sys.modules, "airflow", airflow)
    monkeypatch.setitem(sys.modules, "airflow.operators", operators)
    monkeypatch.setitem(sys.modules, "airflow.operators.python", python)

    spec = importlib.util.spec_from_file_location("bentleybot_trading_dag_test", DAG_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_simulation_pipeline_never_invokes_a_broker(monkeypatch, tmp_path, caplog):
    dag_module = _load_dag_module(monkeypatch)
    caplog.set_level("INFO", logger=dag_module.__name__)
    timestamps = pd.date_range("2026-01-01", periods=30, freq="D")
    prices = pd.DataFrame({"Close": range(100, 130)}, index=timestamps)
    monkeypatch.setenv("TRADING_SIMULATION_MODE", "true")
    monkeypatch.setenv("BENTLEY_TRADING_WORK_DIR", str(tmp_path))
    monkeypatch.setitem(sys.modules, "yfinance", SimpleNamespace(download=lambda *args, **kwargs: prices))

    task_instance = FakeTaskInstance()
    for task_id, task in (
        ("fetch_market_data", dag_module.fetch_market_data),
        ("generate_signals", dag_module.generate_signals),
        ("execute_trades", dag_module.execute_trades),
        ("calculate_performance", dag_module.calculate_performance),
        ("send_daily_report", dag_module.send_daily_report),
    ):
        task_instance.current_task_id = task_id
        task(task_instance=task_instance)

    trades = pd.read_csv(tmp_path / "simulated_trades.csv")
    report = task_instance.values[("send_daily_report", "daily_report")]
    assert set(dag_module.dag.task_ids) == {
        "fetch_market_data",
        "generate_signals",
        "execute_trades",
        "calculate_performance",
        "send_daily_report",
    }
    assert (trades["status"] == "simulated").all()
    assert (trades["execution_mode"] == "SIMULATION MODE").all()
    assert report["status"] == "sent"
    assert report["metrics"]["real_executions"] == 0
    assert "SIMULATION MODE" in caplog.text
