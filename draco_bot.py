from __future__ import annotations

import json
import importlib
import logging
import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


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
pd = _optional_import("pandas")
statsmodels_arima = _optional_import("statsmodels.tsa.arima.model")
ARIMA = getattr(statsmodels_arima, "ARIMA", None)
textblob_module = _optional_import("textblob")
TextBlob = getattr(textblob_module, "TextBlob", None)
yf = _optional_import("yfinance")


logger = logging.getLogger(__name__)


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


@dataclass
class DracoConfig:
    alpaca_api_key: Optional[str]
    alpaca_secret_key: Optional[str]
    alpaca_base_url: str
    ibkr_host: str
    ibkr_port: int
    ibkr_client_id: int
    mlflow_tracking_uri: str
    mlflow_experiment: str
    enable_trading: bool
    enable_mlflow_logging: bool
    forecast_steps: int
    default_history_period: str
    default_history_interval: str

    @classmethod
    def from_env(cls) -> "DracoConfig":
        if load_dotenv is not None:
            load_dotenv(override=False)

        return cls(
            alpaca_api_key=os.getenv("ALPACA_API_KEY"),
            alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY"),
            alpaca_base_url=os.getenv(
                "ALPACA_BASE_URL",
                "https://paper-api.alpaca.markets",
            ),
            ibkr_host=os.getenv("IBKR_HOST", "127.0.0.1"),
            ibkr_port=_as_int(os.getenv("IBKR_PORT"), 7497),
            ibkr_client_id=_as_int(os.getenv("IBKR_CLIENT_ID"), 1),
            mlflow_tracking_uri=os.getenv(
                "MLFLOW_TRACKING_URI",
                "http://localhost:5000",
            ),
            mlflow_experiment=os.getenv(
                "DRACO_MLFLOW_EXPERIMENT",
                "draco_bot_analysis",
            ),
            enable_trading=_as_bool(
                os.getenv("DRACO_ENABLE_TRADING"),
                False,
            ),
            enable_mlflow_logging=_as_bool(
                os.getenv("DRACO_ENABLE_MLFLOW_LOGGING"),
                True,
            ),
            forecast_steps=_as_int(
                os.getenv("DRACO_FORECAST_STEPS"),
                5,
            ),
            default_history_period=os.getenv("DRACO_HISTORY_PERIOD", "1y"),
            default_history_interval=os.getenv("DRACO_HISTORY_INTERVAL", "1d"),
        )


CONFIG = DracoConfig.from_env()


class AnalysisRequest(BaseModel):
    ticker: str = Field(min_length=1)
    news_headlines: list[str] = Field(default_factory=list)
    steps: int = Field(default=CONFIG.forecast_steps, ge=1, le=30)


class TradeRequest(BaseModel):
    ticker: str = Field(min_length=1)
    qty: float = Field(gt=0)
    side: Literal["buy", "sell"]
    broker: Literal["alpaca", "ibkr"]
    order_type: Literal["market", "limit"] = "market"
    limit_price: Optional[float] = Field(default=None, gt=0)


app = FastAPI(
    title="Draco Bot API",
    version="1.0.0",
    description=(
        "Draco analysis and execution service for fundamentals, technicals, "
        "sentiment, ARIMA forecasting, broker routing, and MLflow logging."
    ),
)


def _dependency_status() -> dict[str, bool]:
    return {
        "yfinance": yf is not None,
        "pandas": pd is not None,
        "textblob": TextBlob is not None,
        "statsmodels": ARIMA is not None,
        "mlflow": mlflow is not None,
        "alpaca_trade_api": tradeapi is not None,
        "ib_insync": ib_insync is not None,
    }


def _require_package(name: str, module: Any) -> Any:
    if module is None:
        raise HTTPException(
            status_code=503,
            detail=f"Required dependency '{name}' is not installed",
        )
    return module


