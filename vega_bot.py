"""
Vega Bot FastAPI application — Mansa_Retail fund, Vega Mansa Retail MTF-ML strategy.

Primary broker: IBKR (paper port 7497 / live port 7496).
Fallback broker: Alpaca paper.

Mount in Main.py:
    from vega_bot import app as vega_app
    app.mount("/vega", vega_app)

Standalone (port 8011):
    python vega_bot.py
"""

from __future__ import annotations

import datetime
import importlib
import json
import logging
import math
import os
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Optional-import helpers
# ---------------------------------------------------------------------------

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
yf = _optional_import("yfinance")

try:
    from scripts.noomo_ml_notify import notify_ml_event
except ImportError:
    from noomo_ml_notify import notify_ml_event

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Type coercions
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class VegaConfig:
    # IBKR (primary)
    ibkr_host: str
    ibkr_port: int
    ibkr_client_id: int
    # Alpaca (paper fallback)
    alpaca_api_key: Optional[str]
    alpaca_secret_key: Optional[str]
    alpaca_base_url: str
    # MLflow
    mlflow_tracking_uri: str
    mlflow_experiment: str
    # Feature flags
    enable_trading: bool
    enable_mlflow_logging: bool
    # Market data defaults
    forecast_steps: int
    default_history_period: str
    default_history_interval: str
    # Retail universe
    retail_universe: tuple[str, ...] = (
        "KOF", "SBH", "WMT", "FDX", "W", "LULU", "DG", "KO", "PG", "COST",
    )
    # Identity
    bot_name: str = "Vega_Bot"
    fund_name: str = "Mansa_Retail"
    strategy_name: str = "Vega Mansa Retail MTF-ML"

    @classmethod
    def from_env(cls) -> "VegaConfig":
        if load_dotenv is not None:
            load_dotenv(override=False)

        trading_mode = os.getenv("VEGA_TRADING_MODE", "paper").lower()
        default_port = 7497 if trading_mode == "paper" else 7496

        return cls(
            ibkr_host=os.getenv("IBKR_HOST", "127.0.0.1"),
            ibkr_port=_as_int(os.getenv("IBKR_PORT"), default_port),
            ibkr_client_id=_as_int(os.getenv("IBKR_CLIENT_ID"), 1),
            alpaca_api_key=os.getenv("ALPACA_API_KEY"),
            alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY"),
            alpaca_base_url=os.getenv(
                "ALPACA_BASE_URL", "https://paper-api.alpaca.markets"
            ),
            mlflow_tracking_uri=os.getenv(
                "MLFLOW_TRACKING_URI", "http://localhost:5000"
            ),
            mlflow_experiment=os.getenv(
                "VEGA_MLFLOW_EXPERIMENT", "vega_bot_analysis"
            ),
            enable_trading=_as_bool(os.getenv("VEGA_ENABLE_TRADING"), False),
            enable_mlflow_logging=_as_bool(
                os.getenv("VEGA_ENABLE_MLFLOW_LOGGING"), True
            ),
            forecast_steps=_as_int(os.getenv("VEGA_FORECAST_STEPS"), 5),
            default_history_period=os.getenv("VEGA_HISTORY_PERIOD", "6mo"),
            default_history_interval=os.getenv("VEGA_HISTORY_INTERVAL", "1d"),
            retail_universe=tuple(
                t.strip().upper()
                for t in os.getenv(
                    "VEGA_UNIVERSE",
                    "KOF,SBH,WMT,FDX,W,LULU,DG,KO,PG,COST",
                ).split(",")
                if t.strip()
            ),
        )


CONFIG = VegaConfig.from_env()

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class SignalRequest(BaseModel):
    """Breakout signal detection request."""
    ticker: str = Field(min_length=1)
    timeframe: str = Field(default="1d", description="Chart timeframe, e.g. '15m', '1h', '1d'")
    # Optional overrides — if omitted, computed live from yfinance
    breakout_level: Optional[float] = Field(default=None, gt=0)
    volume: Optional[float] = Field(default=None, ge=0)
    atr: Optional[float] = Field(default=None, ge=0)
    direction: Literal["long", "short", "auto"] = "auto"
    news_headlines: list[str] = Field(default_factory=list)


