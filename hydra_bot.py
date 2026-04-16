from __future__ import annotations

import importlib
import json
import logging
import math
import os
from dataclasses import asdict, dataclass
from typing import Any, Optional

import requests


def _optional_import(module_name: str) -> Any:
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


dotenv_module = _optional_import("dotenv")
load_dotenv = getattr(dotenv_module, "load_dotenv", None)
tradeapi = _optional_import("alpaca_trade_api")
ib_insync = _optional_import("ib_insync")
mlflow = _optional_import("mlflow")
mlflow_exceptions = _optional_import("mlflow.exceptions")
MlflowException = getattr(mlflow_exceptions, "MlflowException", RuntimeError)
np = _optional_import("numpy")
pd = _optional_import("pandas")
textblob_module = _optional_import("textblob")
TextBlob = getattr(textblob_module, "TextBlob", None)
yf = _optional_import("yfinance")

try:
    from bbbot1_pipeline.mlflow_config import get_mlflow_tracking_uri
except ImportError:
    get_mlflow_tracking_uri = None


logger = logging.getLogger(__name__)


def _notify_discord_trade(
    side: str,
    symbol: str,
    qty: float,
    broker: Optional[str] = None,
    order_id: Optional[str] = None,
) -> None:
    webhook = (
        os.getenv("DISCORD_BOT_TALK_WEBHOOK", "").strip()
        or os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        or os.getenv("DISCORD_WEBHOOK", "").strip()
        or os.getenv("DISCORD_WEBHOOK_PROD", "").strip()
    )
    if not webhook:
        return
    color = 3066993 if str(side).lower() == "buy" else 15158332
    broker_label = f" via {broker}" if broker else ""
    order_label = f" | order: {order_id}" if order_id else ""
    embed = {
        "title": f"🤖 Hydra Trade: {side.upper()} {symbol}",
        "description": f"Qty: {qty}{broker_label}{order_label}",
        "color": color,
    }
    try:
        requests.post(webhook, json={"embeds": [embed]}, timeout=5)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Discord trade notification failed: %s", exc)


def _as_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _as_int(value: Optional[str], default: int) -> int:
    try:
        return int(str(value).strip())
    except (AttributeError, TypeError, ValueError):
        return default


def _as_float(value: Optional[str], default: float) -> float:
    try:
        return float(str(value).strip())
    except (AttributeError, TypeError, ValueError):
        return default


def _clamp(value: float, lower: float = -1.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, float(value)))


def _ensure_list(values: Any) -> list[Any]:
    if values is None:
        return []
    if isinstance(values, list):
        return values
    if isinstance(values, tuple):
        return list(values)
    if hasattr(values, "tolist"):
        return list(values.tolist())
    return [values]


def _headline_fallback_polarity(headline: str) -> float:
    positive_words = {
        "beat",
        "bullish",
        "growth",
        "improves",
        "launch",
        "outperform",
        "strong",
        "surge",
        "upgrade",
    }
    negative_words = {
        "bearish",
        "cut",
        "decline",
        "downgrade",
        "investigation",
        "miss",
        "recall",
        "weak",
    }
    words = {
        word.strip(".,:;!?()[]{}\"'").lower()
        for word in str(headline or "").split()
        if word.strip()
    }
    if not words:
        return 0.0
    positive_hits = len(words & positive_words)
    negative_hits = len(words & negative_words)
    return _clamp((positive_hits - negative_hits) / max(len(words), 4))


