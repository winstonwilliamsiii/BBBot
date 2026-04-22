from __future__ import annotations

import csv
import importlib
import json
import os
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


def _optional_import(module_name: str) -> Any:
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None

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

tradeapi = _optional_import("alpaca_trade_api")
ib_insync = _optional_import("ib_insync")

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

try:
    from scripts.noomo_ml_notify import notify_ml_event
except ImportError:
    from noomo_ml_notify import notify_ml_event


REPO_ROOT = Path(__file__).resolve().parent
ALTAIR_PROFILE_PATH = REPO_ROOT / "bentley-bot" / "config" / "bots" / "altair.yml"
ALTAIR_SCREENER_PATH = REPO_ROOT / "bentley-bot" / "config" / "altair_news_signals.csv"

FALLBACK_NORMALIZED_CONFIG = {
    "bot_name": "Altair_Bot",
    "bot_display_name": "Altair",
    "fund_name": "Mansa AI Fund",
    "strategy_label": "Altair_News_Trading",
    "strategy_name": "News Trading",
    "module": "altair_bot.py",
    "screener_file": "altair_news_signals.csv",
    "universe": "AI_News_Momentum",
    "timeframe": "30m",
    "position_size": 1800,
    "risk_rules": {
        "min_news_score": 0.70,
        "min_volume": 800000,
        "max_pe": 60,
        "min_roe": 10,
        "max_debt_to_equity": 0.7,
        "max_holding_hours": 24,
        "max_daily_loss_pct": 1.5,
        "max_open_positions": 4,
    },
    "execution": {
        "primary_client": "alpaca",
        "fallback_client": "ibkr",
        "mode": "paper",
        "enabled": False,
        "order_type": "market",
    },
    "notification": {
        "discord": {
            "required_indicators": ["FVFI", "ROVL"],
        }
    },
}

FALLBACK_RAW_PROFILE = {
    "bot": {
        "id": 4,
        "name": "Altair",
        "runtime_name": "Altair_Bot",
        "fund": "Mansa AI Fund",
        "strategy": "News Trading",
        "module": "altair_bot.py",
    },
    "execution": FALLBACK_NORMALIZED_CONFIG["execution"],
    "strategy": {
        "label": "Altair_News_Trading",
        "screener_file": "altair_news_signals.csv",
        "universe": "AI_News_Momentum",
        "timeframe": "30m",
        "position_size": 1800,
    },
    "services": {
        "fastapi": {
            "route_prefix": "/altair",
            "health_endpoint": "/altair/health",
            "analyze_endpoint": "/altair/analyze",
            "trade_endpoint": "/altair/trade",
        },
        "airflow": {
            "dag_id": "altair_mansa_ai_fund",
            "schedule": "15 8 * * 1-5",
        },
        "airbyte": {
            "source": "stocktwits",
            "source_config": "airbyte/sources/stocktwits/altair_mansa_config.json",
            "connection_id_env": "ALTAIR_AIRBYTE_CONNECTION_ID",
        },
        "mlflow": {
            "experiment": "Altair_Mansa_AI_Fund",
            "tracking_uri_env": "MLFLOW_TRACKING_URI",
        },
    },
    "risk": FALLBACK_NORMALIZED_CONFIG["risk_rules"],
    "notification": FALLBACK_NORMALIZED_CONFIG["notification"],
}


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).strip().replace(",", ""))
    except (AttributeError, TypeError, ValueError):
        return default


