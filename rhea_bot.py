from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    import requests
except ImportError:
    requests = None

try:
    import yaml
except ImportError:
    yaml = None

try:
    import mlflow
except ImportError:
    mlflow = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    from sklearn.ensemble import RandomForestClassifier
except ImportError:
    RandomForestClassifier = None

try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None

try:
    import torch
    import torch.nn as nn
except ImportError:
    torch = None
    nn = None

from bbbot1_pipeline.db import get_mysql_connection
from bbbot1_pipeline.mlflow_config import get_mlflow_tracking_uri

try:
    from scripts.load_screener_csv import (
        load_bot_config,
        load_screener_rows,
        resolve_screener_path,
    )
except ImportError:
    load_bot_config = None
    load_screener_rows = None
    resolve_screener_path = None


REPO_ROOT = Path(__file__).resolve().parent
RHEA_PROFILE_PATH = REPO_ROOT / "bentley-bot" / "config" / "bots" / "rhea.yml"
RHEA_SCREENER_PATH = REPO_ROOT / "bentley-bot" / "config" / "rhea_adi_swing.csv"
RHEA_AIRBYTE_CONFIG = "airbyte/sources/stocktwits/rhea_mansa_config.json"

RHEA_FALLBACK_UNIVERSE = (
    "SIDU",
    "AXON",
    "NNE",
    "GD",
    "NOC",
    "KTOS",
    "HON",
    "FLY",
    "IR",
    "XTIA",
)

FALLBACK_NORMALIZED_CONFIG = {
    "bot_name": "Rhea_Bot",
    "bot_display_name": "Rhea",
    "fund_name": "Mansa ADI",
    "strategy_label": "Rhea_Intraday_Swing",
    "strategy_name": "Intra-Day / Swing",
    "module": "rhea_bot.py",
    "screener_file": "rhea_adi_swing.csv",
    "universe": "Aerospace_Defense_Industrials",
    "timeframe": "30m",
    "position_size": 1800,
    "execution": {
        "primary_client": "ibkr_client",
        "mode": "paper",
        "enabled": False,
        "order_type": "market",
    },
    "risk_rules": {
        "max_holding_days": 5,
        "max_daily_loss_pct": 1.25,
        "max_open_positions": 5,
    },
    "notification": {
        "discord": {
            "required_indicators": ["FVFI", "ROVL"],
        }
    },
}


class RheaTorchModel(nn.Module if nn is not None else object):
    def __init__(self, input_dim: int, cnn_channels: int = 16, transformer_heads: int = 4):
        if nn is None:
            raise RuntimeError("torch is not installed")
        super().__init__()
        self.cnn = nn.Conv1d(
            in_channels=input_dim,
            out_channels=cnn_channels,
            kernel_size=3,
            padding=1,
        )
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=cnn_channels,
            nhead=transformer_heads,
            batch_first=False,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=2)
        self.fc = nn.Linear(cnn_channels, 1)

    def forward(self, x):
        x = self.cnn(x)
        x = x.permute(2, 0, 1)
        x = self.transformer(x)
        x = x.mean(dim=0)
        return torch.sigmoid(self.fc(x))


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).strip().replace(",", ""))
    except (AttributeError, TypeError, ValueError):
        return default


