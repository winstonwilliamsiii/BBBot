from __future__ import annotations

import importlib
import logging
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
statsmodels_arima = _optional_import("statsmodels.tsa.arima.model")
ARIMA = getattr(statsmodels_arima, "ARIMA", None)

try:
    from bbbot1_pipeline.mlflow_config import get_mlflow_tracking_uri
except ImportError:
    get_mlflow_tracking_uri = None

try:
    from scripts.noomo_ml_notify import notify_ml_event
except ImportError:
    from noomo_ml_notify import notify_ml_event


logger = logging.getLogger(__name__)


def _notify_discord_trade(
    side: str,
    symbol: str,
    qty: float,
    broker: Optional[str] = None,
    order_id: Optional[str] = None,
    mode: str = "paper",
) -> None:
    try:
        from frontend.utils.discord_notify import notify_trade
        notify_trade(
            bot_name="Triton",
            symbol=symbol,
            side=side,
            qty=qty,
            status="submitted",
            mode=mode,
            ticket=order_id,
            broker=broker or "",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Discord trade notification failed: %s", exc)


def _notify_discord_trade_triton_legacy(
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
        "title": f"🤖 Triton Trade: {side.upper()} {symbol}",
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


def _headline_fallback_score(headline: str) -> float:
    positive_words = {
        "beat",
        "cargo",
        "delivery",
        "demand",
        "freight",
        "growth",
        "logistics",
        "rebound",
        "strong",
        "upgrade",
    }
    negative_words = {
        "delay",
        "downgrade",
        "fuel",
        "recall",
        "slowdown",
        "strike",
        "tariff",
        "weak",
    }
    words = {
        token.strip(".,:;!?()[]{}\"'").lower()
        for token in str(headline or "").split()
        if token.strip()
    }
    if not words:
        return 0.0

    positive_hits = len(words & positive_words)
    negative_hits = len(words & negative_words)
    return _clamp((positive_hits - negative_hits) / max(len(words), 4))


@dataclass
class TritonConfig:
    alpaca_api_key: Optional[str]
    alpaca_secret_key: Optional[str]
    alpaca_base_url: str
    ibkr_host: str
    ibkr_port: int
    ibkr_client_id: int
    fastapi_base_url: str
    mlflow_tracking_uri: str
    mlflow_experiment: str
    enable_trading: bool
    enable_mlflow_logging: bool
    default_history_period: str
    default_history_interval: str
    forecast_steps: int
    transport_universe: tuple[str, ...]
    buy_threshold: float
    sell_threshold: float
    fund: str = "Mansa Transportation"
    strategy: str = "ARIMA and LSTM Swing Trading"

    @classmethod
    def from_env(cls) -> "TritonConfig":
        if load_dotenv is not None:
            load_dotenv(override=False)

        tracking_uri = (
            os.getenv("TRITON_MLFLOW_TRACKING_URI")
            or os.getenv("MLFLOW_TRACKING_URI")
            or (
                get_mlflow_tracking_uri()
                if get_mlflow_tracking_uri is not None
                else "http://localhost:5000"
            )
        )
        raw_universe = os.getenv(
            "TRITON_UNIVERSE",
            "IYT,UNP,CSX,NSC,UPS,FDX,DAL,UBER",
        )
        transport_universe = tuple(
            ticker.strip().upper()
            for ticker in raw_universe.split(",")
            if ticker.strip()
        )

        return cls(
            alpaca_api_key=os.getenv("ALPACA_API_KEY"),
            alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY"),
            alpaca_base_url=os.getenv(
                "ALPACA_BASE_URL",
                "https://paper-api.alpaca.markets",
            ),
            ibkr_host=os.getenv("IBKR_HOST", "127.0.0.1"),
            ibkr_port=_as_int(os.getenv("IBKR_PORT"), 7497),
            ibkr_client_id=_as_int(os.getenv("IBKR_CLIENT_ID"), 7),
            fastapi_base_url=(
                os.getenv("TRITON_FASTAPI_URL")
                or os.getenv("CONTROL_CENTER_API_URL")
                or os.getenv("FASTAPI_BASE_URL")
                or "http://127.0.0.1:5001"
            ),
            mlflow_tracking_uri=tracking_uri,
            mlflow_experiment=os.getenv(
                "TRITON_MLFLOW_EXPERIMENT",
                "Triton_Mansa_Transportation",
            ),
            enable_trading=_as_bool(os.getenv("TRITON_ENABLE_TRADING"), False),
            enable_mlflow_logging=_as_bool(
                os.getenv("TRITON_ENABLE_MLFLOW_LOGGING"),
                True,
            ),
            default_history_period=os.getenv("TRITON_HISTORY_PERIOD", "1y"),
            default_history_interval=os.getenv(
                "TRITON_HISTORY_INTERVAL",
                "1d",
            ),
            forecast_steps=_as_int(os.getenv("TRITON_FORECAST_STEPS"), 5),
            transport_universe=transport_universe,
            buy_threshold=_as_float(os.getenv("TRITON_BUY_THRESHOLD"), 0.18),
            sell_threshold=_as_float(
                os.getenv("TRITON_SELL_THRESHOLD"),
                -0.18,
            ),
        )


class TritonBot:
    def __init__(self, config: Optional[TritonConfig] = None):
        self.config = config or TritonConfig.from_env()
        self._alpaca = None
        self._ib = None
        self.last_analysis: dict[str, Any] = {}

    def _dependency_status(self) -> dict[str, bool]:
        return {
            "numpy": np is not None,
            "pandas": pd is not None,
            "yfinance": yf is not None,
            "textblob": TextBlob is not None,
            "statsmodels": ARIMA is not None,
            "mlflow": mlflow is not None,
            "alpaca_trade_api": tradeapi is not None,
            "ib_insync": ib_insync is not None,
        }

    def _sanitize_ticker(self, ticker: str) -> str:
        normalized = str(ticker or "").strip().upper()
        if not normalized:
            raise ValueError("Ticker is required")
        return normalized

    def _alpha_vantage_api_key(self) -> str:
        raw = (
            os.getenv("TRITON_ALPHA_VANTAGE_API_KEY", "").strip()
            or os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()
        )
        if raw.lower() in {"your_alpha_vantage_key_here", "demo"}:
            return ""
        return raw

    def _fetch_price_history_from_alpha_vantage(self, ticker: str) -> Any:
        if pd is None:
            return None

        api_key = self._alpha_vantage_api_key()
        if not api_key:
            return None

        interval = str(self.config.default_history_interval or "1d").lower()
        if interval not in {"1d", "1day", "daily"}:
            return None

        try:
            response = requests.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "TIME_SERIES_DAILY_ADJUSTED",
                    "symbol": ticker,
                    "outputsize": "compact",
                    "apikey": api_key,
                },
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            logger.warning("Alpha Vantage price fallback failed for %s: %s", ticker, exc)
            return None

        if not isinstance(payload, dict):
            return None
        if "Note" in payload or "Error Message" in payload:
            logger.warning("Alpha Vantage returned API warning for %s: %s", ticker, payload)
            return None

        series = payload.get("Time Series (Daily)")
        if not isinstance(series, dict) or not series:
            return None

        rows: list[dict[str, Any]] = []
        for date_str, values in series.items():
            if not isinstance(values, dict):
                continue
            try:
                rows.append(
                    {
                        "Date": date_str,
                        "Open": float(values.get("1. open", 0.0)),
                        "High": float(values.get("2. high", 0.0)),
                        "Low": float(values.get("3. low", 0.0)),
                        "Close": float(values.get("4. close", 0.0)),
                        "Adj Close": float(values.get("5. adjusted close", 0.0)),
                        "Volume": float(values.get("6. volume", 0.0)),
                    }
                )
            except (TypeError, ValueError):
                continue

        if not rows:
            return None

        history = pd.DataFrame(rows)
        history["Date"] = pd.to_datetime(history["Date"], errors="coerce")
        history = history.dropna(subset=["Date"]).set_index("Date").sort_index()
        if history.empty:
            return None
        return history

    def _fetch_price_history_from_ibkr(self, ticker: str) -> Any:
        if ib_insync is None or pd is None:
            return None

        ib_client = ib_insync.IB()
        connected = False
        try:
            ib_client.connect(
                self.config.ibkr_host,
                self.config.ibkr_port,
                clientId=self.config.ibkr_client_id,
                timeout=5,
            )
            connected = True
            contract = ib_insync.Stock(ticker, "SMART", "USD")
            ib_client.qualifyContracts(contract)
            bars = ib_client.reqHistoricalData(
                contract,
                endDateTime="",
                durationStr="1 Y",
                barSizeSetting="1 day",
                whatToShow="TRADES",
                useRTH=True,
                formatDate=1,
                keepUpToDate=False,
            )
            if not bars:
                return None

            rows: list[dict[str, Any]] = []
            for bar in bars:
                rows.append(
                    {
                        "Date": bar.date,
                        "Open": float(bar.open),
                        "High": float(bar.high),
                        "Low": float(bar.low),
                        "Close": float(bar.close),
                        "Volume": float(bar.volume),
                    }
                )

            history = pd.DataFrame(rows)
            history["Date"] = pd.to_datetime(history["Date"], errors="coerce")
            history = history.dropna(subset=["Date"]).set_index("Date").sort_index()
            return history if not history.empty else None
        except Exception as exc:  # noqa: BLE001
            logger.warning("IBKR price fallback failed for %s: %s", ticker, exc)
            return None
        finally:
            if connected and ib_client.isConnected():
                ib_client.disconnect()

    def _fetch_fundamentals_from_alpha_vantage(self, ticker: str) -> dict[str, Any]:
        api_key = self._alpha_vantage_api_key()
        if not api_key:
            return {}

        try:
            response = requests.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "OVERVIEW",
                    "symbol": ticker,
                    "apikey": api_key,
                },
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            logger.warning("Alpha Vantage fundamentals fallback failed for %s: %s", ticker, exc)
            return {}

        if not isinstance(payload, dict):
            return {}
        if "Note" in payload or "Error Message" in payload or "Symbol" not in payload:
            return {}

        def _to_float(raw: Any) -> Optional[float]:
            try:
                if raw in (None, "", "None", "-"):
                    return None
                return float(raw)
            except (TypeError, ValueError):
                return None

        def _to_int(raw: Any) -> Optional[int]:
            try:
                if raw in (None, "", "None", "-"):
                    return None
                return int(float(raw))
            except (TypeError, ValueError):
                return None

        return {
            "sector": payload.get("Sector"),
            "industry": payload.get("Industry"),
            "marketCap": _to_int(payload.get("MarketCapitalization")),
            "forwardPE": _to_float(payload.get("ForwardPE")) or _to_float(payload.get("PERatio")),
            "profitMargins": _to_float(payload.get("ProfitMargin")),
            "revenueGrowth": _to_float(payload.get("QuarterlyRevenueGrowthYOY")),
            "beta": _to_float(payload.get("Beta")),
        }

    def _fetch_price_history(self, ticker: str) -> Any:
        history = None
        if yf is not None:
            try:
                history = yf.download(
                    ticker,
                    period=self.config.default_history_period,
                    interval=self.config.default_history_interval,
                    progress=False,
                    auto_adjust=False,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("yfinance download failed for %s: %s", ticker, exc)

            if history is None or history.empty:
                try:
                    history = yf.Ticker(ticker).history(
                        period=self.config.default_history_period,
                        interval=self.config.default_history_interval,
                        auto_adjust=False,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("yfinance Ticker.history failed for %s: %s", ticker, exc)

        if history is not None and not history.empty:
            return history

        av_history = self._fetch_price_history_from_alpha_vantage(ticker)
        if av_history is not None and not av_history.empty:
            return av_history

        ibkr_history = self._fetch_price_history_from_ibkr(ticker)
        if ibkr_history is not None and not ibkr_history.empty:
            return ibkr_history

        raise RuntimeError(
            f"No market data returned for {ticker} from yfinance, Alpha Vantage, or IBKR"
        )

    def _extract_close_series(self, history: Any) -> Any:
        if pd is None:
            raise RuntimeError("pandas is not installed")
        if history is None or history.empty:
            raise RuntimeError("Pricing data is empty")

        if isinstance(history.columns, pd.MultiIndex):
            close_columns = [
                column
                for column in history.columns
                if str(column[0]) == "Close"
            ]
            if not close_columns:
                raise RuntimeError("Close column missing from pricing data")
            close_series = history[close_columns[0]]
        else:
            if "Close" not in history.columns:
                raise RuntimeError("Close column missing from pricing data")
            close_series = history["Close"]

        if isinstance(close_series, pd.DataFrame):
            close_series = close_series.iloc[:, 0]

        close_series = pd.to_numeric(close_series, errors="coerce").dropna()
        if close_series.empty:
            raise RuntimeError("No valid closing prices available")
        return close_series.astype(float)

    def _fetch_fundamentals(self, ticker: str) -> dict[str, Any]:
        info: dict[str, Any] = {}
        if yf is not None:
            try:
                info = dict(getattr(yf.Ticker(ticker), "info", {}) or {})
            except Exception as exc:  # noqa: BLE001
                logger.warning("yfinance fundamentals failed for %s: %s", ticker, exc)
        if info:
            return info
        return self._fetch_fundamentals_from_alpha_vantage(ticker)

    def fundamental_analysis(
        self,
        ticker: str,
        fundamentals: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        info = (
            fundamentals
            if fundamentals is not None
            else self._fetch_fundamentals(ticker)
        )
        return {
            "ticker": ticker,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "forward_pe": info.get("forwardPE"),
            "profit_margin": info.get("profitMargins"),
            "revenue_growth": info.get("revenueGrowth"),
            "beta": info.get("beta"),
        }

    def technical_analysis(self, history: Any) -> dict[str, Any]:
        close = self._extract_close_series(history)
        delta = close.diff()
        gains = delta.clip(lower=0).rolling(14).mean()
        losses = (-delta.clip(upper=0)).rolling(14).mean().replace(0, pd.NA)
        rs = gains / losses
        rsi = 100 - (100 / (1 + rs))
        rsi = pd.to_numeric(rsi, errors="coerce").fillna(50.0)

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9, adjust=False).mean()

        last_index = close.index[-1]
        timestamp = (
            last_index.isoformat()
            if hasattr(last_index, "isoformat")
            else str(last_index)
        )
        return {
            "timestamp": timestamp,
            "close": float(close.iloc[-1]),
            "rsi_14": float(rsi.iloc[-1]),
            "macd": float(macd.iloc[-1]),
            "macd_signal": float(macd_signal.iloc[-1]),
            "sma_20": float(close.tail(20).mean()),
            "sma_50": float(close.tail(min(50, len(close))).mean()),
        }

    def sentiment_analysis(self, headlines: list[str]) -> dict[str, Any]:
        filtered = [
            headline for headline in headlines if str(headline).strip()
        ]
        if not filtered:
            return {"score": 0.0, "headline_count": 0, "method": "none"}

        scores: list[float] = []
        method = "fallback"
        for headline in filtered:
            if TextBlob is not None:
                method = "textblob"
                score = float(TextBlob(headline).sentiment.polarity)
            else:
                score = _headline_fallback_score(headline)
            scores.append(_clamp(score))

        return {
            "score": round(sum(scores) / len(scores), 4),
            "headline_count": len(filtered),
            "method": method,
        }

    def arima_forecast(
        self,
        history: Any,
        steps: Optional[int] = None,
    ) -> dict[str, Any]:
        if ARIMA is None:
            return {
                "available": False,
                "reason": "statsmodels is not installed",
            }

        close = self._extract_close_series(history)
        if len(close) < 30:
            return {
                "available": False,
                "reason": "ARIMA requires at least 30 closing prices",
            }

        forecast_steps = steps or self.config.forecast_steps
        try:
            model = ARIMA(close, order=(5, 1, 0))
            fitted = model.fit()
            forecast = fitted.forecast(steps=forecast_steps)
            return {
                "available": True,
                "steps": forecast_steps,
                "forecast": [float(value) for value in list(forecast)],
                "last_close": float(close.iloc[-1]),
            }
        except Exception as exc:
            return {
                "available": False,
                "reason": str(exc),
            }

    def _trend_score(self, technicals: dict[str, Any]) -> float:
        rsi_component = _clamp((50.0 - technicals["rsi_14"]) / 50.0)
        macd_component = _clamp(technicals["macd"] - technicals["macd_signal"])
        sma_component = 0.0
        if technicals["sma_50"]:
            sma_component = _clamp(
                (technicals["sma_20"] - technicals["sma_50"])
                / technicals["sma_50"]
                * 10.0
            )
        return round(
            (rsi_component * 0.3)
            + (macd_component * 0.4)
            + (sma_component * 0.3),
            4,
        )

    def analyze_ticker(
        self,
        ticker: str,
        headlines: Optional[list[str]] = None,
        history: Optional[Any] = None,
        fundamentals: Optional[dict[str, Any]] = None,
        log_to_mlflow: Optional[bool] = None,
    ) -> dict[str, Any]:
        symbol = self._sanitize_ticker(ticker)
        shared_history = history
        data_error: Optional[str] = None
        if shared_history is None:
            try:
                shared_history = self._fetch_price_history(symbol)
            except Exception as exc:  # noqa: BLE001
                data_error = str(exc)
                shared_history = None

        if shared_history is None:
            payload = {
                "ticker": symbol,
                "fund": self.config.fund,
                "strategy": self.config.strategy,
                "fundamental": self.fundamental_analysis(symbol, fundamentals),
                "technical": {},
                "sentiment": self.sentiment_analysis(headlines or []),
                "forecast": {
                    "available": False,
                    "reason": "market_data_unavailable",
                },
                "technical_score": 0.0,
                "fundamental_score": 0.0,
                "forecast_score": 0.0,
                "composite_score": 0.0,
                "action": "HOLD",
                "degraded": True,
                "degraded_reason": data_error or "market_data_unavailable",
            }
            self.last_analysis = payload
            return payload

        shared_fundamentals = (
            fundamentals
            if fundamentals is not None
            else self._fetch_fundamentals(symbol)
        )

        fundamental = self.fundamental_analysis(symbol, shared_fundamentals)
        technical = self.technical_analysis(shared_history)
        sentiment = self.sentiment_analysis(headlines or [])
        forecast = self.arima_forecast(shared_history)

        valuation_component = 0.0
        forward_pe = fundamental.get("forward_pe")
        if isinstance(forward_pe, (int, float)) and forward_pe:
            valuation_component = _clamp((22.0 - float(forward_pe)) / 22.0)
        growth_component = _clamp(
            float(fundamental.get("revenue_growth") or 0.0) / 0.2
        )
        fundamental_score = round(
            (valuation_component * 0.5) + (growth_component * 0.5),
            4,
        )
        technical_score = self._trend_score(technical)
        sentiment_score = float(sentiment["score"])

        forecast_score = 0.0
        if forecast.get("available") and forecast.get("forecast"):
            last_close = float(forecast["last_close"])
            projected_close = float(forecast["forecast"][-1])
            forecast_score = _clamp(
                ((projected_close / last_close) - 1.0) * 10.0
            )

        composite_score = round(
            (technical_score * 0.45)
            + (fundamental_score * 0.25)
            + (sentiment_score * 0.15)
            + (forecast_score * 0.15),
            4,
        )

        action = "HOLD"
        if composite_score >= self.config.buy_threshold:
            action = "BUY"
        elif composite_score <= self.config.sell_threshold:
            action = "SELL"

        payload = {
            "ticker": symbol,
            "fund": self.config.fund,
            "strategy": self.config.strategy,
            "fundamental": fundamental,
            "technical": technical,
            "sentiment": sentiment,
            "forecast": forecast,
            "technical_score": technical_score,
            "fundamental_score": fundamental_score,
            "forecast_score": forecast_score,
            "composite_score": composite_score,
            "action": action,
        }
        self.last_analysis = payload

        should_log = (
            self.config.enable_mlflow_logging
            if log_to_mlflow is None
            else log_to_mlflow
        )
        if should_log:
            payload["mlflow"] = self.log_signal_run(payload)
        return payload

    def bootstrap_demo_state(self) -> dict[str, Any]:
        if pd is None:
            raise RuntimeError("pandas is required for Triton demo bootstrap")
        demo_history = pd.DataFrame(
            {
                "Close": [
                    100,
                    101,
                    102,
                    104,
                    103,
                    105,
                    107,
                    109,
                    111,
                    112,
                    114,
                    116,
                    118,
                    119,
                    121,
                    122,
                    124,
                    126,
                    128,
                    129,
                    130,
                    132,
                    134,
                    136,
                    138,
                    139,
                    141,
                    143,
                    145,
                    147,
                    149,
                    150,
                    152,
                    154,
                    156,
                ]
            }
        )
        demo_fundamentals = {
            "sector": "Industrials",
            "industry": "Railroads",
            "forwardPE": 19.0,
            "revenueGrowth": 0.11,
            "profitMargins": 0.14,
        }
        demo_headlines = [
            "Freight demand rebounds as transport volumes strengthen",
            "Analysts upgrade logistics leaders on pricing discipline",
        ]
        return self.analyze_ticker(
            "IYT",
            headlines=demo_headlines,
            history=demo_history,
            fundamentals=demo_fundamentals,
            log_to_mlflow=False,
        )

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
        symbol = self._sanitize_ticker(ticker)
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
            "ticker": symbol,
            "action": normalized_action,
            "qty": float(qty),
            "dry_run": effective_dry_run,
        }
        if effective_dry_run:
            preview["status"] = "simulated"
            preview["reason"] = "Trading disabled; no live order submitted"
            return preview

        if normalized_broker == "alpaca":
            api = self._get_alpaca_client()
            order = api.submit_order(
                symbol=symbol,
                qty=qty,
                side=normalized_action.lower(),
                type="market",
                time_in_force="day",
            )
            preview["status"] = "submitted"
            preview["order_id"] = getattr(order, "id", None)
            _notify_discord_trade(normalized_action, symbol, qty, "alpaca", preview["order_id"])
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

            contract = ib_insync.Stock(symbol, "SMART", "USD")
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
            _notify_discord_trade(normalized_action, symbol, qty, "ibkr", preview["order_id"])
            return preview

        raise ValueError("Broker must be 'alpaca' or 'ibkr'")

    def configure(self, overrides: dict[str, Any]) -> dict[str, Any]:
        updated = {}
        for key, value in overrides.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                updated[key] = value
        return {"updated": updated, "config": asdict(self.config)}

    def check_fastapi(self) -> dict[str, Any]:
        base_url = self.config.fastapi_base_url.rstrip("/")
        last_error = "No FastAPI health endpoint responded"
        for path in ("/triton/health", "/health", "/healthz"):
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
            is_remote_uri = any(
                tracking_uri.startswith(prefix)
                for prefix in ("http://", "https://")
            )
            if is_remote_uri:
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

    def health_snapshot(self) -> dict[str, Any]:
        alpaca_ready, alpaca_error = self._alpaca_ready()
        ibkr_ready, ibkr_error = self._ibkr_ready()
        return {
            "name": "Triton",
            "fund": self.config.fund,
            "strategy": self.config.strategy,
            "transport_universe": list(self.config.transport_universe),
            "execution_enabled": self.config.enable_trading,
            "dependencies": self._dependency_status(),
            "fastapi": self.check_fastapi(),
            "mlflow": self.check_mlflow(),
            "brokers": {
                "alpaca": {"ready": alpaca_ready, "error": alpaca_error},
                "ibkr": {"ready": ibkr_ready, "error": ibkr_error},
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "id": 7,
            "name": "Triton",
            "fund": self.config.fund,
            "strategy": self.config.strategy,
            "transport_universe": list(self.config.transport_universe),
            "execution_enabled": self.config.enable_trading,
            "mlflow_enabled": self.config.enable_mlflow_logging,
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
                run_name or f"triton_{analysis['ticker'].lower()}"
            )
            run_id = "n/a"
            with mlflow.start_run(run_name=resolved_run_name) as run:
                run_id = run.info.run_id
                mlflow.set_tag("bot", "Triton")
                mlflow.set_tag("fund", self.config.fund)
                mlflow.set_tag("strategy", self.config.strategy)
                for key, value in (tags or {}).items():
                    mlflow.set_tag(key, value)

                mlflow.log_param("ticker", analysis["ticker"])
                mlflow.log_param("action", analysis["action"])
                mlflow.log_metric(
                    "composite_score",
                    float(analysis["composite_score"]),
                )
                mlflow.log_metric(
                    "technical_score",
                    float(analysis["technical_score"]),
                )
                mlflow.log_metric(
                    "fundamental_score",
                    float(analysis["fundamental_score"]),
                )
                mlflow.log_metric(
                    "forecast_score",
                    float(analysis["forecast_score"]),
                )
                mlflow.log_metric(
                    "sentiment_score",
                    float(analysis["sentiment"]["score"]),
                )
                if hasattr(mlflow, "log_text"):
                    mlflow.log_text(
                        str(analysis),
                        f"triton_{analysis['ticker'].lower()}_analysis.txt",
                    )
            notify_ml_event(
                bot_name="Triton",
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
        except (
            RuntimeError,
            TypeError,
            ValueError,
            MlflowException,
            requests.RequestException,
        ) as exc:
            logger.warning("Triton MLflow logging failed: %s", exc)
            return {
                "logged": False,
                "tracking_uri": self.config.mlflow_tracking_uri,
                "error": str(exc),
            }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot = TritonBot()
    print(bot.bootstrap_demo_state())