def _sanitize_ticker(ticker: str) -> str:
    normalized = str(ticker or "").strip().upper()
    if not normalized:
        raise HTTPException(status_code=400, detail="Ticker is required")
    return normalized


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _coerce_metric_dict(payload: dict[str, Any]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for key, value in payload.items():
        if _is_finite_number(value):
            metrics[key] = float(value)
    return metrics


def _mlflow_tracking_is_reachable(tracking_uri: str) -> bool:
    if mlflow is None:
        return False

    uri = str(tracking_uri or "").strip()
    if not uri:
        return False

    if uri.startswith("http://") or uri.startswith("https://"):
        health_url = f"{uri.rstrip('/')}/health"
        try:
            with urlopen(health_url, timeout=2) as response:
                return 200 <= getattr(response, "status", 200) < 300
        except (URLError, TimeoutError, ValueError):
            logger.info("MLflow health check failed for %s", health_url)
            return False

    return True


def _extract_close_series(history: Any) -> Any:
    if history is None or len(history.index) == 0:
        raise HTTPException(status_code=404, detail="No pricing data returned")

    pandas_module = _require_package("pandas", pd)

    if isinstance(history.columns, pandas_module.MultiIndex):
        if ("Close", "") in history.columns:
            close_series = history[("Close", "")]
        else:
            close_columns = [
                column
                for column in history.columns
                if str(column[0]) == "Close"
            ]
            if not close_columns:
                raise HTTPException(
                    status_code=502,
                    detail="Close column missing from market data",
                )
            close_series = history[close_columns[0]]
    else:
        if "Close" not in history.columns:
            raise HTTPException(
                status_code=502,
                detail="Close column missing from market data",
            )
        close_series = history["Close"]

    return close_series.astype(float)


def get_price_history(
    ticker: str,
    period: Optional[str] = None,
    interval: Optional[str] = None,
) -> Any:
    yfinance_module = _require_package("yfinance", yf)
    _require_package("pandas", pd)

    symbol = _sanitize_ticker(ticker)
    history = yfinance_module.download(
        symbol,
        period=period or CONFIG.default_history_period,
        interval=interval or CONFIG.default_history_interval,
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    if history is None or history.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No market data returned for {symbol}",
        )
    return history


def fundamental_analysis(ticker: str) -> dict[str, Any]:
    yfinance_module = _require_package("yfinance", yf)
    symbol = _sanitize_ticker(ticker)
    info = yfinance_module.Ticker(symbol).info or {}
    return {
        "ticker": symbol,
        "short_name": info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "currency": info.get("currency"),
        "forward_pe": info.get("forwardPE"),
        "market_cap": info.get("marketCap"),
        "dividend_yield": info.get("dividendYield"),
        "profit_margins": info.get("profitMargins"),
        "return_on_equity": info.get("returnOnEquity"),
        "beta": info.get("beta"),
    }


def compute_rsi(series: Any, period: int = 14) -> Any:
    pandas_module = _require_package("pandas", pd)
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    loss = loss.replace(0, pandas_module.NA)
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(0)


def technical_analysis(history: Any) -> dict[str, Any]:
    pandas_module = _require_package("pandas", pd)
    close_series = _extract_close_series(history)
    technical_df = pandas_module.DataFrame(index=history.index)
    technical_df["close"] = close_series
    technical_df["sma_20"] = technical_df["close"].rolling(20).mean()
    technical_df["sma_50"] = technical_df["close"].rolling(50).mean()
    technical_df["rsi_14"] = compute_rsi(technical_df["close"])
    latest = technical_df.dropna(how="all").tail(1)
    if latest.empty:
        raise HTTPException(
            status_code=422,
            detail="Insufficient history for technical analysis",
        )

    last_row = latest.iloc[0]
    timestamp = latest.index[-1]
    timestamp_value = (
        timestamp.isoformat()
        if hasattr(timestamp, "isoformat")
        else str(timestamp)
    )
    sma_20 = (
        float(last_row["sma_20"])
        if pandas_module.notna(last_row["sma_20"])
        else None
    )
    sma_50 = (
        float(last_row["sma_50"])
        if pandas_module.notna(last_row["sma_50"])
        else None
    )
    rsi_14 = (
        float(last_row["rsi_14"])
        if pandas_module.notna(last_row["rsi_14"])
        else None
    )
    return {
        "timestamp": timestamp_value,
        "close": float(last_row["close"]),
        "sma_20": sma_20,
        "sma_50": sma_50,
        "rsi_14": rsi_14,
    }


def sentiment_analysis(news_headlines: list[str]) -> dict[str, Any]:
    headlines = [
        headline.strip()
        for headline in news_headlines
        if headline and headline.strip()
    ]
    if not headlines:
        return {
            "headline_count": 0,
            "sentiment_score": 0.0,
            "provider": "none",
        }

    if TextBlob is None:
        return {
            "headline_count": len(headlines),
            "sentiment_score": 0.0,
            "provider": "textblob_unavailable",
        }

    scores = [TextBlob(headline).sentiment.polarity for headline in headlines]
    mean_score = sum(scores) / len(scores)
    return {
        "headline_count": len(headlines),
        "sentiment_score": float(mean_score),
        "provider": "textblob",
    }


def arima_forecast(history: Any, steps: int) -> dict[str, Any]:
    arima_class = _require_package("statsmodels", ARIMA)
    close_series = _extract_close_series(history).dropna()
    if len(close_series) < 30:
        raise HTTPException(
            status_code=422,
            detail="ARIMA forecast requires at least 30 closing prices",
        )

    try:
        model = arima_class(close_series, order=(5, 1, 0))
        fitted_model = model.fit()
        forecast = fitted_model.forecast(steps=steps)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"ARIMA forecast failed: {exc}",
        ) from exc

    values = [float(value) for value in list(forecast)]
    return {
        "steps": steps,
        "forecast": values,
        "last_close": float(close_series.iloc[-1]),
    }