def _clamp(value: float, minimum: float = -1.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _headline_sentiment_score(headlines: list[str]) -> float:
    positive_terms = {
        "beat",
        "beats",
        "bullish",
        "upgrade",
        "surge",
        "growth",
        "expand",
        "strong",
        "momentum",
        "ai",
    }
    negative_terms = {
        "miss",
        "misses",
        "downgrade",
        "lawsuit",
        "weak",
        "decline",
        "cuts",
        "bearish",
        "slowdown",
        "risk",
    }
    filtered = [headline for headline in headlines if str(headline).strip()]
    if not filtered:
        return 0.0

    scores: list[float] = []
    for headline in filtered:
        tokens = {
            token.strip(" ,.!?;:-_()[]{}\"").lower()
            for token in str(headline).split()
            if token
        }
        positive_hits = len(tokens & positive_terms)
        negative_hits = len(tokens & negative_terms)
        raw_score = (positive_hits - negative_hits) / max(len(tokens), 1)
        scores.append(_clamp(raw_score * 12.0))

    return round(sum(scores) / len(scores), 4)


def _load_altair_profile() -> tuple[dict[str, Any], dict[str, Any]]:
    if (
        load_bot_config is None
        or yaml is None
        or not ALTAIR_PROFILE_PATH.exists()
    ):
        return dict(FALLBACK_NORMALIZED_CONFIG), dict(FALLBACK_RAW_PROFILE)

    normalized = load_bot_config("Altair", config_path=ALTAIR_PROFILE_PATH)
    with ALTAIR_PROFILE_PATH.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    return normalized, raw if isinstance(raw, dict) else {}


def _resolve_altair_screener_path(normalized: dict[str, Any]) -> Path:
    if resolve_screener_path is not None:
        return resolve_screener_path(normalized, config_path=ALTAIR_PROFILE_PATH)
    return ALTAIR_SCREENER_PATH


def _load_altair_screener_rows(csv_path: Path) -> list[dict[str, str]]:
    if load_screener_rows is not None:
        return load_screener_rows(csv_path)

    rows: list[dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(dict(row))
    return rows


@dataclass
class AltairConfig:
    id: int = 4
    name: str = "Altair"
    runtime_name: str = "Altair_Bot"
    fund: str = "Mansa AI Fund"
    strategy: str = "News Trading"
    screener_file: str = "altair_news_signals.csv"
    universe: str = "AI_News_Momentum"
    timeframe: str = "30m"
    position_size: float = 1800.0
    route_prefix: str = "/altair"
    health_endpoint: str = "/altair/health"
    analyze_endpoint: str = "/altair/analyze"
    trade_endpoint: str = "/altair/trade"
    airflow_dag_id: str = "altair_mansa_ai_fund"
    airflow_schedule: str = "15 8 * * 1-5"
    airflow_base_url: str = "http://localhost:8080"
    airbyte_source: str = "stocktwits"
    airbyte_source_config: str = "airbyte/sources/stocktwits/altair_mansa_config.json"
    airbyte_connection_id_env: str = "ALTAIR_AIRBYTE_CONNECTION_ID"
    mlflow_experiment: str = "Altair_Mansa_AI_Fund"
    mlflow_tracking_uri: str = "http://localhost:5000"
    enable_mlflow_logging: bool = True
    fastapi_base_url: str = "http://localhost:5001"
    dashboard_url: str = "http://localhost:8501"
    enable_trading: bool = False
    execution_mode: str = "paper"
    primary_broker: str = "alpaca"
    fallback_broker: str = "ibkr"
    alpaca_api_key: Optional[str] = None
    alpaca_secret_key: Optional[str] = None
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    ibkr_host: str = "127.0.0.1"
    ibkr_port: int = 7497
    ibkr_client_id: int = 7
    min_volume: float = 800000.0
    max_pe: float = 60.0
    min_roe: float = 10.0
    max_debt_to_equity: float = 0.7
    buy_threshold: float = 0.22
    sell_threshold: float = -0.22
    mysql_signal_table: str = "bot_signal_events"
    required_indicators: tuple[str, ...] = ("FVFI", "ROVL")
    default_universe: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_env(cls) -> "AltairConfig":
        normalized, raw = _load_altair_profile()
        bot_meta = raw.get("bot") if isinstance(raw.get("bot"), dict) else {}
        execution = raw.get("execution") if isinstance(raw.get("execution"), dict) else {}
        strategy_meta = raw.get("strategy") if isinstance(raw.get("strategy"), dict) else {}
        risk = raw.get("risk") if isinstance(raw.get("risk"), dict) else {}
        services = raw.get("services") if isinstance(raw.get("services"), dict) else {}
        fastapi_service = services.get("fastapi") if isinstance(services.get("fastapi"), dict) else {}
        airflow_service = services.get("airflow") if isinstance(services.get("airflow"), dict) else {}
        airbyte_service = services.get("airbyte") if isinstance(services.get("airbyte"), dict) else {}
        mlflow_service = services.get("mlflow") if isinstance(services.get("mlflow"), dict) else {}
        notification = raw.get("notification") if isinstance(raw.get("notification"), dict) else {}
        discord = notification.get("discord") if isinstance(notification.get("discord"), dict) else {}

        screener_path = _resolve_altair_screener_path(normalized)
        universe_rows = _load_altair_screener_rows(screener_path)
        default_universe = tuple(
            str(row.get("Symbol") or row.get("Ticker") or "").strip().upper()
            for row in universe_rows
            if str(row.get("Symbol") or row.get("Ticker") or "").strip()
        )

        return cls(
            id=int(bot_meta.get("id") or 4),
            name=str(bot_meta.get("name") or "Altair"),
            runtime_name=str(bot_meta.get("runtime_name") or "Altair_Bot"),
            fund=str(bot_meta.get("fund") or "Mansa AI Fund"),
            strategy=str(bot_meta.get("strategy") or "News Trading"),
            screener_file=str(normalized.get("screener_file") or strategy_meta.get("screener_file") or "altair_news_signals.csv"),
            universe=str(normalized.get("universe") or strategy_meta.get("universe") or "AI_News_Momentum"),
            timeframe=str(normalized.get("timeframe") or strategy_meta.get("timeframe") or "30m"),
            position_size=float(normalized.get("position_size") or strategy_meta.get("position_size") or 1800),
            route_prefix=str(fastapi_service.get("route_prefix") or "/altair"),
            health_endpoint=str(fastapi_service.get("health_endpoint") or "/altair/health"),
            analyze_endpoint=str(fastapi_service.get("analyze_endpoint") or "/altair/analyze"),
            trade_endpoint=str(fastapi_service.get("trade_endpoint") or "/altair/trade"),
            airflow_dag_id=str(os.getenv("ALTAIR_AIRFLOW_DAG_ID", airflow_service.get("dag_id") or "altair_mansa_ai_fund")),
            airflow_schedule=str(airflow_service.get("schedule") or "15 8 * * 1-5"),
            airflow_base_url=str(os.getenv("AIRFLOW_BASE_URL", "http://localhost:8080")).rstrip("/"),
            airbyte_source=str(airbyte_service.get("source") or "stocktwits"),
            airbyte_source_config=str(os.getenv("ALTAIR_AIRBYTE_SOURCE_CONFIG", airbyte_service.get("source_config") or "airbyte/sources/stocktwits/altair_mansa_config.json")),
            airbyte_connection_id_env=str(airbyte_service.get("connection_id_env") or "ALTAIR_AIRBYTE_CONNECTION_ID"),
            mlflow_experiment=str(os.getenv("ALTAIR_MLFLOW_EXPERIMENT", mlflow_service.get("experiment") or "Altair_Mansa_AI_Fund")),
            mlflow_tracking_uri=str(os.getenv(str(mlflow_service.get("tracking_uri_env") or "MLFLOW_TRACKING_URI"), get_mlflow_tracking_uri())).rstrip("/"),
            enable_mlflow_logging=_truthy(os.getenv("ALTAIR_ENABLE_MLFLOW", "true")),
            fastapi_base_url=str(os.getenv("ALTAIR_FASTAPI_BASE_URL", os.getenv("CONTROL_CENTER_API_URL", "http://localhost:5001"))).rstrip("/"),
            dashboard_url=str(os.getenv("BENTLEY_UI_URL", os.getenv("STREAMLIT_PUBLIC_URL", "http://localhost:8501"))).rstrip("/"),
            enable_trading=_truthy(os.getenv("ALTAIR_ENABLE_TRADING", execution.get("enabled", False))),
            execution_mode=str(os.getenv("ALTAIR_TRADING_MODE") or os.getenv("ALTAIR_EXECUTION_MODE", execution.get("mode") or "paper")).strip().lower(),
            primary_broker=str(
                os.getenv("ALTAIR_PRIMARY_BROKER", execution.get("primary_client") or "alpaca")
            ).strip().lower().replace("_client", ""),
            fallback_broker=str(
                os.getenv("ALTAIR_FALLBACK_BROKER", execution.get("fallback_client") or "ibkr")
            ).strip().lower().replace("_client", ""),
            alpaca_api_key=os.getenv("ALPACA_API_KEY"),
            alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY"),
            alpaca_base_url=str(
                os.getenv("ALPACA_BASE_URL") or (
                    "https://api.alpaca.markets"
                    if (os.getenv("ALTAIR_TRADING_MODE") or os.getenv("ALTAIR_EXECUTION_MODE", execution.get("mode") or "paper")).strip().lower() == "live"
                    else "https://paper-api.alpaca.markets"
                )
            ).strip(),
            ibkr_host=str(os.getenv("IBKR_HOST", "127.0.0.1")).strip(),
            ibkr_port=int(str(
                os.getenv("IBKR_PORT") or (
                    "7496"
                    if (os.getenv("ALTAIR_TRADING_MODE") or os.getenv("ALTAIR_EXECUTION_MODE", execution.get("mode") or "paper")).strip().lower() == "live"
                    else "7497"
                )
            ).strip()),
            ibkr_client_id=int(str(os.getenv("IBKR_CLIENT_ID", "7")).strip()),
            min_volume=_to_float(risk.get("min_volume"), 800000.0),
            max_pe=_to_float(risk.get("max_pe"), 60.0),
            min_roe=_to_float(risk.get("min_roe"), 10.0),
            max_debt_to_equity=_to_float(risk.get("max_debt_to_equity"), 0.7),
            buy_threshold=_to_float(os.getenv("ALTAIR_BUY_THRESHOLD"), 0.22),
            sell_threshold=_to_float(os.getenv("ALTAIR_SELL_THRESHOLD"), -0.22),
            mysql_signal_table=str(os.getenv("ALTAIR_MYSQL_SIGNAL_TABLE", "bot_signal_events")),
            required_indicators=tuple(discord.get("required_indicators") or ("FVFI", "ROVL")),
            default_universe=default_universe,
        )


class AltairAnalyzeRequest(BaseModel):
    ticker: str = Field(min_length=1)
    news_headlines: list[str] = Field(default_factory=list)


class AltairTradeRequest(BaseModel):
    broker: str = Field(default="alpaca", min_length=1)
    ticker: str = Field(min_length=1)
    action: str = Field(min_length=1)
    qty: float = Field(gt=0)
    dry_run: bool = True


class AltairConfigureRequest(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)


class AltairBot:
    def __init__(self, config: Optional[AltairConfig] = None):
        self.config = config or AltairConfig.from_env()
        self.last_analysis: dict[str, Any] = {}
        self._screener_rows = self._load_screener_rows()
        self._alpaca = None
        self._ib = None

    def _load_screener_rows(self) -> dict[str, dict[str, str]]:
        normalized, _ = _load_altair_profile()
        screener_path = _resolve_altair_screener_path(normalized)
        rows = _load_altair_screener_rows(screener_path)
        return {
            str(row.get("Symbol") or row.get("Ticker") or "").strip().upper(): row
            for row in rows
            if str(row.get("Symbol") or row.get("Ticker") or "").strip()
        }

    def _dependency_status(self) -> dict[str, bool]:
        return {
            "requests": requests is not None,
            "yaml": yaml is not None,
            "fastapi": True,
            "mlflow": mlflow is not None,
            "mysql": True,
            "alpaca_trade_api": tradeapi is not None,
            "ib_insync": ib_insync is not None,
        }

    def _sanitize_ticker(self, ticker: str) -> str:
        normalized = str(ticker or "").strip().upper()
        if not normalized:
            raise ValueError("Ticker is required")
        return normalized

    def _score_screener_row(self, ticker: str) -> dict[str, Any]:
        row = self._screener_rows.get(ticker, {})
        volume = _to_float(row.get("volume"))
        pe_ratio = _to_float(row.get("pe"))
        roe = _to_float(row.get("roe"))
        debt_to_equity = _to_float(row.get("debt_to_equity"))

        volume_score = _clamp((volume - self.config.min_volume) / max(self.config.min_volume, 1.0))
        valuation_score = 0.0 if pe_ratio <= 0 else _clamp((self.config.max_pe - pe_ratio) / max(self.config.max_pe, 1.0))
        roe_score = _clamp(roe / max(self.config.min_roe, 1.0))
        leverage_score = _clamp((self.config.max_debt_to_equity - debt_to_equity) / max(self.config.max_debt_to_equity, 0.1))
        quality_score = round((roe_score * 0.6) + (leverage_score * 0.4), 4)

        return {
            "row": row,
            "volume": volume,
            "pe_ratio": pe_ratio,
            "roe": roe,
            "debt_to_equity": debt_to_equity,
            "volume_score": round(volume_score, 4),
            "valuation_score": round(valuation_score, 4),
            "quality_score": quality_score,
        }

    def analyze_ticker(
        self,
        ticker: str,
        headlines: Optional[list[str]] = None,
        log_to_mlflow: Optional[bool] = None,
    ) -> dict[str, Any]:
        symbol = self._sanitize_ticker(ticker)
        screener = self._score_screener_row(symbol)
        sentiment_score = _headline_sentiment_score(headlines or [])
        composite_score = round(
            (screener["volume_score"] * 0.20)
            + (screener["valuation_score"] * 0.25)
            + (screener["quality_score"] * 0.30)
            + (sentiment_score * 0.25),
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
            "screener": screener,
            "sentiment": {
                "score": sentiment_score,
                "headline_count": len(headlines or []),
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
            },
        }
        self.last_analysis = analysis

        should_log = self.config.enable_mlflow_logging if log_to_mlflow is None else bool(log_to_mlflow)
        if should_log:
            analysis["mlflow"] = self.log_signal_run(analysis)

        return analysis

    def bootstrap_demo_state(self) -> dict[str, Any]:
        demo_ticker = self.config.default_universe[0] if self.config.default_universe else "NVDA"
        demo_headlines = [
            "AI infrastructure demand stays strong after enterprise upgrade cycle",
            "Analysts highlight durable data center growth for leading AI names",
        ]
        return self.analyze_ticker(demo_ticker, headlines=demo_headlines, log_to_mlflow=False)

    def _alpaca_ready(self) -> tuple[bool, Optional[str]]:
        if tradeapi is None:
            return False, "alpaca_trade_api is not installed"
        if not self.config.alpaca_api_key or not self.config.alpaca_secret_key:
            return False, "Alpaca credentials are not configured"
        return True, None

    def _ibkr_ready(self) -> tuple[bool, Optional[str]]:
        if ib_insync is None:
            return False, "ib_insync is not installed"
        return True, None

    def _get_alpaca_client(self) -> Any:
        ready, error = self._alpaca_ready()
        if not ready:
            raise RuntimeError(error or "Alpaca is unavailable")
        if self._alpaca is None:
            self._alpaca = tradeapi.REST(
                self.config.alpaca_api_key,
                self.config.alpaca_secret_key,
                self.config.alpaca_base_url,
            )
        return self._alpaca

    def _get_ibkr_client(self) -> Any:
        ready, error = self._ibkr_ready()
        if not ready:
            raise RuntimeError(error or "IBKR is unavailable")
        if self._ib is None:
            self._ib = ib_insync.IB()
        return self._ib

    def _resolve_broker_attempt_order(self, requested_broker: str) -> list[str]:
        requested = str(requested_broker or "").strip().lower().replace("_client", "")
        primary = self.config.primary_broker or "alpaca"
        fallback = self.config.fallback_broker or "ibkr"

        if requested and requested not in {"auto", "default"}:
            return [requested]

        order = [primary]
        if fallback and fallback not in order:
            order.append(fallback)
        return order

    def _submit_order_alpaca(self, symbol: str, side: str, qty: float) -> dict[str, Any]:
        api = self._get_alpaca_client()
        order = api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side.lower(),
            type="market",
            time_in_force="day",
        )
        return {
            "status": "submitted",
            "broker": "alpaca",
            "order_id": getattr(order, "id", None),
            "raw_status": getattr(order, "status", None),
        }

    def _submit_order_ibkr(self, symbol: str, side: str, qty: float) -> dict[str, Any]:
        client = self._get_ibkr_client()
        connected_here = False
        if not client.isConnected():
            client.connect(
                self.config.ibkr_host,
                self.config.ibkr_port,
                clientId=self.config.ibkr_client_id,
            )
            connected_here = True

        contract = ib_insync.Stock(symbol, "SMART", "USD")
        order = ib_insync.MarketOrder(side, qty)
        trade = client.placeOrder(contract, order)

        if connected_here:
            client.disconnect()

        return {
            "status": "submitted",
            "broker": "ibkr",
            "order_id": getattr(getattr(trade, "order", None), "orderId", None),
        }

    def execute_trade(
        self,
        broker: str,
        ticker: str,
        action: str,
        qty: float = 1.0,
        dry_run: Optional[bool] = None,
    ) -> dict[str, Any]:
        symbol = self._sanitize_ticker(ticker)
        normalized_action = str(action or "").strip().upper()
        if normalized_action not in {"BUY", "SELL"}:
            raise ValueError("Action must be BUY or SELL")
        if qty <= 0:
            raise ValueError("Quantity must be positive")

        effective_dry_run = (not self.config.enable_trading) if dry_run is None else bool(dry_run)
        broker_order = self._resolve_broker_attempt_order(broker)

        result = {
            "broker": broker_order[0] if broker_order else "alpaca",
            "attempted_brokers": broker_order,
            "ticker": symbol,
            "action": normalized_action,
            "qty": float(qty),
            "mode": self.config.execution_mode,
            "airflow_dag_id": self.config.airflow_dag_id,
            "mlflow_experiment": self.config.mlflow_experiment,
        }

        if effective_dry_run:
            result["status"] = "simulated"
            result["reason"] = "Dry-run enabled or ALTAIR_ENABLE_TRADING is false"
        else:
            errors: list[str] = []
            submitted = None
            for candidate in broker_order:
                try:
                    if candidate == "alpaca":
                        submitted = self._submit_order_alpaca(symbol, normalized_action, qty)
                    elif candidate == "ibkr":
                        submitted = self._submit_order_ibkr(symbol, normalized_action, qty)
                    else:
                        raise RuntimeError(f"Unsupported broker '{candidate}'")

                    break
                except Exception as exc:
                    errors.append(f"{candidate}: {exc}")

            if submitted is None:
                raise RuntimeError(
                    "All broker attempts failed. " + " | ".join(errors)
                )

            result.update(submitted)

        try:
            from frontend.utils.discord_notify import notify_trade

            notify_trade(
                bot_name=self.config.name,
                symbol=symbol,
                side=normalized_action,
                qty=float(qty),
                status=result["status"],
                mode=self.config.execution_mode,
                broker=result["broker"],
                ticket=str(result.get("order_id") or "") or None,
                fund_name=self.config.fund,
            )
        except Exception:
            pass
        return result

    def configure(self, overrides: dict[str, Any]) -> dict[str, Any]:
        updated = {}
        for key, value in overrides.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                updated[key] = value
        return {"updated": updated, "config": asdict(self.config)}

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
            "user_agent": "Mozilla/5.0 (compatible; AltairBot/1.0)",
            "config_path": str(self.config.airbyte_source_config),
        }

    def check_fastapi(self) -> dict[str, Any]:
        if requests is None:
            return {
                "reachable": False,
                "url": self.config.fastapi_base_url,
                "error": "requests is not installed",
            }

        base_url = self.config.fastapi_base_url.rstrip("/")
        last_error = "No Altair health endpoint responded"
        for path in (self.config.health_endpoint, "/healthz", "/health"):
            url = f"{base_url}{path}"
            try:
                response = requests.get(url, timeout=2)
                if response.ok:
                    return {
                        "reachable": True,
                        "url": url,
                        "status_code": response.status_code,
                    }
            except requests.RequestException as exc:
                last_error = str(exc)
        return {
            "reachable": False,
            "url": base_url,
            "error": last_error,
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
        alpaca_ready, alpaca_error = self._alpaca_ready()
        ibkr_ready, ibkr_error = self._ibkr_ready()
        return {
            "name": self.config.name,
            "fund": self.config.fund,
            "strategy": self.config.strategy,
            "execution_enabled": self.config.enable_trading,
            "execution_mode": self.config.execution_mode,
            "broker_priority": [
                self.config.primary_broker,
                self.config.fallback_broker,
            ],
            "dashboard_url": self.config.dashboard_url,
            "dependencies": self._dependency_status(),
            "fastapi": (
                self.check_fastapi()
                if probe_fastapi
                else {
                    "reachable": True,
                    "url": self.config.fastapi_base_url,
                    "detail": "In-process Altair API assumed healthy",
                }
            ),
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
            "brokers": {
                "alpaca": {"ready": alpaca_ready, "error": alpaca_error},
                "ibkr": {"ready": ibkr_ready, "error": ibkr_error},
            },
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

    def log_signal_run(
        self,
        analysis: dict[str, Any],
        run_name: Optional[str] = None,
    ) -> dict[str, Any]:
        if mlflow is None:
            return {"logged": False, "reason": "mlflow unavailable"}

        try:
            mlflow.set_tracking_uri(self.config.mlflow_tracking_uri)
            mlflow.set_experiment(self.config.mlflow_experiment)
            run_id = "n/a"
            with mlflow.start_run(run_name=run_name or f"altair_{analysis['ticker'].lower()}") as run:
                run_id = run.info.run_id
                mlflow.set_tag("bot", self.config.name)
                mlflow.set_tag("fund", self.config.fund)
                mlflow.set_tag("strategy", self.config.strategy)
                mlflow.log_param("ticker", analysis["ticker"])
                mlflow.log_param("action", analysis["action"])
                mlflow.log_param("universe", analysis["universe"])
                mlflow.log_metric("composite_score", float(analysis["composite_score"]))
                mlflow.log_metric("sentiment_score", float(analysis["sentiment"]["score"]))
                mlflow.log_metric("volume_score", float(analysis["screener"]["volume_score"]))
                mlflow.log_metric("valuation_score", float(analysis["screener"]["valuation_score"]))
                mlflow.log_metric("quality_score", float(analysis["screener"]["quality_score"]))
            notify_ml_event(
                bot_name="Altair",
                event_label="signal analysis completed",
                fields={
                    "symbol": analysis["ticker"],
                    "run_id": run_id,
                    "composite_score": f"{float(analysis['composite_score']):.4f}",
                },
            )
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
def get_altair_bot() -> AltairBot:
    return AltairBot()


app = FastAPI(
    title="Altair Bot API",
    version="0.1.0",
    description="Mansa AI Fund service surface for Bentley Dashboard, Airflow, MLflow, MySQL, and Discord integrations.",
)


def _notify_bot_trade(bot_name: str, trade_result: dict) -> None:
    """Send a Discord trade notification. Never raises."""
    status = trade_result.get("status", "")
    if status not in ("submitted", "simulated", "dry_run"):
        return
    try:
        from frontend.utils.discord_notify import notify_trade
        notify_trade(
            bot_name=bot_name,
            symbol=str(trade_result.get("ticker", "")),
            side=str(trade_result.get("action") or trade_result.get("side") or ""),
            qty=float(trade_result.get("qty", 0)),
            status=status,
            mode=str(trade_result.get("mode", "paper")),
            ticket=str(trade_result.get("order_id", "")) or None,
            broker=str(trade_result.get("broker", "")),
        )
    except Exception:
        pass


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "bot": "Altair",
        "fund": "Mansa AI Fund",
        "health": "/health",
        "status": "/status",
        "analyze": "/analyze",
        "trade": "/trade",
    }


@app.get("/health")
async def health() -> dict[str, Any]:
    return get_altair_bot().health_snapshot(probe_fastapi=False)


@app.get("/status")
async def status() -> dict[str, Any]:
    return get_altair_bot().status()


@app.post("/bootstrap")
async def bootstrap() -> dict[str, Any]:
    return {
        "status": "bootstrapped",
        "analysis": get_altair_bot().bootstrap_demo_state(),
    }


@app.post("/analyze")
async def analyze(payload: AltairAnalyzeRequest) -> dict[str, Any]:
    try:
        return get_altair_bot().analyze_ticker(
            payload.ticker,
            headlines=payload.news_headlines,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/trade")
async def trade(payload: AltairTradeRequest) -> dict[str, Any]:
    try:
        result = get_altair_bot().execute_trade(
            payload.broker,
            payload.ticker,
            payload.action,
            qty=payload.qty,
            dry_run=payload.dry_run,
        )
        _notify_bot_trade("Altair", result)
        return result
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/configure")
async def configure(payload: AltairConfigureRequest) -> dict[str, Any]:
    return get_altair_bot().configure(payload.settings)


@app.get("/airbyte-config")
async def airbyte_config() -> dict[str, Any]:
    return get_altair_bot().airbyte_source_config()