@dataclass
class HydraConfig:
    alpaca_api_key: Optional[str]
    alpaca_secret_key: Optional[str]
    alpaca_base_url: str
    ibkr_host: str
    ibkr_port: int
    ibkr_client_id: int
    fastapi_base_url: str
    airbyte_api_base: str
    airflow_dag_id: str
    mlflow_tracking_uri: str
    mlflow_experiment: str
    enable_trading: bool
    enable_mlflow_logging: bool
    momentum_lookback: int
    technical_short_window: int
    technical_long_window: int
    buy_threshold: float
    default_history_period: str
    default_history_interval: str
    default_universe: tuple[str, ...]
    fund: str = "Mansa Health"
    strategy: str = "Momentum Strategy"

    @classmethod
    def from_env(cls) -> "HydraConfig":
        if load_dotenv is not None:
            load_dotenv(override=False)

        mlflow_tracking_uri = (
            os.getenv("HYDRA_MLFLOW_TRACKING_URI")
            or os.getenv("MLFLOW_TRACKING_URI")
            or (
                get_mlflow_tracking_uri()
                if get_mlflow_tracking_uri is not None
                else "http://localhost:5000"
            )
        )
        raw_universe = os.getenv(
            "HYDRA_UNIVERSE",
            "XLV,UNH,ELV,CI,CVS,HCA,ISRG,LLY,ABBV",
        )
        default_universe = tuple(
            ticker.strip().upper()
            for ticker in raw_universe.split(",")
            if ticker.strip()
        )

        return cls(
            alpaca_api_key=(
                os.getenv("ALPACA_API_KEY")
                or os.getenv("ALPACA_KEY_ID")
            ),
            alpaca_secret_key=(
                os.getenv("ALPACA_SECRET_KEY")
                or os.getenv("ALPACA_SECRET")
            ),
            alpaca_base_url=os.getenv(
                "ALPACA_BASE_URL",
                "https://paper-api.alpaca.markets",
            ),
            ibkr_host=os.getenv("IBKR_HOST", "127.0.0.1"),
            ibkr_port=_as_int(os.getenv("IBKR_PORT"), 7497),
            ibkr_client_id=_as_int(os.getenv("IBKR_CLIENT_ID"), 6),
            fastapi_base_url=(
                os.getenv("HYDRA_FASTAPI_URL")
                or os.getenv("CONTROL_CENTER_API_URL")
                or os.getenv("FASTAPI_BASE_URL")
                or "http://127.0.0.1:5001"
            ),
            airbyte_api_base=os.getenv(
                "HYDRA_AIRBYTE_API_BASE",
                "http://localhost:8001/api/v1",
            ),
            airflow_dag_id=os.getenv(
                "HYDRA_AIRFLOW_DAG_ID",
                "hydra_mansa_health",
            ),
            mlflow_tracking_uri=mlflow_tracking_uri,
            mlflow_experiment=os.getenv(
                "HYDRA_MLFLOW_EXPERIMENT",
                "Hydra_Mansa_Health",
            ),
            enable_trading=_as_bool(os.getenv("HYDRA_ENABLE_TRADING"), False),
            enable_mlflow_logging=_as_bool(
                os.getenv("HYDRA_ENABLE_MLFLOW_LOGGING"),
                True,
            ),
            momentum_lookback=_as_int(
                os.getenv("HYDRA_MOMENTUM_LOOKBACK"),
                20,
            ),
            technical_short_window=_as_int(
                os.getenv("HYDRA_TECHNICAL_SHORT_WINDOW"),
                50,
            ),
            technical_long_window=_as_int(
                os.getenv("HYDRA_TECHNICAL_LONG_WINDOW"),
                200,
            ),
            buy_threshold=_as_float(os.getenv("HYDRA_BUY_THRESHOLD"), 0.15),
            default_history_period=os.getenv("HYDRA_HISTORY_PERIOD", "1y"),
            default_history_interval=os.getenv("HYDRA_HISTORY_INTERVAL", "1d"),
            default_universe=default_universe,
        )