class ExecuteRequest(BaseModel):
    """Execution request derived from a confirmed breakout signal."""
    trade_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticker: str = Field(min_length=1)
    entry_price: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    # Risk sizing: fraction of equity risked per trade (default 1 %)
    risk_pct: float = Field(default=0.01, gt=0, le=0.05)
    broker: Literal["ibkr", "alpaca"] = "ibkr"
    order_type: Literal["market", "limit"] = "market"

    @property
    def risk_ratio(self) -> float:
        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.take_profit - self.entry_price)
        return round(reward / risk, 2) if risk else 0.0

    @property
    def direction(self) -> str:
        return "long" if self.take_profit > self.entry_price else "short"


class TradeLog(BaseModel):
    """Audit record written to MySQL after a trade closes."""
    trade_id: str
    ticker: str = Field(min_length=1)
    entry_price: float
    exit_price: float
    pnl: float
    broker: Literal["ibkr", "alpaca"] = "ibkr"
    strategy: str = "Vega Mansa Retail MTF-ML"
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)


class TradeRequest(BaseModel):
    ticker: str = Field(min_length=1)
    qty: float = Field(gt=0)
    side: Literal["buy", "sell"]
    broker: Literal["ibkr", "alpaca"] = "ibkr"
    order_type: Literal["market", "limit"] = "market"
    limit_price: Optional[float] = Field(default=None, gt=0)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Vega Bot API",
    version="1.0.0",
    description=(
        "Vega_Bot analysis and execution service — Mansa_Retail fund, "
        "Vega Mansa Retail MTF-ML strategy. IBKR primary, Alpaca fallback."
    ),
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

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _dependency_status() -> dict[str, bool]:
    return {
        "yfinance": yf is not None,
        "pandas": pd is not None,
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


def _is_finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _mlflow_reachable(tracking_uri: str) -> bool:
    if mlflow is None:
        return False
    uri = str(tracking_uri or "").strip()
    if uri.startswith(("http://", "https://")):
        try:
            with urlopen(f"{uri.rstrip('/')}/health", timeout=2) as resp:
                return 200 <= getattr(resp, "status", 200) < 300
        except (URLError, TimeoutError, ValueError):
            return False
    return bool(uri)


def _probe_ibkr_socket() -> bool:
    """Non-blocking TCP probe; True if the TWS socket is listening."""
    import socket
    try:
        with socket.create_connection((CONFIG.ibkr_host, CONFIG.ibkr_port), timeout=3):
            return True
    except OSError:
        return False

# ---------------------------------------------------------------------------
# Market data
# ---------------------------------------------------------------------------

def _extract_close_series(history: Any) -> Any:
    if history is None or len(history.index) == 0:
        raise HTTPException(status_code=404, detail="No pricing data returned")

    pandas_module = _require_package("pandas", pd)

    if isinstance(history.columns, pandas_module.MultiIndex):
        close_cols = [c for c in history.columns if str(c[0]) == "Close"]
        if not close_cols:
            raise HTTPException(status_code=502, detail="Close column missing")
        close_series = history[close_cols[0]]
    else:
        if "Close" not in history.columns:
            raise HTTPException(status_code=502, detail="Close column missing")
        close_series = history["Close"]

    return close_series.astype(float)


def get_price_history(
    ticker: str,
    period: Optional[str] = None,
    interval: Optional[str] = None,
) -> Any:
    yf_module = _require_package("yfinance", yf)
    _require_package("pandas", pd)
    symbol = _sanitize_ticker(ticker)
    req_period = period or CONFIG.default_history_period
    req_interval = interval or CONFIG.default_history_interval

    for p, i in [(req_period, req_interval), ("2y", "1d"), ("1y", "1d")]:
        try:
            hist = yf_module.download(
                symbol, period=p, interval=i,
                auto_adjust=False, progress=False, threads=False,
            )
        except Exception as exc:
            logger.warning("yfinance download failed %s: %s", symbol, exc)
            hist = None
        if hist is not None and not hist.empty:
            return hist

    try:
        ticker_hist = yf_module.Ticker(symbol).history(
            period=req_period, interval=req_interval, auto_adjust=False
        )
    except Exception as exc:
        logger.warning("Ticker.history failed %s: %s", symbol, exc)
        ticker_hist = None
    if ticker_hist is not None and not ticker_hist.empty:
        return ticker_hist

    raise HTTPException(status_code=404, detail=f"No market data for {symbol}")


def _quote_fallback(ticker: str) -> dict[str, Any]:
    yf_module = _require_package("yfinance", yf)
    symbol = _sanitize_ticker(ticker)
    try:
        fast_info = dict(yf_module.Ticker(symbol).fast_info or {})
    except Exception:
        fast_info = {}
    last = fast_info.get("lastPrice") or fast_info.get("last_price")
    return {
        "ticker": symbol, "timestamp": None, "close": float(last) if _is_finite(last) else None,
        "sma_20": None, "sma_50": None, "rsi_14": None, "signal": None,
        "data_source": "quote_fallback",
    }

# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def _compute_rsi(series: Any, period: int = 14) -> Any:
    pandas_module = _require_package("pandas", pd)
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    loss = loss.replace(0, pandas_module.NA)
    rs = gain / loss
    return (100 - (100 / (1 + rs))).fillna(0)


def _vega_signal(rsi: Optional[float], close: Optional[float], sma_20: Optional[float]) -> str:
    """Vega MTF-ML signal heuristic used by the simple /technical endpoint."""
    if rsi is None or close is None or sma_20 is None:
        return "neutral"
    if rsi < 35 and close > sma_20:
        return "buy"
    if rsi > 68 or close < sma_20:
        return "sell"
    return "neutral"


# ---------------------------------------------------------------------------
# Breakout module helpers
# ---------------------------------------------------------------------------

_VOLUME_MULTIPLIER_THRESHOLD = 1.5   # volume must be ≥ 150 % of rolling avg
_ATR_MIN_RATIO = 0.005               # ATR / close must be ≥ 0.5 % (meaningful move)
_RSI_OVERBOUGHT = 65.0               # higher-TF bias: reject longs above this
_RSI_OVERSOLD = 38.0                 # higher-TF bias: reject shorts below this
_MIN_RISK_RATIO = 1.5                # minimum reward-to-risk required to execute
_MAX_DAILY_LOSS_PCT = 0.02           # 2 % equity daily loss limit (informational)


def _compute_average_volume(history: Any, window: int = 20) -> Optional[float]:
    """Return rolling average volume over the last `window` bars."""
    if history is None or pd is None:
        return None
    pandas_module = _require_package("pandas", pd)
    vol_col = None
    for candidate in ["Volume", ("Volume", "")]:
        if candidate in history.columns:
            vol_col = candidate
            break
    if vol_col is None:
        return None
    series = history[vol_col].astype(float)
    avg = series.rolling(window).mean()
    valid = avg.dropna()
    return float(valid.iloc[-1]) if not valid.empty else None


def _compute_atr(history: Any, period: int = 14) -> Optional[float]:
    """Average True Range over the last `period` bars."""
    if history is None or pd is None:
        return None
    pandas_module = _require_package("pandas", pd)
    try:
        def _col(name: str) -> Any:
            for candidate in [name, (name, "")]:
                if candidate in history.columns:
                    return history[candidate].astype(float)
            return None

        high = _col("High")
        low = _col("Low")
        close_s = _col("Close")
        if high is None or low is None or close_s is None:
            return None
        prev_close = close_s.shift(1)
        tr = pandas_module.concat(
            [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
            axis=1,
        ).max(axis=1)
        atr_series = tr.rolling(period).mean().dropna()
        return float(atr_series.iloc[-1]) if not atr_series.empty else None
    except Exception as exc:
        logger.warning("ATR computation failed: %s", exc)
        return None


def _breakout_decision(
    *,
    ticker: str,
    direction: str,
    close: Optional[float],
    rsi: Optional[float],
    sma_20: Optional[float],
    current_volume: Optional[float],
    avg_volume: Optional[float],
    atr: Optional[float],
    breakout_level: Optional[float],
) -> dict[str, Any]:
    """Apply Vega breakout filters and return {execute, reason, filters}."""
    filters: dict[str, Any] = {}
    rejections: list[str] = []

    # --- Volume filter: ≥ 150 % of rolling average ---
    if current_volume is not None and avg_volume and avg_volume > 0:
        vol_ratio = current_volume / avg_volume
        filters["volume_ratio"] = round(vol_ratio, 3)
        filters["volume_ok"] = vol_ratio >= _VOLUME_MULTIPLIER_THRESHOLD
        if not filters["volume_ok"]:
            rejections.append(
                f"volume ratio {vol_ratio:.2f}x < {_VOLUME_MULTIPLIER_THRESHOLD}x threshold"
            )
    else:
        filters["volume_ok"] = None  # data unavailable — non-blocking

    # --- ATR filter: confirms meaningful price movement ---
    if atr is not None and close and close > 0:
        atr_ratio = atr / close
        filters["atr_ratio"] = round(atr_ratio, 5)
        filters["atr_ok"] = atr_ratio >= _ATR_MIN_RATIO
        if not filters["atr_ok"]:
            rejections.append(
                f"ATR ratio {atr_ratio:.5f} < {_ATR_MIN_RATIO} (low volatility)"
            )
    else:
        filters["atr_ok"] = None

    # --- Higher-timeframe bias (RSI) ---
    if rsi is not None:
        filters["rsi"] = round(rsi, 2)
        if direction == "long" and rsi > _RSI_OVERBOUGHT:
            filters["htf_bias_ok"] = False
            rejections.append(f"RSI {rsi:.1f} > {_RSI_OVERBOUGHT} — overbought, reject long")
        elif direction == "short" and rsi < _RSI_OVERSOLD:
            filters["htf_bias_ok"] = False
            rejections.append(f"RSI {rsi:.1f} < {_RSI_OVERSOLD} — oversold, reject short")
        else:
            filters["htf_bias_ok"] = True
    else:
        filters["htf_bias_ok"] = None

    # --- Breakout level check (price must be at/past the level) ---
    if breakout_level is not None and close is not None:
        if direction == "long":
            filters["above_breakout_level"] = close >= breakout_level
            if not filters["above_breakout_level"]:
                rejections.append(
                    f"close {close:.4f} below breakout level {breakout_level:.4f}"
                )
        else:
            filters["below_breakout_level"] = close <= breakout_level
            if not filters["below_breakout_level"]:
                rejections.append(
                    f"close {close:.4f} above breakout level {breakout_level:.4f}"
                )

    execute = len(rejections) == 0
    reason = (
        "Breakout confirmed: volume surge, ATR expansion, higher-TF bias aligned"
        if execute
        else "; ".join(rejections)
    )
    return {"execute": execute, "reason": reason, "filters": filters}


def _mysql_log_trade(log: TradeLog) -> None:
    """Insert a closed trade into MySQL trades table.
    Uses the same env-var DB credentials as the rest of the platform.
    Creates the table on first use if it doesn't exist.
    """
    try:
        import pymysql  # type: ignore[import]
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="pymysql not installed — cannot write audit log",
        ) from exc

    conn_kwargs = dict(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3307")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "root"),
        database=os.getenv("MYSQL_DATABASE", "mansa_bot"),
        connect_timeout=5,
    )
    try:
        conn = pymysql.connect(**conn_kwargs)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"MySQL connection failed: {exc}",
        ) from exc

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vega_trades (
                    trade_id    VARCHAR(64)  PRIMARY KEY,
                    ticker      VARCHAR(16)  NOT NULL,
                    entry_price DOUBLE       NOT NULL,
                    exit_price  DOUBLE       NOT NULL,
                    pnl         DOUBLE       NOT NULL,
                    broker      VARCHAR(16)  NOT NULL,
                    strategy    VARCHAR(128) NOT NULL,
                    timestamp   DATETIME     NOT NULL
                )
            """)
            cursor.execute("""
                INSERT INTO vega_trades
                    (trade_id, ticker, entry_price, exit_price, pnl, broker, strategy, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    exit_price = VALUES(exit_price),
                    pnl        = VALUES(pnl),
                    timestamp  = VALUES(timestamp)
            """, (
                log.trade_id, log.ticker, log.entry_price,
                log.exit_price, log.pnl, log.broker,
                log.strategy, log.timestamp,
            ))
        conn.commit()
    finally:
        conn.close()


def technical_analysis(history: Any, ticker: str = "") -> dict[str, Any]:
    pandas_module = _require_package("pandas", pd)
    close_series = _extract_close_series(history)
    df = pandas_module.DataFrame(index=history.index)
    df["close"] = close_series
    df["sma_20"] = df["close"].rolling(20).mean()
    df["sma_50"] = df["close"].rolling(50).mean()
    df["rsi_14"] = _compute_rsi(df["close"])
    latest = df.dropna(how="all").tail(1)
    if latest.empty:
        raise HTTPException(status_code=422, detail="Insufficient history for technical analysis")

    row = latest.iloc[0]
    ts = latest.index[-1]
    ts_val = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)

    def _safe(v: Any) -> Optional[float]:
        return float(v) if pandas_module.notna(v) else None

    rsi = _safe(row["rsi_14"])
    close = _safe(row["close"])
    sma_20 = _safe(row["sma_20"])
    return {
        "ticker": _sanitize_ticker(ticker) if ticker else None,
        "timestamp": ts_val,
        "close": close,
        "sma_20": sma_20,
        "sma_50": _safe(row["sma_50"]),
        "rsi_14": rsi,
        "signal": _vega_signal(rsi, close, sma_20),
        "data_source": "price_history",
    }


def fundamental_analysis(ticker: str) -> dict[str, Any]:
    yf_module = _require_package("yfinance", yf)
    symbol = _sanitize_ticker(ticker)
    try:
        info = yf_module.Ticker(symbol).info or {}
    except Exception as exc:
        logger.warning("Ticker.info failed %s: %s", symbol, exc)
        info = {}
    try:
        fast_info = dict(yf_module.Ticker(symbol).fast_info or {})
    except Exception:
        fast_info = {}

    return {
        "ticker": symbol,
        "short_name": info.get("shortName") or info.get("longName") or symbol,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "currency": info.get("currency") or fast_info.get("currency"),
        "market_cap": info.get("marketCap") or fast_info.get("marketCap"),
        "forward_pe": info.get("forwardPE"),
        "profit_margins": info.get("profitMargins"),
        "return_on_equity": info.get("returnOnEquity"),
        "beta": info.get("beta"),
        "data_source": "ticker_info" if info else "fast_info_fallback",
    }


def _log_mlflow(*, ticker: str, technicals: dict, fundamentals: dict) -> dict[str, Any]:
    if mlflow is None:
        return {"logged": False, "reason": "mlflow_not_installed"}
    if not CONFIG.enable_mlflow_logging:
        return {"logged": False, "reason": "mlflow_logging_disabled"}
    if not _mlflow_reachable(CONFIG.mlflow_tracking_uri):
        return {"logged": False, "reason": "tracking_uri_unreachable"}

    artifact_path: Optional[Path] = None
    try:
        mlflow.set_tracking_uri(CONFIG.mlflow_tracking_uri)
        mlflow.set_experiment(CONFIG.mlflow_experiment)

        payload = {"technicals": technicals, "fundamentals": fundamentals}
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix="_vega.json", delete=False) as fh:
            json.dump(payload, fh)
            artifact_path = Path(fh.name)

        numeric: dict[str, float] = {}
        for src in (technicals, fundamentals):
            for k, v in src.items():
                if _is_finite(v):
                    numeric[k] = float(v)

        run_id = "n/a"
        with mlflow.start_run(run_name=f"Vega_{ticker}") as run:
            run_id = run.info.run_id
            mlflow.log_param("bot_name", CONFIG.bot_name)
            mlflow.log_param("ticker", ticker)
            mlflow.log_param("strategy", CONFIG.strategy_name)
            if numeric:
                mlflow.log_metrics(numeric)
            if artifact_path is not None:
                mlflow.log_artifact(str(artifact_path))

        notify_ml_event(
            bot_name="Vega",
            event_label="signal analysis completed",
            fields={
                "symbol": ticker,
                "run_id": run_id,
                "close": (
                    f"{float(technicals.get('close')):.4f}"
                    if _is_finite(technicals.get("close"))
                    else "n/a"
                ),
            },
        )

        return {"logged": True, "tracking_uri": CONFIG.mlflow_tracking_uri, "experiment": CONFIG.mlflow_experiment}
    except (MlflowException, OSError, TypeError, ValueError, RuntimeError) as exc:
        logger.warning("MLflow logging failed: %s", exc)
        return {"logged": False, "reason": str(exc)}
    finally:
        if artifact_path is not None and artifact_path.exists():
            artifact_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Trade execution
# ---------------------------------------------------------------------------

def _notify_discord_trade(bot_name: str, side: str, qty: float, result: dict[str, Any], order_type: str = "market", limit_price: Any = None) -> None:
    """Fire a Discord Bot_Talk notification. Never raises."""
    try:
        from frontend.utils.discord_alpaca import send_discord_trade_notification
        order_id = result.get("order_id")
        id_suffix = f" | order_id: {order_id}" if order_id else ""
        send_discord_trade_notification(
            symbol=str(result.get("ticker", "")),
            side=side,
            qty=qty,
            order_type=order_type,
            limit_price=limit_price,
            status=f"[{bot_name}] {result.get('status', 'submitted')}{id_suffix}",
        )
    except Exception:
        pass


def _submit_alpaca(request: TradeRequest, symbol: str) -> dict[str, Any]:
    api_module = _require_package("alpaca_trade_api", tradeapi)
    if not CONFIG.alpaca_api_key or not CONFIG.alpaca_secret_key:
        raise HTTPException(status_code=400, detail="Alpaca credentials missing")
    api = api_module.REST(CONFIG.alpaca_api_key, CONFIG.alpaca_secret_key, base_url=CONFIG.alpaca_base_url)
    try:
        order = api.submit_order(
            symbol=symbol, qty=request.qty, side=request.side,
            type=request.order_type, time_in_force="gtc",
            limit_price=request.limit_price,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Alpaca order failed: {exc}") from exc
    result = {
        "status": "submitted", "broker": "alpaca", "ticker": symbol,
        "order_id": getattr(order, "id", None),
        "raw_status": getattr(order, "status", None),
    }
    _notify_discord_trade("Vega", request.side, request.qty, result, request.order_type, request.limit_price)
    return result


def _submit_ibkr(request: TradeRequest, symbol: str) -> dict[str, Any]:
    ib_module = _require_package("ib_insync", ib_insync)
    ib = ib_module.IB()
    try:
        ib.connect(CONFIG.ibkr_host, CONFIG.ibkr_port, clientId=CONFIG.ibkr_client_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"IBKR connection failed: {exc}") from exc
    try:
        contract = ib_module.Stock(symbol, "SMART", "USD")
        ib.qualifyContracts(contract)
        if request.order_type == "limit":
            order = ib_module.LimitOrder(request.side.upper(), request.qty, request.limit_price)
        else:
            order = ib_module.MarketOrder(request.side.upper(), request.qty)
        trade = ib.placeOrder(contract, order)
        status = getattr(getattr(trade, "orderStatus", None), "status", None)
        order_id = getattr(getattr(trade, "order", None), "orderId", None)
        result = {"status": status or "submitted", "broker": "ibkr", "ticker": symbol, "order_id": order_id}
        _notify_discord_trade("Vega", request.side, request.qty, result, request.order_type, request.limit_price)
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"IBKR order failed: {exc}") from exc
    finally:
        if ib.isConnected():
            ib.disconnect()


def submit_trade(request: TradeRequest) -> dict[str, Any]:
    symbol = _sanitize_ticker(request.ticker)
    if not CONFIG.enable_trading:
        return {
            "status": "dry_run", "broker": request.broker, "ticker": symbol,
            "qty": request.qty, "side": request.side, "order_type": request.order_type,
            "message": "Trading disabled by VEGA_ENABLE_TRADING",
        }
    if request.order_type == "limit" and request.limit_price is None:
        raise HTTPException(status_code=400, detail="limit_price required for limit orders")
    if request.broker == "ibkr":
        result = _submit_ibkr(request, symbol)
    else:
        result = _submit_alpaca(request, symbol)
    return result


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Vega Bot API online", "fund": CONFIG.fund_name, "strategy": CONFIG.strategy_name}


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "vega_bot",
        "bot_name": CONFIG.bot_name,
        "fund": CONFIG.fund_name,
        "strategy": CONFIG.strategy_name,
        "trading_enabled": CONFIG.enable_trading,
        "ibkr_host": CONFIG.ibkr_host,
        "ibkr_port": CONFIG.ibkr_port,
        "ibkr_socket_reachable": _probe_ibkr_socket(),
        "mlflow_logging_enabled": CONFIG.enable_mlflow_logging,
        "mlflow_tracking_reachable": _mlflow_reachable(CONFIG.mlflow_tracking_uri),
        "dependencies": _dependency_status(),
    }


@app.get("/technical")
def get_technical(ticker: str = Query(...)) -> dict[str, Any]:
    try:
        history = get_price_history(ticker, period="6mo", interval="1d")
        return technical_analysis(history, ticker=ticker)
    except HTTPException as exc:
        if exc.status_code in {404, 502}:
            return _quote_fallback(ticker)
        raise


@app.get("/fundamental")
def get_fundamental(ticker: str = Query(...)) -> dict[str, Any]:
    return fundamental_analysis(ticker)


@app.post("/signal")
def post_signal(request: SignalRequest) -> dict[str, Any]:
    """
    Breakout signal scout.

    Applies three Vega breakout filters:
    • Volume surge  — current bar volume ≥ 150 % of 20-bar rolling average
    • ATR expansion — ATR/close ≥ 0.5 % (non-trivial volatility)
    • Higher-TF bias — RSI must not be overbought for longs / oversold for shorts

    Returns ``execute: true/false`` plus per-filter detail and a full
    technical + fundamental snapshot for downstream use by /execute.
    """
    symbol = _sanitize_ticker(request.ticker)

    # Resolve timeframe → yfinance interval mapping
    _tf_map = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
               "1h": "60m", "4h": "1h", "1d": "1d", "1w": "1wk"}
    interval = _tf_map.get(request.timeframe, "1d")
    period = "1mo" if interval in {"1m", "5m", "15m", "30m"} else "6mo"

    history = get_price_history(symbol, period=period, interval=interval)
    tech = technical_analysis(history, ticker=symbol)
    fund = fundamental_analysis(symbol)

    # Determine direction
    if request.direction == "auto":
        raw_signal = tech.get("signal", "neutral")
        direction = "long" if raw_signal == "buy" else ("short" if raw_signal == "sell" else "neutral")
    else:
        direction = request.direction

    # Breakout filters
    close = tech.get("close")
    rsi = tech.get("rsi_14")
    sma_20 = tech.get("sma_20")
    avg_volume = _compute_average_volume(history)
    live_atr = _compute_atr(history)
    atr = request.atr if request.atr is not None else live_atr

    # Last bar volume
    current_volume: Optional[float] = None
    if yf is not None:
        try:
            yf_module = _require_package("yfinance", yf)
            vol_col = next(
                (c for c in ["Volume", ("Volume", "")] if c in history.columns), None
            )
            if vol_col is not None:
                current_volume = float(history[vol_col].dropna().iloc[-1])
        except Exception:
            pass
    # Allow caller override
    if request.volume is not None:
        current_volume = request.volume

    decision = _breakout_decision(
        ticker=symbol,
        direction=direction,
        close=close,
        rsi=rsi,
        sma_20=sma_20,
        current_volume=current_volume,
        avg_volume=avg_volume,
        atr=atr,
        breakout_level=request.breakout_level,
    )

    mlflow_result = _log_mlflow(ticker=symbol, technicals=tech, fundamentals=fund)
    return {
        "ticker": symbol,
        "direction": direction,
        "timeframe": request.timeframe,
        "signal": tech.get("signal", "neutral"),
        "decision": decision,
        "technicals": tech,
        "fundamentals": fund,
        "mlflow": mlflow_result,
    }


@app.post("/execute")
def post_execute(request: ExecuteRequest) -> dict[str, Any]:
    """
    Execute a breakout trade with position sizing and risk controls.

    Position size is derived from:
        qty = floor( (equity * risk_pct) / |entry - stop_loss| )

    Hard guards:
    • Minimum reward-to-risk of 1.5 : 1 required
    • Daily loss limit flagged at 2 % equity (informational; not enforced live)
    • ``VEGA_ENABLE_TRADING`` must be set to execute a real order
    """
    symbol = _sanitize_ticker(request.ticker)

    # Risk-ratio guard
    if request.risk_ratio < _MIN_RISK_RATIO:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Risk ratio {request.risk_ratio:.2f} below minimum {_MIN_RISK_RATIO}. "
                "Adjust take_profit or stop_loss."
            ),
        )

    risk_per_share = abs(request.entry_price - request.stop_loss)
    if risk_per_share == 0:
        raise HTTPException(status_code=422, detail="entry_price and stop_loss must differ")

    # Position sizing — uses a notional equity of $100 000 when account info is
    # not available; replace with a live account equity lookup when IBKR is live.
    notional_equity = float(os.getenv("VEGA_NOTIONAL_EQUITY", "100000"))
    import math as _math
    qty = max(1, int(_math.floor((notional_equity * request.risk_pct) / risk_per_share)))

    side: Literal["buy", "sell"] = "buy" if request.direction == "long" else "sell"

    trade_req = TradeRequest(
        ticker=symbol,
        qty=float(qty),
        side=side,
        broker=request.broker,
        order_type=request.order_type,
        limit_price=request.entry_price if request.order_type == "limit" else None,
    )

    result = submit_trade(trade_req)
    result["trade_id"] = request.trade_id
    result["entry_price"] = request.entry_price
    result["stop_loss"] = request.stop_loss
    result["take_profit"] = request.take_profit
    result["risk_ratio"] = request.risk_ratio
    result["qty"] = qty
    result["risk_pct"] = request.risk_pct
    result["daily_loss_limit_pct"] = _MAX_DAILY_LOSS_PCT
    return result


@app.post("/log")
def post_log(trade: TradeLog) -> dict[str, Any]:
    """
    Persist a closed trade to the ``vega_trades`` MySQL table for compliance
    and MLflow audit trail.  Table is created automatically on first use.
    """
    _mysql_log_trade(trade)
    mlflow_audit = _log_mlflow(
        ticker=trade.ticker,
        technicals={"pnl": trade.pnl, "entry_price": trade.entry_price, "exit_price": trade.exit_price},
        fundamentals={},
    )
    return {
        "trade_id": trade.trade_id,
        "status": "logged",
        "table": "vega_trades",
        "mlflow": mlflow_audit,
    }


@app.post("/trade")
def post_trade(request: TradeRequest) -> dict[str, Any]:
    """Low-level direct trade endpoint (bypass position sizing)."""
    result = submit_trade(request)
    _notify_bot_trade("Vega", result)
    return result


@app.get("/universe")
def get_universe() -> dict[str, Any]:
    """Return the Vega retail universe of tickers."""
    return {
        "bot": CONFIG.bot_name,
        "fund": CONFIG.fund_name,
        "sector": "Retail",
        "tickers": list(CONFIG.retail_universe),
    }