def log_analysis_to_mlflow(
    *,
    ticker: str,
    fundamentals: dict[str, Any],
    technicals: dict[str, Any],
    sentiment: dict[str, Any],
    forecast: dict[str, Any],
) -> dict[str, Any]:
    if mlflow is None:
        return {"logged": False, "reason": "mlflow_not_installed"}

    if not CONFIG.enable_mlflow_logging:
        return {"logged": False, "reason": "mlflow_logging_disabled"}

    if not _mlflow_tracking_is_reachable(CONFIG.mlflow_tracking_uri):
        return {"logged": False, "reason": "tracking_uri_unreachable"}

    mlflow_module = _require_package("mlflow", mlflow)
    artifact_path: Optional[Path] = None
    try:
        mlflow_module.set_tracking_uri(CONFIG.mlflow_tracking_uri)
        mlflow_module.set_experiment(CONFIG.mlflow_experiment)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix="_forecast.json",
            delete=False,
        ) as handle:
            json.dump(forecast, handle)
            artifact_path = Path(handle.name)

        with mlflow_module.start_run(run_name=f"Draco_{ticker}"):
            mlflow_module.log_param("bot_name", "Draco")
            mlflow_module.log_param("ticker", ticker)
            mlflow_module.log_param("forecast_steps", forecast.get("steps"))
            mlflow_module.log_metrics(
                _coerce_metric_dict(
                    {
                        **fundamentals,
                        **technicals,
                        **sentiment,
                        "forecast_last_close": forecast.get("last_close"),
                    }
                )
            )
            if artifact_path is not None:
                mlflow_module.log_artifact(str(artifact_path))

        return {
            "logged": True,
            "tracking_uri": CONFIG.mlflow_tracking_uri,
            "experiment": CONFIG.mlflow_experiment,
        }
    except (
        MlflowException,
        OSError,
        TypeError,
        ValueError,
        RuntimeError,
    ) as exc:
        logger.warning("MLflow logging failed: %s", exc)
        return {"logged": False, "reason": str(exc)}
    finally:
        if artifact_path is not None and artifact_path.exists():
            artifact_path.unlink(missing_ok=True)


def connect_alpaca() -> Any:
    tradeapi_module = _require_package("alpaca_trade_api", tradeapi)
    if not CONFIG.alpaca_api_key or not CONFIG.alpaca_secret_key:
        raise HTTPException(
            status_code=400,
            detail="Alpaca credentials missing",
        )
    return tradeapi_module.REST(
        CONFIG.alpaca_api_key,
        CONFIG.alpaca_secret_key,
        base_url=CONFIG.alpaca_base_url,
    )


def connect_ibkr() -> Any:
    ib_module = _require_package("ib_insync", ib_insync)
    ib = ib_module.IB()
    try:
        ib.connect(
            CONFIG.ibkr_host,
            CONFIG.ibkr_port,
            clientId=CONFIG.ibkr_client_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"IBKR connection failed: {exc}",
        ) from exc
    return ib