class HydraBot:
    def __init__(self, config: Optional[HydraConfig] = None):
        self.config = config or HydraConfig.from_env()
        self._alpaca = None
        self._ib = None
        self.last_analysis: dict[str, Any] = {}

    def _dependency_status(self) -> dict[str, bool]:
        return {
            "numpy": np is not None,
            "pandas": pd is not None,
            "requests": True,
            "textblob": TextBlob is not None,
            "yfinance": yf is not None,
            "mlflow": mlflow is not None,
            "alpaca_trade_api": tradeapi is not None,
            "ib_insync": ib_insync is not None,
        }

    def _sanitize_ticker(self, ticker: str) -> str:
        normalized = str(ticker or "").strip().upper()
        if not normalized:
            raise ValueError("Ticker is required")
        return normalized

    def _extract_close_prices(self, history: Any) -> list[float]:
        if history is None:
            raise RuntimeError("No pricing data returned")

        close_values: Any = None
        pandas_module = pd

        if (
            pandas_module is not None
            and isinstance(history, pandas_module.DataFrame)
        ):
            if history.empty:
                raise RuntimeError("Pricing data is empty")

            if isinstance(history.columns, pandas_module.MultiIndex):
                close_columns = [
                    column
                    for column in history.columns
                    if (isinstance(column, tuple) and column[0] == "Close")
                    or column == "Close"
                ]
                if not close_columns:
                    raise RuntimeError(
                        "Close column missing from pricing data"
                    )
                close_values = history[close_columns[0]]
            elif "Close" in history.columns:
                close_values = history["Close"]
            else:
                raise RuntimeError("Close column missing from pricing data")

            if (
                pandas_module is not None
                and isinstance(close_values, pandas_module.DataFrame)
            ):
                close_values = close_values.iloc[:, 0]

        elif isinstance(history, dict) and "Close" in history:
            close_values = history["Close"]
        elif hasattr(history, "tolist"):
            close_values = history.tolist()
        else:
            close_values = history

        numeric_values: list[float] = []
        for value in _ensure_list(close_values):
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            if math.isfinite(numeric):
                numeric_values.append(numeric)

        if len(numeric_values) < 2:
            raise RuntimeError("At least two valid close prices are required")
        return numeric_values

    def _fetch_price_history(
        self,
        ticker: str,
        period: Optional[str] = None,
    ) -> Any:
        if yf is None:
            return self._fallback_price_history(ticker)
        try:
            history = yf.download(
                ticker,
                period=period or self.config.default_history_period,
                interval=self.config.default_history_interval,
                progress=False,
                auto_adjust=False,
            )
        except Exception:
            return self._fallback_price_history(ticker)
        if history is None or getattr(history, "empty", False):
            return self._fallback_price_history(ticker)
        return history

    def _fallback_price_history(self, ticker: str) -> dict[str, list[float]]:
        normalized_ticker = self._sanitize_ticker(ticker)
        seed = sum(ord(char) for char in normalized_ticker)
        base_price = 90.0 + float(seed % 35)
        closes = [
            round(base_price + (index * 1.35) + ((index % 5) * 0.4), 4)
            for index in range(36)
        ]
        return {"Close": closes}

    def _fetch_fundamentals(self, ticker: str) -> dict[str, Any]:
        if yf is None:
            return {}
        try:
            info = getattr(yf.Ticker(ticker), "info", {}) or {}
        except Exception:
            return {}
        return dict(info)

    def _mean(self, values: list[float]) -> float:
        return sum(values) / len(values)

    def momentum_score(
        self,
        ticker: str,
        price_history: Optional[Any] = None,
        lookback: Optional[int] = None,
    ) -> dict[str, Any]:
        history = (
            price_history
            if price_history is not None
            else self._fetch_price_history(ticker)
        )
        prices = self._extract_close_prices(history)
        effective_lookback = max(
            2,
            min(
                lookback or self.config.momentum_lookback,
                len(prices) - 1,
            ),
        )
        returns = [
            (current / previous) - 1.0
            for previous, current in zip(
                prices[-(effective_lookback + 1):-1],
                prices[-effective_lookback:],
            )
            if previous
        ]
        if not returns:
            raise RuntimeError("Unable to compute momentum returns")
        average_return = self._mean(returns)
        score = _clamp(average_return * 100.0)
        return {
            "score": score,
            "average_return": average_return,
            "lookback": effective_lookback,
            "latest_price": prices[-1],
            "signal": score > 0,
        }

    def fundamental_score(
        self,
        ticker: str,
        fundamentals: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        info = (
            fundamentals
            if fundamentals is not None
            else self._fetch_fundamentals(ticker)
        )

        pe_ratio = info.get("forwardPE") or info.get("trailingPE")
        roe = info.get("returnOnEquity")
        revenue_growth = info.get("revenueGrowth")
        operating_margin = info.get("operatingMargins")

        components = {
            "roe_component": _clamp(
                (float(roe) if roe is not None else 0.0) / 0.25
            ),
            "growth_component": _clamp(
                (
                    float(revenue_growth)
                    if revenue_growth is not None
                    else 0.0
                )
                / 0.20
            ),
            "margin_component": _clamp(
                (
                    float(operating_margin)
                    if operating_margin is not None
                    else 0.0
                )
                / 0.20
            ),
            "pe_component": 0.0,
        }
        if pe_ratio not in (None, 0):
            components["pe_component"] = _clamp(
                (25.0 - float(pe_ratio)) / 25.0
            )

        score = round(self._mean(list(components.values())), 4)
        return {
            "score": score,
            "forward_pe": pe_ratio,
            "return_on_equity": roe,
            "revenue_growth": revenue_growth,
            "operating_margin": operating_margin,
            **components,
        }

    def technical_score(
        self,
        ticker: str,
        price_history: Optional[Any] = None,
    ) -> dict[str, Any]:
        history = (
            price_history
            if price_history is not None
            else self._fetch_price_history(ticker)
        )
        prices = self._extract_close_prices(history)
        long_window = min(self.config.technical_long_window, len(prices))
        short_window = min(
            self.config.technical_short_window,
            max(5, long_window // 2),
        )

        if short_window >= long_window:
            short_window = max(5, long_window - 1)

        short_sma = self._mean(prices[-short_window:])
        long_sma = self._mean(prices[-long_window:])
        if not long_sma:
            raise RuntimeError("Long SMA evaluated to zero")

        crossover = (short_sma / long_sma) - 1.0
        score = _clamp(crossover * 20.0)
        return {
            "score": score,
            "short_sma": short_sma,
            "long_sma": long_sma,
            "signal": short_sma > long_sma,
            "short_window": short_window,
            "long_window": long_window,
        }

    def sentiment_score(self, news_headlines: list[str]) -> dict[str, Any]:
        headlines = [
            headline
            for headline in news_headlines
            if str(headline).strip()
        ]
        if not headlines:
            return {"score": 0.0, "headline_count": 0, "method": "none"}

        scores: list[float] = []
        method = "fallback"
        for headline in headlines:
            if TextBlob is not None:
                method = "textblob"
                polarity = float(TextBlob(headline).sentiment.polarity)
            else:
                polarity = _headline_fallback_polarity(headline)
            scores.append(_clamp(polarity))

        return {
            "score": round(self._mean(scores), 4),
            "headline_count": len(headlines),
            "method": method,
        }

    def analyze_ticker(
        self,
        ticker: str,
        headlines: Optional[list[str]] = None,
        price_history: Optional[Any] = None,
        fundamentals: Optional[dict[str, Any]] = None,
        log_to_mlflow: Optional[bool] = None,
    ) -> dict[str, Any]:
        normalized_ticker = self._sanitize_ticker(ticker)
        if price_history is not None:
            shared_history = price_history
        else:
            try:
                shared_history = self._fetch_price_history(normalized_ticker)
            except Exception as exc:
                raise RuntimeError(
                    "Unable to fetch market data for "
                    f"{normalized_ticker}: {exc}"
                ) from exc

        shared_fundamentals = (
            fundamentals
            if fundamentals is not None
            else self._fetch_fundamentals(normalized_ticker)
        )

        momentum = self.momentum_score(
            normalized_ticker,
            price_history=shared_history,
        )
        fundamental = self.fundamental_score(
            normalized_ticker,
            fundamentals=shared_fundamentals,
        )
        technical = self.technical_score(
            normalized_ticker,
            price_history=shared_history,
        )
        sentiment = self.sentiment_score(headlines or [])

        composite_score = round(
            (momentum["score"] * 0.35)
            + (fundamental["score"] * 0.25)
            + (technical["score"] * 0.25)
            + (sentiment["score"] * 0.15),
            4,
        )
        action = "HOLD"
        if composite_score >= self.config.buy_threshold:
            action = "BUY"
        elif composite_score <= -self.config.buy_threshold:
            action = "SELL"

        analysis = {
            "ticker": normalized_ticker,
            "fund": self.config.fund,
            "strategy": self.config.strategy,
            "momentum": momentum,
            "fundamental": fundamental,
            "technical": technical,
            "sentiment": sentiment,
            "latest_price": momentum.get("latest_price"),
            "composite_score": composite_score,
            "buy_threshold": self.config.buy_threshold,
            "action": action,
        }
        self.last_analysis = analysis

        if log_to_mlflow is None:
            log_to_mlflow = self.config.enable_mlflow_logging
        if log_to_mlflow:
            analysis["mlflow"] = self.log_signal_run(analysis)

        return analysis

    def bootstrap_demo_state(self) -> dict[str, Any]:
        demo_prices = {
            "Close": [
                98,
                99,
                101,
                103,
                105,
                108,
                110,
                112,
                114,
                117,
                119,
                122,
            ]
        }
        demo_fundamentals = {
            "forwardPE": 18.2,
            "returnOnEquity": 0.21,
            "revenueGrowth": 0.12,
            "operatingMargins": 0.17,
        }
        demo_headlines = [
            "Hydra fund target posts strong growth in medical services",
            "Analysts upgrade healthcare momentum names after earnings beat",
        ]
        return self.analyze_ticker(
            "XLV",
            headlines=demo_headlines,
            price_history=demo_prices,
            fundamentals=demo_fundamentals,
            log_to_mlflow=False,
        )

    def scan_universe(
        self,
        tickers: Optional[list[str]] = None,
        headlines_by_ticker: Optional[dict[str, list[str]]] = None,
        log_to_mlflow: Optional[bool] = None,
    ) -> list[dict[str, Any]]:
        headlines_map = headlines_by_ticker or {}
        results: list[dict[str, Any]] = []
        for ticker in tickers or list(self.config.default_universe):
            normalized = self._sanitize_ticker(ticker)
            analysis = self.analyze_ticker(
                normalized,
                headlines=headlines_map.get(normalized, []),
                log_to_mlflow=log_to_mlflow,
            )
            results.append(analysis)
        return results

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

    def execute_trade(
        self,
        broker: str,
        ticker: str,
        action: str,
        qty: float = 10,
        dry_run: Optional[bool] = None,
    ) -> dict[str, Any]:
        normalized_broker = str(broker or "").strip().lower()
        normalized_action = str(action or "").strip().upper()
        normalized_ticker = self._sanitize_ticker(ticker)

        if normalized_action not in {"BUY", "SELL"}:
            raise ValueError("Action must be BUY or SELL")
        if qty <= 0:
            raise ValueError("Quantity must be positive")

        effective_dry_run = (
            (not self.config.enable_trading)
            if dry_run is None
            else bool(dry_run)
        )
        preview = {
            "broker": normalized_broker,
            "ticker": normalized_ticker,
            "action": normalized_action,
            "qty": float(qty),
            "price": self.last_analysis.get("latest_price"),
            "dry_run": effective_dry_run,
        }

        if effective_dry_run:
            preview["status"] = "simulated"
            preview["reason"] = "Trading disabled; no live order submitted"
            return preview

        if normalized_broker == "alpaca":
            api = self._get_alpaca_client()
            order = api.submit_order(
                symbol=normalized_ticker,
                qty=qty,
                side=normalized_action.lower(),
                type="market",
                time_in_force="day",
            )
            preview["status"] = "submitted"
            preview["order_id"] = getattr(order, "id", None)
            _notify_discord_trade(normalized_action, normalized_ticker, qty, "alpaca", preview["order_id"])
            return preview

        if normalized_broker == "ibkr":
            ib_client = self._get_ibkr_client()
            connected_here = False
            if not ib_client.isConnected():
                ib_client.connect(
                    self.config.ibkr_host,
                    self.config.ibkr_port,
                    clientId=self.config.ibkr_client_id,
                )
                connected_here = True

            contract = ib_insync.Stock(normalized_ticker, "SMART", "USD")
            order = ib_insync.MarketOrder(normalized_action, qty)
            trade = ib_client.placeOrder(contract, order)
            preview["status"] = "submitted"
            preview["order_id"] = getattr(
                getattr(trade, "order", None),
                "orderId",
                None,
            )

            if connected_here:
                ib_client.disconnect()

            _notify_discord_trade(normalized_action, normalized_ticker, qty, "ibkr", preview["order_id"])
            return preview

        raise ValueError("Broker must be 'alpaca' or 'ibkr'")

    def configure(self, overrides: dict[str, Any]) -> dict[str, Any]:
        updated = {}
        for key, value in overrides.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                updated[key] = value
        return {"updated": updated, "config": asdict(self.config)}

    def airbyte_source_config(self) -> dict[str, Any]:
        return {
            "tickers": list(self.config.default_universe),
            "user_agent": "Mozilla/5.0 (compatible; HydraBot/1.0)",
        }

    def check_fastapi(self) -> dict[str, Any]:
        base_url = self.config.fastapi_base_url.rstrip("/")
        last_error = "No FastAPI health endpoint responded"
        for path in ("/hydra/health", "/healthz", "/health"):
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

    def check_airbyte(self) -> dict[str, Any]:
        base_url = self.config.airbyte_api_base.rstrip("/")
        last_error = "Airbyte health endpoint did not respond"
        health_candidates = [
            base_url.replace("/api/v1", "") + "/health",
            base_url.replace("/v1", "") + "/health",
        ]
        for url in health_candidates:
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
            if (
                tracking_uri.startswith("http://")
                or tracking_uri.startswith("https://")
            ):
                response = requests.get(
                    f"{tracking_uri.rstrip('/')}/health",
                    timeout=2,
                )
                response.raise_for_status()
            client = mlflow.tracking.MlflowClient()
            experiments = client.search_experiments(max_results=5)
            return {
                "reachable": True,
                "tracking_uri": tracking_uri,
                "experiment_count": len(experiments),
            }
        except Exception as exc:
            return {
                "reachable": False,
                "tracking_uri": tracking_uri,
                "error": str(exc),
            }

    def health_snapshot(
        self,
        probe_fastapi: bool = True,
    ) -> dict[str, Any]:
        alpaca_ready, alpaca_error = self._alpaca_ready()
        ibkr_ready, ibkr_error = self._ibkr_ready()
        return {
            "name": "Hydra",
            "fund": self.config.fund,
            "strategy": self.config.strategy,
            "execution_enabled": self.config.enable_trading,
            "dependencies": self._dependency_status(),
            "fastapi": (
                self.check_fastapi()
                if probe_fastapi
                else {
                    "reachable": True,
                    "url": self.config.fastapi_base_url.rstrip("/"),
                    "detail": "In-process FastAPI status assumed healthy",
                }
            ),
            "airbyte": self.check_airbyte(),
            "mlflow": self.check_mlflow(),
            "brokers": {
                "alpaca": {"ready": alpaca_ready, "error": alpaca_error},
                "ibkr": {"ready": ibkr_ready, "error": ibkr_error},
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "id": 6,
            "name": "Hydra",
            "fund": self.config.fund,
            "strategy": self.config.strategy,
            "universe": list(self.config.default_universe),
            "execution_enabled": self.config.enable_trading,
            "mlflow_enabled": self.config.enable_mlflow_logging,
            "airflow_dag_id": self.config.airflow_dag_id,
            "last_analysis": self.last_analysis,
        }

    def log_signal_run(
        self,
        analysis: dict[str, Any],
        run_name: Optional[str] = None,
        tags: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        if mlflow is None:
            return {"logged": False, "reason": "mlflow unavailable"}

        try:
            mlflow.set_tracking_uri(self.config.mlflow_tracking_uri)
            mlflow.set_experiment(self.config.mlflow_experiment)
            resolved_run_name = (
                run_name or f"hydra_{analysis['ticker'].lower()}"
            )
            with mlflow.start_run(run_name=resolved_run_name):
                mlflow.set_tag("bot", "Hydra")
                mlflow.set_tag("fund", self.config.fund)
                mlflow.set_tag("strategy", self.config.strategy)
                for key, value in (tags or {}).items():
                    mlflow.set_tag(key, value)

                mlflow.log_param("ticker", analysis["ticker"])
                mlflow.log_param("action", analysis["action"])
                mlflow.log_param("airflow_dag_id", self.config.airflow_dag_id)
                mlflow.log_metric(
                    "composite_score",
                    float(analysis["composite_score"]),
                )
                mlflow.log_metric(
                    "momentum_score",
                    float(analysis["momentum"]["score"]),
                )
                mlflow.log_metric(
                    "fundamental_score",
                    float(analysis["fundamental"]["score"]),
                )
                mlflow.log_metric(
                    "technical_score",
                    float(analysis["technical"]["score"]),
                )
                mlflow.log_metric(
                    "sentiment_score",
                    float(analysis["sentiment"]["score"]),
                )
                if hasattr(mlflow, "log_text"):
                    mlflow.log_text(
                        json.dumps(analysis, indent=2, default=str),
                        f"hydra_{analysis['ticker'].lower()}_analysis.json",
                    )
            return {
                "logged": True,
                "tracking_uri": self.config.mlflow_tracking_uri,
            }
        except (
            RuntimeError,
            TypeError,
            ValueError,
            MlflowException,
            requests.RequestException,
        ) as exc:
            logger.warning("Hydra MLflow logging failed: %s", exc)
            return {
                "logged": False,
                "tracking_uri": self.config.mlflow_tracking_uri,
                "error": str(exc),
            }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot = HydraBot()
    print(bot.bootstrap_demo_state())
    print(bot.status())