def _clamp(value: float, minimum: float = -1.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _load_rhea_profile() -> tuple[dict[str, Any], dict[str, Any]]:
    if (
        load_bot_config is None
        or yaml is None
        or not RHEA_PROFILE_PATH.exists()
    ):
        return dict(FALLBACK_NORMALIZED_CONFIG), {
            "services": {
                "airbyte": {
                    "source_config": RHEA_AIRBYTE_CONFIG,
                    "connection_id_env": "RHEA_AIRBYTE_CONNECTION_ID",
                },
                "airflow": {
                    "dag_id": "rhea_mansa_adi",
                    "schedule": "20 8 * * 1-5",
                },
                "mlflow": {
                    "experiment": "Rhea_Mansa_ADI",
                    "tracking_uri_env": "MLFLOW_TRACKING_URI",
                },
            },
            "notification": {
                "discord": {
                    "required_indicators": ["FVFI", "ROVL"],
                }
            },
            "execution": {
                "enabled": False,
                "mode": "paper",
            },
        }

    normalized = load_bot_config("Rhea", config_path=RHEA_PROFILE_PATH)
    with RHEA_PROFILE_PATH.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    return normalized, raw if isinstance(raw, dict) else {}


def _resolve_rhea_screener_path(normalized: dict[str, Any]) -> Path:
    if resolve_screener_path is not None:
        return resolve_screener_path(normalized, config_path=RHEA_PROFILE_PATH)
    return RHEA_SCREENER_PATH


def _load_rhea_screener_rows(csv_path: Path) -> list[dict[str, str]]:
    if pd is not None and csv_path.exists():
        frame = pd.read_csv(csv_path)
        return frame.to_dict(orient="records")
    if load_screener_rows is not None:
        return load_screener_rows(csv_path)
    return []


@dataclass
class RheaConfig:
    id: int = 12
    name: str = "Rhea"
    runtime_name: str = "Rhea_Bot"
    fund: str = "Mansa ADI"
    strategy: str = "Intra-Day / Swing"
    screener_file: str = "rhea_adi_swing.csv"
    universe: str = "Aerospace_Defense_Industrials"
    timeframe: str = "30m"
    position_size: float = 1800.0
    route_prefix: str = "/rhea"
    health_endpoint: str = "/rhea/health"
    analyze_endpoint: str = "/rhea/analyze"
    trade_endpoint: str = "/rhea/trade"
    airflow_dag_id: str = "rhea_mansa_adi"
    airflow_schedule: str = "20 8 * * 1-5"
    airflow_base_url: str = "http://localhost:8080"
    airbyte_source: str = "stocktwits"
    airbyte_source_config: str = RHEA_AIRBYTE_CONFIG
    airbyte_connection_id_env: str = "RHEA_AIRBYTE_CONNECTION_ID"
    mlflow_experiment: str = "Rhea_Mansa_ADI"
    mlflow_tracking_uri: str = "http://localhost:5000"
    enable_mlflow_logging: bool = True
    fastapi_base_url: str = "http://localhost:5001"
    dashboard_url: str = "http://localhost:8501"
    enable_trading: bool = False
    buy_threshold: float = 0.18
    sell_threshold: float = -0.18
    mysql_signal_table: str = "rhea_trade_events"
    required_indicators: tuple[str, ...] = ("FVFI", "ROVL")
    broker_allowlist: tuple[str, ...] = ("ibkr", "alpaca")
    default_universe: tuple[str, ...] = field(default_factory=lambda: RHEA_FALLBACK_UNIVERSE)

    @classmethod
    def from_env(cls) -> "RheaConfig":
        normalized, raw = _load_rhea_profile()
        bot_meta = raw.get("bot") if isinstance(raw.get("bot"), dict) else {}
        execution = raw.get("execution") if isinstance(raw.get("execution"), dict) else {}
        strategy_meta = raw.get("strategy") if isinstance(raw.get("strategy"), dict) else {}
        services = raw.get("services") if isinstance(raw.get("services"), dict) else {}
        fastapi_service = services.get("fastapi") if isinstance(services.get("fastapi"), dict) else {}
        airflow_service = services.get("airflow") if isinstance(services.get("airflow"), dict) else {}
        airbyte_service = services.get("airbyte") if isinstance(services.get("airbyte"), dict) else {}
        mlflow_service = services.get("mlflow") if isinstance(services.get("mlflow"), dict) else {}
        notification = raw.get("notification") if isinstance(raw.get("notification"), dict) else {}
        discord = notification.get("discord") if isinstance(notification.get("discord"), dict) else {}

        screener_path = _resolve_rhea_screener_path(normalized)
        screener_rows = _load_rhea_screener_rows(screener_path)
        universe = [
            str(row.get("Symbol") or row.get("Ticker") or "").strip().upper()
            for row in screener_rows
            if str(row.get("Symbol") or row.get("Ticker") or "").strip()
        ]
        if not universe:
            universe = list(RHEA_FALLBACK_UNIVERSE)

        return cls(
            id=int(bot_meta.get("id") or 12),
            name=str(bot_meta.get("name") or "Rhea"),
            runtime_name=str(bot_meta.get("runtime_name") or "Rhea_Bot"),
            fund=str(bot_meta.get("fund") or "Mansa ADI"),
            strategy=str(bot_meta.get("strategy") or "Intra-Day / Swing"),
            screener_file=str(normalized.get("screener_file") or strategy_meta.get("screener_file") or "rhea_adi_swing.csv"),
            universe=str(normalized.get("universe") or strategy_meta.get("universe") or "Aerospace_Defense_Industrials"),
            timeframe=str(normalized.get("timeframe") or strategy_meta.get("timeframe") or "30m"),
            position_size=float(normalized.get("position_size") or strategy_meta.get("position_size") or 1800),
            route_prefix=str(fastapi_service.get("route_prefix") or "/rhea"),
            health_endpoint=str(fastapi_service.get("health_endpoint") or "/rhea/health"),
            analyze_endpoint=str(fastapi_service.get("analyze_endpoint") or "/rhea/analyze"),
            trade_endpoint=str(fastapi_service.get("trade_endpoint") or "/rhea/trade"),
            airflow_dag_id=str(os.getenv("RHEA_AIRFLOW_DAG_ID", airflow_service.get("dag_id") or "rhea_mansa_adi")),
            airflow_schedule=str(airflow_service.get("schedule") or "20 8 * * 1-5"),
            airflow_base_url=str(os.getenv("AIRFLOW_BASE_URL", "http://localhost:8080")).rstrip("/"),
            airbyte_source=str(airbyte_service.get("source") or "stocktwits"),
            airbyte_source_config=str(os.getenv("RHEA_AIRBYTE_SOURCE_CONFIG", airbyte_service.get("source_config") or RHEA_AIRBYTE_CONFIG)),
            airbyte_connection_id_env=str(airbyte_service.get("connection_id_env") or "RHEA_AIRBYTE_CONNECTION_ID"),
            mlflow_experiment=str(os.getenv("RHEA_MLFLOW_EXPERIMENT", mlflow_service.get("experiment") or "Rhea_Mansa_ADI")),
            mlflow_tracking_uri=str(
                os.getenv(
                    str(mlflow_service.get("tracking_uri_env") or "MLFLOW_TRACKING_URI"),
                    get_mlflow_tracking_uri(),
                )
            ).rstrip("/"),
            enable_mlflow_logging=_truthy(os.getenv("RHEA_ENABLE_MLFLOW", "true")),
            fastapi_base_url=str(os.getenv("RHEA_FASTAPI_BASE_URL", os.getenv("CONTROL_CENTER_API_URL", "http://localhost:5001"))).rstrip("/"),
            dashboard_url=str(os.getenv("BENTLEY_UI_URL", os.getenv("STREAMLIT_PUBLIC_URL", "http://localhost:8501"))).rstrip("/"),
            enable_trading=_truthy(os.getenv("RHEA_ENABLE_TRADING", execution.get("enabled", False))),
            buy_threshold=_to_float(os.getenv("RHEA_BUY_THRESHOLD"), 0.18),
            sell_threshold=_to_float(os.getenv("RHEA_SELL_THRESHOLD"), -0.18),
            mysql_signal_table=str(os.getenv("RHEA_MYSQL_SIGNAL_TABLE", "rhea_trade_events")),
            required_indicators=tuple(discord.get("required_indicators") or ("FVFI", "ROVL")),
            broker_allowlist=tuple(
                token.strip().lower()
                for token in os.getenv("RHEA_BROKER_ALLOWLIST", "ibkr,alpaca").split(",")
                if token.strip()
            ),
            default_universe=tuple(universe),
        )


class RheaAnalyzeRequest(BaseModel):
    ticker: str = Field(min_length=1)
    news_headlines: list[str] = Field(default_factory=list)


class RheaTradeRequest(BaseModel):
    broker: str = Field(default="ibkr", min_length=1)
    ticker: str = Field(min_length=1)
    action: str = Field(min_length=1)
    qty: float = Field(gt=0)
    dry_run: bool = True


class RheaFeatureRequest(BaseModel):
    features: list[float] = Field(min_length=1)


class RheaBot:
    def __init__(self, config: Optional[RheaConfig] = None):
        self.config = config or RheaConfig.from_env()
        self.last_analysis: dict[str, Any] = {}
        self._rf_model = None
        self._xgb_model = None
        self._torch_model = None
        self._train_scaffold_models()

    def _dependency_status(self) -> dict[str, bool]:
        return {
            "numpy": np is not None,
            "pandas": pd is not None,
            "requests": requests is not None,
            "yfinance": yf is not None,
            "mlflow": mlflow is not None,
            "sklearn": RandomForestClassifier is not None,
            "xgboost": XGBClassifier is not None,
            "torch": torch is not None,
            "mysql": True,
        }

    def _sanitize_ticker(self, ticker: str) -> str:
        normalized = str(ticker or "").strip().upper()
        if not normalized:
            raise ValueError("Ticker is required")
        return normalized

    def _train_scaffold_models(self) -> None:
        if np is None:
            return
        rng = np.random.default_rng(42)
        X_dummy = rng.random((160, 8))
        y_dummy = (X_dummy[:, 0] + X_dummy[:, 1] * 0.7 + X_dummy[:, 2] * 0.2 > 0.95).astype(int)

        if RandomForestClassifier is not None:
            self._rf_model = RandomForestClassifier(n_estimators=80, random_state=42)
            self._rf_model.fit(X_dummy, y_dummy)

        if XGBClassifier is not None:
            self._xgb_model = XGBClassifier(
                use_label_encoder=False,
                eval_metric="logloss",
                n_estimators=90,
                max_depth=4,
                learning_rate=0.08,
            )
            self._xgb_model.fit(X_dummy, y_dummy)

        if torch is not None:
            try:
                self._torch_model = RheaTorchModel(input_dim=8, cnn_channels=16, transformer_heads=4)
                self._torch_model.eval()
            except Exception:
                self._torch_model = None

    def _fetch_price_history(self, ticker: str) -> Any:
        if yf is None or pd is None:
            return pd.DataFrame() if pd is not None else None
        history = yf.download(
            ticker,
            period="6mo",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        if history is None:
            return pd.DataFrame()
        return history.tail(160)

    def _technical_indicators(self, ticker: str) -> dict[str, Any]:
        if pd is None or np is None:
            return {
                "sma_20": 0.0,
                "ema_20": 0.0,
                "bollinger_upper": 0.0,
                "bollinger_lower": 0.0,
                "adi": 0.0,
                "history_points": 0,
            }

        history = self._fetch_price_history(ticker)
        if history is None or history.empty:
            return {
                "sma_20": 0.0,
                "ema_20": 0.0,
                "bollinger_upper": 0.0,
                "bollinger_lower": 0.0,
                "adi": 0.0,
                "history_points": 0,
            }

        close = history["Close"].astype(float)
        high = history["High"].astype(float)
        low = history["Low"].astype(float)
        volume = history["Volume"].fillna(0).astype(float)

        sma = float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else float(close.iloc[-1])
        ema = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
        std20 = float(close.rolling(20).std().iloc[-1]) if len(close) >= 20 else 0.0
        bollinger_upper = sma + (2.0 * std20)
        bollinger_lower = sma - (2.0 * std20)

        money_flow_multiplier = (((close - low) - (high - close)) / (high - low).replace(0, np.nan)).fillna(0.0)
        money_flow_volume = money_flow_multiplier * volume
        adi = float(money_flow_volume.cumsum().iloc[-1])

        return {
            "sma_20": round(sma, 4),
            "ema_20": round(ema, 4),
            "bollinger_upper": round(float(bollinger_upper), 4),
            "bollinger_lower": round(float(bollinger_lower), 4),
            "adi": round(adi, 4),
            "history_points": int(len(history)),
            "last_close": round(float(close.iloc[-1]), 4),
        }

    def _sentiment_score(self, headlines: list[str]) -> float:
        if not headlines:
            return 0.0
        positive = {
            "contract",
            "award",
            "growth",
            "upgrade",
            "defense",
            "aerospace",
            "demand",
            "expansion",
        }
        negative = {
            "cut",
            "downgrade",
            "delay",
            "investigation",
            "miss",
            "slowdown",
            "weak",
        }
        scores = []
        for headline in headlines:
            tokens = {
                token.strip(" ,.!?;:-_()[]{}\"").lower()
                for token in str(headline).split()
                if token
            }
            if not tokens:
                continue
            score = (len(tokens & positive) - len(tokens & negative)) / max(len(tokens), 1)
            scores.append(_clamp(score * 10.0))
        if not scores:
            return 0.0
        return round(sum(scores) / len(scores), 4)

    def _torch_signal(self, features: list[float]) -> float:
        if self._torch_model is None or torch is None:
            return 0.0
        try:
            tensor = torch.tensor(features, dtype=torch.float32).view(1, len(features), 1)
            score = float(self._torch_model(tensor).item())
            return _clamp((score - 0.5) * 2.0)
        except Exception:
            return 0.0

    def analyze_ticker(self, ticker: str, headlines: Optional[list[str]] = None, log_to_mlflow: Optional[bool] = None) -> dict[str, Any]:
        symbol = self._sanitize_ticker(ticker)
        technical = self._technical_indicators(symbol)
        sentiment_score = self._sentiment_score(headlines or [])

        price_trend = 0.0
        if technical.get("last_close") and technical.get("sma_20"):
            price_trend = _clamp((technical["last_close"] - technical["sma_20"]) / max(technical["sma_20"], 1e-6))

        adi_signal = _clamp(technical.get("adi", 0.0) / 1_000_000.0)
        feature_vector = [
            technical.get("last_close", 0.0),
            technical.get("sma_20", 0.0),
            technical.get("ema_20", 0.0),
            technical.get("bollinger_upper", 0.0),
            technical.get("bollinger_lower", 0.0),
            technical.get("adi", 0.0),
            sentiment_score,
            price_trend,
        ]
        scale = max(max(abs(v) for v in feature_vector), 1.0)
        normalized_features = [float(v) / scale for v in feature_vector]

        rf_vote = 0.0
        if self._rf_model is not None and np is not None:
            rf_vote = float(self._rf_model.predict(np.array(normalized_features).reshape(1, -1))[0])
            rf_vote = 1.0 if rf_vote > 0 else -1.0

        xgb_vote = 0.0
        if self._xgb_model is not None and np is not None:
            xgb_vote = float(self._xgb_model.predict(np.array(normalized_features).reshape(1, -1))[0])
            xgb_vote = 1.0 if xgb_vote > 0 else -1.0

        torch_vote = self._torch_signal(normalized_features)

        composite_score = round(
            (price_trend * 0.30)
            + (adi_signal * 0.20)
            + (sentiment_score * 0.20)
            + (rf_vote * 0.10)
            + (xgb_vote * 0.10)
            + (torch_vote * 0.10),
            4,
        )

        action = "HOLD"
        if composite_score >= self.config.buy_threshold:
            action = "BUY"
        elif composite_score <= self.config.sell_threshold:
            action = "SELL"

        analysis = {
            "ticker": symbol,
            "fund": self.config.fund,
            "strategy": self.config.strategy,
            "universe": self.config.universe,
            "timeframe": self.config.timeframe,
            "position_size": self.config.position_size,
            "required_indicators": list(self.config.required_indicators),
            "technical": technical,
            "sentiment": {
                "score": sentiment_score,
                "headline_count": len(headlines or []),
            },
            "model_stack": {
                "random_forest_vote": rf_vote,
                "xgboost_vote": xgb_vote,
                "torch_vote": round(torch_vote, 4),
            },
            "composite_score": composite_score,
            "buy_threshold": self.config.buy_threshold,
            "sell_threshold": self.config.sell_threshold,
            "action": action,
            "data_pipeline": {
                "airflow_dag_id": self.config.airflow_dag_id,
                "airflow_schedule": self.config.airflow_schedule,
                "mlflow_experiment": self.config.mlflow_experiment,
                "mlflow_tracking_uri": self.config.mlflow_tracking_uri,
                "mysql_signal_table": self.config.mysql_signal_table,
                "airbyte_source_config": self.config.airbyte_source_config,
            },
        }
        self.last_analysis = analysis

        should_log = self.config.enable_mlflow_logging if log_to_mlflow is None else bool(log_to_mlflow)
        if should_log:
            analysis["mlflow"] = self.log_signal_run(analysis)

        return analysis

    def bootstrap_demo_state(self) -> dict[str, Any]:
        ticker = self.config.default_universe[0] if self.config.default_universe else "GD"
        headlines = [
            "Defense contract award boosts aerospace order backlog",
            "Industrial production growth supports mid-cap suppliers",
        ]
        return self.analyze_ticker(ticker, headlines=headlines, log_to_mlflow=False)

    def _persist_trade_event(self, trade_result: dict[str, Any], analysis: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.config.mysql_signal_table} (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        bot_name VARCHAR(64) NOT NULL,
                        fund_name VARCHAR(128) NOT NULL,
                        broker VARCHAR(32) NOT NULL,
                        ticker VARCHAR(32) NOT NULL,
                        action VARCHAR(16) NOT NULL,
                        qty DECIMAL(18, 6) NOT NULL,
                        mode VARCHAR(16) NOT NULL,
                        status VARCHAR(32) NOT NULL,
                        discord_notified TINYINT(1) NOT NULL DEFAULT 0,
                        trade_payload_json JSON,
                        analysis_payload_json JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
                cursor.execute(
                    f"""
                    INSERT INTO {self.config.mysql_signal_table} (
                        bot_name,
                        fund_name,
                        broker,
                        ticker,
                        action,
                        qty,
                        mode,
                        status,
                        discord_notified,
                        trade_payload_json,
                        analysis_payload_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.config.name,
                        self.config.fund,
                        str(trade_result.get("broker", "")),
                        str(trade_result.get("ticker", "")),
                        str(trade_result.get("action", "")),
                        float(trade_result.get("qty", 0.0)),
                        str(trade_result.get("mode", "paper")),
                        str(trade_result.get("status", "")),
                        1 if bool(trade_result.get("discord_notified", False)) else 0,
                        json.dumps(trade_result),
                        json.dumps(analysis or self.last_analysis or {}),
                    ),
                )
            conn.commit()
            conn.close()
            return {"persisted": True, "table": self.config.mysql_signal_table}
        except Exception as exc:
            return {"persisted": False, "table": self.config.mysql_signal_table, "error": str(exc)}

    def execute_trade(self, broker: str, ticker: str, action: str, qty: float = 1.0, dry_run: Optional[bool] = None) -> dict[str, Any]:
        symbol = self._sanitize_ticker(ticker)
        normalized_action = str(action or "").strip().upper()
        if normalized_action not in {"BUY", "SELL"}:
            raise ValueError("Action must be BUY or SELL")
        if qty <= 0:
            raise ValueError("Quantity must be positive")

        normalized_broker = str(broker or "ibkr").strip().lower()
        if normalized_broker not in self.config.broker_allowlist:
            raise ValueError(f"Broker must be one of: {', '.join(self.config.broker_allowlist)}")

        effective_dry_run = True if dry_run is None else bool(dry_run)
        status = "simulated" if effective_dry_run else "dry_run"

        result = {
            "broker": normalized_broker,
            "ticker": symbol,
            "action": normalized_action,
            "qty": float(qty),
            "mode": "paper",
            "status": status,
            "dry_run": effective_dry_run,
            "reason": "Rhea order flow is integrated for dashboard, MySQL trade persistence, and Discord notifications; execution remains dry-run by default",
            "airflow_dag_id": self.config.airflow_dag_id,
            "mlflow_experiment": self.config.mlflow_experiment,
            "required_indicators": list(self.config.required_indicators),
        }

        discord_notified = False
        try:
            from frontend.utils.discord_notify import notify_trade

            notify_trade(
                bot_name=self.config.name,
                symbol=symbol,
                side=normalized_action,
                qty=float(qty),
                status=result["status"],
                mode="paper",
                broker=normalized_broker,
                fund_name=self.config.fund,
            )
            discord_notified = True
        except Exception:
            discord_notified = False

        result["discord_notified"] = discord_notified
        result["persistence"] = self._persist_trade_event(result, analysis=self.last_analysis)
        return result

    def predict_xgboost(self, features: list[float]) -> dict[str, Any]:
        if self._xgb_model is None or np is None:
            return {
                "model": "XGBoost",
                "available": False,
                "reason": "xgboost or numpy unavailable",
            }
        arr = np.array(features, dtype=float).reshape(1, -1)
        prediction = int(self._xgb_model.predict(arr)[0])
        return {
            "model": "XGBoost",
            "available": True,
            "features": features,
            "prediction": prediction,
        }

    def predict_random_forest(self, features: list[float]) -> dict[str, Any]:
        if self._rf_model is None or np is None:
            return {
                "model": "RandomForest",
                "available": False,
                "reason": "scikit-learn or numpy unavailable",
            }
        arr = np.array(features, dtype=float).reshape(1, -1)
        prediction = int(self._rf_model.predict(arr)[0])
        return {
            "model": "RandomForest",
            "available": True,
            "features": features,
            "prediction": prediction,
        }

    def airbyte_source_config(self) -> dict[str, Any]:
        config_path = REPO_ROOT / self.config.airbyte_source_config
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                payload["config_path"] = str(config_path.relative_to(REPO_ROOT)).replace("\\", "/")
                return payload
        return {
            "tickers": list(self.config.default_universe),
            "user_agent": "Mozilla/5.0 (compatible; RheaBot/1.0)",
            "config_path": self.config.airbyte_source_config,
        }

    def check_airflow(self) -> dict[str, Any]:
        if requests is None:
            return {
                "reachable": False,
                "url": self.config.airflow_base_url,
                "dag_id": self.config.airflow_dag_id,
                "schedule": self.config.airflow_schedule,
                "error": "requests is not installed",
            }

        base_url = self.config.airflow_base_url.rstrip("/")
        last_error = "Airflow health endpoint did not respond"
        for path in ("/health", "/api/v1/health"):
            url = f"{base_url}{path}"
            try:
                response = requests.get(url, timeout=2)
                if response.ok:
                    return {
                        "reachable": True,
                        "url": url,
                        "status_code": response.status_code,
                        "dag_id": self.config.airflow_dag_id,
                        "schedule": self.config.airflow_schedule,
                    }
            except requests.RequestException as exc:
                last_error = str(exc)
        return {
            "reachable": False,
            "url": base_url,
            "dag_id": self.config.airflow_dag_id,
            "schedule": self.config.airflow_schedule,
            "error": last_error,
        }

    def check_mlflow(self) -> dict[str, Any]:
        tracking_uri = self.config.mlflow_tracking_uri
        if mlflow is None:
            return {
                "reachable": False,
                "tracking_uri": tracking_uri,
                "reason": "mlflow is not installed",
            }

        try:
            mlflow.set_tracking_uri(tracking_uri)
            if tracking_uri.startswith(("http://", "https://")):
                if requests is None:
                    return {
                        "reachable": False,
                        "tracking_uri": tracking_uri,
                        "experiment": self.config.mlflow_experiment,
                        "error": "requests is not installed",
                    }
                response = requests.get(f"{tracking_uri.rstrip('/')}/health", timeout=2)
                response.raise_for_status()
            client = mlflow.tracking.MlflowClient()
            experiments = client.search_experiments(max_results=5)
            return {
                "reachable": True,
                "tracking_uri": tracking_uri,
                "experiment": self.config.mlflow_experiment,
                "experiment_count": len(experiments),
            }
        except Exception as exc:
            return {
                "reachable": False,
                "tracking_uri": tracking_uri,
                "experiment": self.config.mlflow_experiment,
                "error": str(exc),
            }

    def check_mysql(self) -> dict[str, Any]:
        try:
            connection = get_mysql_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT DATABASE() AS db_name, VERSION() AS version")
                record = cursor.fetchone() or {}
            connection.close()
            return {
                "reachable": True,
                "database": record.get("db_name"),
                "version": record.get("version"),
                "signal_table": self.config.mysql_signal_table,
            }
        except Exception as exc:
            return {
                "reachable": False,
                "database": os.getenv("MYSQL_DATABASE", "bbbot1"),
                "signal_table": self.config.mysql_signal_table,
                "error": str(exc),
            }

    def health_snapshot(self, probe_fastapi: bool = True) -> dict[str, Any]:
        return {
            "name": self.config.name,
            "fund": self.config.fund,
            "strategy": self.config.strategy,
            "execution_enabled": self.config.enable_trading,
            "dashboard_url": self.config.dashboard_url,
            "dependencies": self._dependency_status(),
            "fastapi": {
                "reachable": True,
                "url": self.config.fastapi_base_url,
                "detail": "In-process Rhea API assumed healthy" if not probe_fastapi else "Use /rhea/health for in-process checks",
            },
            "airflow": self.check_airflow(),
            "mlflow": self.check_mlflow(),
            "mysql": self.check_mysql(),
            "airbyte": {
                "source": self.config.airbyte_source,
                "config": self.airbyte_source_config(),
                "connection_id_env": self.config.airbyte_connection_id_env,
                "configured": bool(os.getenv(self.config.airbyte_connection_id_env, "").strip()),
            },
            "discord": {
                "configured": bool(
                    os.getenv("DISCORD_BOT_TALK_WEBHOOK", "").strip()
                    or os.getenv("DISCORD_WEBHOOK_URL", "").strip()
                    or os.getenv("DISCORD_WEBHOOK", "").strip()
                    or os.getenv("DISCORD_WEBHOOK_PROD", "").strip()
                ),
                "required_indicators": list(self.config.required_indicators),
            },
            "brokers": list(self.config.broker_allowlist),
        }

    def status(self) -> dict[str, Any]:
        return {
            "id": self.config.id,
            "name": self.config.name,
            "runtime_name": self.config.runtime_name,
            "fund": self.config.fund,
            "strategy": self.config.strategy,
            "universe": list(self.config.default_universe),
            "execution_enabled": self.config.enable_trading,
            "mlflow_enabled": self.config.enable_mlflow_logging,
            "airflow_dag_id": self.config.airflow_dag_id,
            "dashboard_url": self.config.dashboard_url,
            "last_analysis": self.last_analysis,
        }

    def log_signal_run(self, analysis: dict[str, Any], run_name: Optional[str] = None) -> dict[str, Any]:
        if mlflow is None:
            return {"logged": False, "reason": "mlflow unavailable"}

        try:
            mlflow.set_tracking_uri(self.config.mlflow_tracking_uri)
            mlflow.set_experiment(self.config.mlflow_experiment)
            with mlflow.start_run(run_name=run_name or f"rhea_{analysis['ticker'].lower()}"):
                mlflow.set_tag("bot", self.config.name)
                mlflow.set_tag("fund", self.config.fund)
                mlflow.set_tag("strategy", self.config.strategy)
                mlflow.log_param("ticker", analysis["ticker"])
                mlflow.log_param("action", analysis["action"])
                mlflow.log_param("universe", analysis["universe"])
                mlflow.log_metric("composite_score", float(analysis["composite_score"]))
                mlflow.log_metric("sentiment_score", float(analysis["sentiment"]["score"]))
                mlflow.log_metric("adi", float(analysis["technical"].get("adi", 0.0)))
                mlflow.log_metric("random_forest_vote", float(analysis["model_stack"].get("random_forest_vote", 0.0)))
                mlflow.log_metric("xgboost_vote", float(analysis["model_stack"].get("xgboost_vote", 0.0)))
            return {
                "logged": True,
                "tracking_uri": self.config.mlflow_tracking_uri,
                "experiment": self.config.mlflow_experiment,
            }
        except Exception as exc:
            return {
                "logged": False,
                "tracking_uri": self.config.mlflow_tracking_uri,
                "experiment": self.config.mlflow_experiment,
                "error": str(exc),
            }


@lru_cache(maxsize=1)
def get_rhea_bot() -> RheaBot:
    return RheaBot()


app = FastAPI(
    title="Rhea Bot API",
    version="0.1.0",
    description="Mansa ADI service surface for Bentley Dashboard, Docker, Airflow, Airbyte, MLflow, and MySQL/Discord trade persistence.",
)


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "bot": "Rhea",
        "fund": "Mansa ADI",
        "health": "/health",
        "status": "/status",
        "analyze": "/analyze",
        "trade": "/trade",
        "strategy_intraday": "/strategy/intraday",
        "strategy_swing": "/strategy/swing",
        "predict_xgboost": "/predict/xgboost",
        "predict_randomforest": "/predict/randomforest",
    }


@app.get("/health")
async def health() -> dict[str, Any]:
    return get_rhea_bot().health_snapshot(probe_fastapi=False)


@app.get("/status")
async def status() -> dict[str, Any]:
    return get_rhea_bot().status()


@app.post("/bootstrap")
async def bootstrap() -> dict[str, Any]:
    return {
        "status": "bootstrapped",
        "analysis": get_rhea_bot().bootstrap_demo_state(),
    }


@app.post("/analyze")
async def analyze(payload: RheaAnalyzeRequest) -> dict[str, Any]:
    try:
        return get_rhea_bot().analyze_ticker(payload.ticker, headlines=payload.news_headlines)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/trade")
async def trade(payload: RheaTradeRequest) -> dict[str, Any]:
    try:
        return get_rhea_bot().execute_trade(
            payload.broker,
            payload.ticker,
            payload.action,
            qty=payload.qty,
            dry_run=payload.dry_run,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/strategy/intraday")
async def strategy_intraday(symbol: str) -> dict[str, Any]:
    analysis = get_rhea_bot().analyze_ticker(symbol)
    return {
        "symbol": symbol.upper(),
        "mode": "intraday",
        "signal": analysis["action"],
        "analysis": analysis,
    }


@app.get("/strategy/swing")
async def strategy_swing(symbol: str) -> dict[str, Any]:
    analysis = get_rhea_bot().analyze_ticker(symbol)
    return {
        "symbol": symbol.upper(),
        "mode": "swing",
        "signal": analysis["action"],
        "analysis": analysis,
    }


@app.get("/technical/indicators")
async def technical_indicators(symbol: str) -> dict[str, Any]:
    return {
        "symbol": symbol.upper(),
        "indicators": get_rhea_bot()._technical_indicators(symbol.upper()),
    }


@app.get("/sentiment/news")
async def sentiment_news(symbol: str, headlines: Optional[str] = None) -> dict[str, Any]:
    parsed = [item.strip() for item in (headlines or "").split("|") if item.strip()]
    score = get_rhea_bot()._sentiment_score(parsed)
    return {
        "symbol": symbol.upper(),
        "headline_count": len(parsed),
        "sentiment_score": score,
    }


@app.post("/predict/xgboost")
async def predict_xgboost(payload: RheaFeatureRequest) -> dict[str, Any]:
    return get_rhea_bot().predict_xgboost(payload.features)


@app.post("/predict/randomforest")
async def predict_randomforest(payload: RheaFeatureRequest) -> dict[str, Any]:
    return get_rhea_bot().predict_random_forest(payload.features)


@app.get("/airbyte-config")
async def airbyte_config() -> dict[str, Any]:
    return get_rhea_bot().airbyte_source_config()