def submit_trade(request: TradeRequest) -> dict[str, Any]:
    symbol = _sanitize_ticker(request.ticker)

    if not CONFIG.enable_trading:
        return {
            "status": "dry_run",
            "broker": request.broker,
            "ticker": symbol,
            "qty": request.qty,
            "side": request.side,
            "order_type": request.order_type,
            "message": "Trading disabled by DRACO_ENABLE_TRADING",
        }

    if request.order_type == "limit" and request.limit_price is None:
        raise HTTPException(
            status_code=400,
            detail="limit_price is required for limit orders",
        )

    if request.broker == "alpaca":
        api = connect_alpaca()
        try:
            order = api.submit_order(
                symbol=symbol,
                qty=request.qty,
                side=request.side,
                type=request.order_type,
                time_in_force="gtc",
                limit_price=request.limit_price,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Alpaca order failed: {exc}",
            ) from exc

        return {
            "status": "submitted",
            "broker": "alpaca",
            "ticker": symbol,
            "order_id": getattr(order, "id", None),
            "raw_status": getattr(order, "status", None),
        }

    ib_module = _require_package("ib_insync", ib_insync)
    ib = connect_ibkr()
    try:
        contract = ib_module.Stock(symbol, "SMART", "USD")
        ib.qualifyContracts(contract)
        if request.order_type == "limit":
            order = ib_module.LimitOrder(
                request.side.upper(),
                request.qty,
                request.limit_price,
            )
        else:
            order = ib_module.MarketOrder(
                request.side.upper(),
                request.qty,
            )
        trade = ib.placeOrder(contract, order)
        status = getattr(getattr(trade, "orderStatus", None), "status", None)
        order_id = getattr(getattr(trade, "order", None), "orderId", None)
        return {
            "status": status or "submitted",
            "broker": "ibkr",
            "ticker": symbol,
            "order_id": order_id,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"IBKR order failed: {exc}",
        ) from exc
    finally:
        if ib.isConnected():
            ib.disconnect()


def build_analysis(
    ticker: str,
    news_headlines: list[str],
    steps: int,
) -> dict[str, Any]:
    symbol = _sanitize_ticker(ticker)
    history = get_price_history(symbol)
    fundamentals = fundamental_analysis(symbol)
    technicals = technical_analysis(history)
    sentiment = sentiment_analysis(news_headlines)
    forecast = arima_forecast(history, steps)
    mlflow_result = log_analysis_to_mlflow(
        ticker=symbol,
        fundamentals=fundamentals,
        technicals=technicals,
        sentiment=sentiment,
        forecast=forecast,
    )
    return {
        "ticker": symbol,
        "fundamentals": fundamentals,
        "technicals": technicals,
        "sentiment": sentiment,
        "forecast": forecast,
        "mlflow": mlflow_result,
    }


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Draco Bot API online"}


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "draco_bot",
        "trading_enabled": CONFIG.enable_trading,
        "mlflow_logging_enabled": CONFIG.enable_mlflow_logging,
        "mlflow_tracking_reachable": _mlflow_tracking_is_reachable(
            CONFIG.mlflow_tracking_uri
        ),
        "dependencies": _dependency_status(),
    }


@app.get("/fundamental")
def get_fundamental(ticker: str = Query(...)) -> dict[str, Any]:
    return fundamental_analysis(ticker)


@app.get("/technical")
def get_technical(ticker: str = Query(...)) -> dict[str, Any]:
    history = get_price_history(ticker, period="6mo", interval="1d")
    result = technical_analysis(history)
    result["ticker"] = _sanitize_ticker(ticker)
    return result


@app.post("/sentiment")
def post_sentiment(request: AnalysisRequest) -> dict[str, Any]:
    result = sentiment_analysis(request.news_headlines)
    result["ticker"] = _sanitize_ticker(request.ticker)
    return result


@app.post("/forecast")
def post_forecast(request: AnalysisRequest) -> dict[str, Any]:
    history = get_price_history(request.ticker)
    result = arima_forecast(history, request.steps)
    result["ticker"] = _sanitize_ticker(request.ticker)
    return result


@app.post("/analysis")
def post_analysis(request: AnalysisRequest) -> dict[str, Any]:
    return build_analysis(
        request.ticker,
        request.news_headlines,
        request.steps,
    )


@app.post("/trade")
def post_trade(request: TradeRequest) -> dict[str, Any]:
    return submit_trade(request)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "draco_bot:app",
        host="127.0.0.1",
        port=8010,
        reload=False,
    )
