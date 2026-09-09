"""
Cosmic Signal Engine — Bentley Budget Bot
==========================================
Braids analytic "head" signals from every bot strategy into a single
Cosmic Score.  Each head independently votes in the range [-1, +1].
The weighted braid produces a final score mapped to three outcomes:

    score > +THRESHOLD  →  BUY  🔥  starfire
    score < -THRESHOLD  →  SELL 🌑  eclipse
    otherwise           →  HOLD ⚖️   cosmic balance

Usage (standalone):
    from frontend.utils.cosmic_signal import compute_cosmic_score
    result = compute_cosmic_score(market_context)

Usage (as FastAPI dependency):
    from frontend.utils.cosmic_signal import CosmicSignalEngine
    engine = CosmicSignalEngine()
    snapshot = engine.evaluate(market_context)
"""

from __future__ import annotations

import csv
import logging
import math
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

BUY_THRESHOLD  =  0.20   # cosmic score must exceed this to fire starfire BUY
SELL_THRESHOLD = -0.20   # cosmic score must be below this to fire eclipse SELL

DECISION_BUY  = "BUY"
DECISION_SELL = "SELL"
DECISION_HOLD = "HOLD"

SYMBOL_STARFIRE = "🔥 starfire"
SYMBOL_ECLIPSE  = "🌑 eclipse"
SYMBOL_BALANCE  = "⚖️  cosmic balance"

# Analytic head names  (these appear in the dashboard and Discord embeds)
HEAD_MOMENTUM    = "Momentum"
HEAD_RSI         = "RSI"
HEAD_SENTIMENT   = "Sentiment"
HEAD_VOLATILITY  = "Volatility"
HEAD_LIQUIDITY   = "Liquidity"
HEAD_ML_CONF     = "ML Confidence"
HEAD_SPREAD      = "Spread / Slippage"
HEAD_MULTIFRAME  = "Multi-Timeframe"

# Default head weights (must sum to 1.0)
DEFAULT_WEIGHTS: Dict[str, float] = {
    HEAD_MOMENTUM:   0.20,
    HEAD_RSI:        0.15,
    HEAD_SENTIMENT:  0.15,
    HEAD_VOLATILITY: 0.10,
    HEAD_LIQUIDITY:  0.10,
    HEAD_ML_CONF:    0.20,
    HEAD_SPREAD:     0.05,
    HEAD_MULTIFRAME: 0.05,
}


# ─── Market data ingestion ───────────────────────────────────────────────────
#
# Real data source priority: Alpaca (if ALPACA_API_KEY/ALPACA_SECRET_KEY are
# configured) → yfinance (always-available fallback, no credentials needed).
# Both paths normalise to the same simple dict shape so the analytic heads
# below never need to know which provider served the data.

_ALPACA_CONNECTOR: Any = None
_ALPACA_INIT_ATTEMPTED = False


def _get_alpaca_connector():
    """Lazily construct a single shared AlpacaConnector instance.

    Returns ``None`` (and logs a warning, once) if credentials are missing
    or the connector otherwise fails to initialize. Never raises.
    """
    global _ALPACA_CONNECTOR, _ALPACA_INIT_ATTEMPTED
    if _ALPACA_CONNECTOR is not None:
        return _ALPACA_CONNECTOR
    if _ALPACA_INIT_ATTEMPTED:
        return None
    _ALPACA_INIT_ATTEMPTED = True

    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        logger.warning(
            "Cosmic Signal Engine: ALPACA_API_KEY/ALPACA_SECRET_KEY not set — "
            "falling back to yfinance for market data."
        )
        return None
    try:
        from frontend.components.alpaca_connector import AlpacaConnector

        paper = str(os.getenv("ALPACA_PAPER", "true")).strip().lower() != "false"
        _ALPACA_CONNECTOR = AlpacaConnector(api_key=api_key, secret_key=secret_key, paper=paper)
        return _ALPACA_CONNECTOR
    except Exception as exc:  # noqa: BLE001 - never let data-source setup crash callers
        logger.warning("Cosmic Signal Engine: Alpaca connector unavailable (%s); using yfinance fallback.", exc)
        return None


def _fetch_bars_alpaca(symbol: str, lookback: int) -> Optional[Dict[str, List[float]]]:
    connector = _get_alpaca_connector()
    if connector is None:
        return None
    try:
        raw = connector.get_bars(symbol, timeframe="1Day", limit=max(lookback + 5, 20))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cosmic Signal Engine: Alpaca get_bars(%s) raised %s", symbol, exc)
        return None
    if not raw or not raw.get("bars"):
        logger.warning("Cosmic Signal Engine: Alpaca returned no bars for %s", symbol)
        return None
    bars = raw["bars"]
    try:
        closes = [float(b["c"]) for b in bars]
        highs = [float(b["h"]) for b in bars]
        lows = [float(b["l"]) for b in bars]
        volumes = [float(b.get("v", 0.0)) for b in bars]
    except (KeyError, TypeError, ValueError) as exc:
        logger.warning("Cosmic Signal Engine: malformed Alpaca bar payload for %s (%s)", symbol, exc)
        return None
    return {"close": closes, "high": highs, "low": lows, "volume": volumes, "source": "alpaca"}


def _fetch_bars_yfinance(symbol: str, lookback: int) -> Optional[Dict[str, List[float]]]:
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        logger.warning("Cosmic Signal Engine: yfinance not installed — cannot fetch market data for %s", symbol)
        return None
    try:
        period_days = max(lookback + 10, 30)
        df = yf.download(
            symbol,
            period=f"{period_days}d",
            interval="1d",
            progress=False,
            auto_adjust=False,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cosmic Signal Engine: yfinance download failed for %s (%s)", symbol, exc)
        return None
    if df is None or df.empty:
        logger.warning("Cosmic Signal Engine: yfinance returned empty data for %s", symbol)
        return None

    # yfinance may return a MultiIndex column frame for some queries — flatten it.
    if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
        try:
            df = df.xs(symbol, axis=1, level=1)
        except Exception:
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

    try:
        closes = [float(v) for v in df["Close"].dropna().tolist()]
        highs = [float(v) for v in df["High"].dropna().tolist()]
        lows = [float(v) for v in df["Low"].dropna().tolist()]
        volumes = [float(v) for v in df["Volume"].dropna().tolist()]
    except (KeyError, TypeError, ValueError) as exc:
        logger.warning("Cosmic Signal Engine: malformed yfinance frame for %s (%s)", symbol, exc)
        return None
    if not closes:
        logger.warning("Cosmic Signal Engine: no usable close prices from yfinance for %s", symbol)
        return None
    return {"close": closes, "high": highs, "low": lows, "volume": volumes, "source": "yfinance"}


# Small in-process cache so a single scheduler tick doesn't hammer the API
# once per bot for the same symbol.
_MARKET_DATA_CACHE: Dict[str, tuple] = {}
_MARKET_DATA_TTL_SECS = float(os.getenv("COSMIC_MARKET_DATA_TTL", "60"))


def _configured_bot_symbol(bot_name: str) -> Optional[str]:
    """Return the first configured screener symbol for a scheduled bot."""
    screener_files = {
        "VEGA": Path(__file__).resolve().parents[2]
        / "bentley-bot"
        / "config"
        / "vega_retail_breakout.csv",
    }
    screener_file = screener_files.get(bot_name.upper())
    if screener_file is None:
        return None

    try:
        with screener_file.open(newline="", encoding="utf-8") as csv_file:
            row = next(csv.DictReader(csv_file), None)
    except (OSError, csv.Error) as exc:
        logger.warning(
            "Cosmic Signal Engine: unable to read %s screener %s (%s)",
            bot_name,
            screener_file,
            exc,
        )
        return None

    if row is None:
        logger.warning(
            "Cosmic Signal Engine: configured screener for %s is empty", bot_name
        )
        return None
    return str(row.get("Symbol") or row.get("symbol") or "").strip().upper() or None


def fetch_market_series(symbol: str, lookback: int = 30) -> Optional[Dict[str, List[float]]]:
    """Fetch OHLCV series for ``symbol`` trying Alpaca first, then yfinance.

    Returns a dict with ``close``/``high``/``low``/``volume`` float lists
    (oldest → newest) and a ``source`` tag, or ``None`` if no provider could
    supply data (logged as a warning either way).
    """
    if not symbol:
        logger.warning("Cosmic Signal Engine: fetch_market_series called with empty symbol")
        return None

    cache_key = f"{symbol.upper()}:{lookback}"
    cached = _MARKET_DATA_CACHE.get(cache_key)
    if cached and (time.time() - cached[0]) < _MARKET_DATA_TTL_SECS:
        return cached[1]

    data = _fetch_bars_alpaca(symbol, lookback) or _fetch_bars_yfinance(symbol, lookback)
    if data is None:
        logger.warning(
            "Cosmic Signal Engine: no market data available for %s from any source (Alpaca/yfinance)",
            symbol,
        )
        return None

    _MARKET_DATA_CACHE[cache_key] = (time.time(), data)
    return data


def fetch_latest_quote(symbol: str) -> Optional[Dict[str, float]]:
    """Fetch latest bid/ask quote for ``symbol`` via Alpaca. Returns ``None`` on failure."""
    connector = _get_alpaca_connector()
    if connector is None:
        return None
    try:
        raw = connector.get_latest_quote(symbol)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cosmic Signal Engine: Alpaca get_latest_quote(%s) raised %s", symbol, exc)
        return None
    quote = (raw or {}).get("quote")
    if not quote:
        return None
    try:
        bid = float(quote.get("bp", 0.0))
        ask = float(quote.get("ap", 0.0))
    except (TypeError, ValueError):
        return None
    return {"bid": bid, "ask": ask}


# ─── Analytic head computations (real market-data driven) ───────────────────
#
# Each function below pulls from a real OHLCV/quote series and returns a
# float already normalized to [-1, +1] (task requirement #3), logging a
# warning and returning a safe neutral value (0.0) whenever data is missing
# or NaN (task requirement #5). These are the primary entry points named in
# the task; ``run_cosmic_engine_for_bot`` calls them to populate ``context``
# before handing off to the existing ``_eval_*``/``compute_cosmic_score``
# aggregation, which remains unchanged.

def _is_bad_number(value: Any) -> bool:
    return value is None or not isinstance(value, (int, float)) or math.isnan(float(value)) or math.isinf(float(value))


def momentum_head(series: Optional[Dict[str, List[float]]], symbol: str = "") -> float:
    """Short-term price velocity: (current_price - previous_price) / previous_price.

    Returns a value clamped to [-1, +1]; 0.0 (with a logged warning) if data
    is missing or invalid.
    """
    if not series or not series.get("close") or len(series["close"]) < 2:
        logger.warning("momentum_head: insufficient close-price data for %s", symbol)
        return 0.0
    closes = series["close"]
    current_price, previous_price = closes[-1], closes[-2]
    if _is_bad_number(current_price) or _is_bad_number(previous_price) or previous_price == 0:
        logger.warning("momentum_head: NaN/zero previous_price for %s", symbol)
        return 0.0
    raw_momentum = (current_price - previous_price) / previous_price
    # Scale so a ~10% single-bar move saturates the [-1, +1] range.
    score = max(-1.0, min(1.0, raw_momentum * 10.0))
    return score


def rsi_head(series: Optional[Dict[str, List[float]]], period: int = 14, symbol: str = "") -> float:
    """Relative Strength Index over a configurable lookback window, normalized to [-1, +1]."""
    if not series or not series.get("close") or len(series["close"]) < period + 1:
        logger.warning("rsi_head: insufficient close-price history for %s (need %d bars)", symbol, period + 1)
        return 0.0
    closes = series["close"]
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    recent_deltas = deltas[-period:]
    gains = [d for d in recent_deltas if d > 0]
    losses = [-d for d in recent_deltas if d < 0]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        rsi = 100.0 if avg_gain > 0 else 50.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
    if _is_bad_number(rsi):
        logger.warning("rsi_head: computed NaN RSI for %s", symbol)
        return 0.0
    # Oversold (30) → bullish +0.6, overbought (70) → bearish -0.6, matches _eval_rsi mapping.
    score = max(-1.0, min(1.0, (50.0 - rsi) / 50.0))
    return score


def volatility_head(series: Optional[Dict[str, List[float]]], period: int = 14, symbol: str = "") -> float:
    """Standard deviation of returns (or ATR when high/low available), normalized to [-1, +1].

    Low volatility → mildly bullish (less risk), high volatility → bearish.
    """
    if not series or not series.get("close") or len(series["close"]) < 2:
        logger.warning("volatility_head: insufficient close-price data for %s", symbol)
        return 0.0
    closes = series["close"]
    highs = series.get("high") or []
    lows = series.get("low") or []

    atr_bandwidth: Optional[float] = None
    if len(highs) == len(closes) and len(lows) == len(closes) and len(closes) >= 2:
        true_ranges = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            true_ranges.append(tr)
        window = true_ranges[-period:] if len(true_ranges) >= period else true_ranges
        if window and closes[-1]:
            atr = sum(window) / len(window)
            atr_bandwidth = atr / closes[-1] if closes[-1] else None

    if atr_bandwidth is not None and not _is_bad_number(atr_bandwidth):
        bandwidth = atr_bandwidth
    else:
        returns = [
            (closes[i] - closes[i - 1]) / closes[i - 1]
            for i in range(1, len(closes))
            if closes[i - 1]
        ]
        window = returns[-period:] if len(returns) >= period else returns
        if not window:
            logger.warning("volatility_head: could not derive returns for %s", symbol)
            return 0.0
        mean = sum(window) / len(window)
        variance = sum((r - mean) ** 2 for r in window) / len(window)
        bandwidth = math.sqrt(variance)

    if _is_bad_number(bandwidth):
        logger.warning("volatility_head: computed NaN volatility for %s", symbol)
        return 0.0
    # Normalize bandwidth roughly onto [0, 1] (5% daily stdev/ATR treated as "very volatile").
    normalized = min(1.0, max(0.0, bandwidth / 0.05))
    score = max(-1.0, min(1.0, 0.5 - normalized))
    return score


def liquidity_head(
    series: Optional[Dict[str, List[float]]],
    quote: Optional[Dict[str, float]] = None,
    symbol: str = "",
) -> float:
    """Liquidity derived from average volume and/or bid-ask spread, normalized to [-1, +1].

    Prefers bid-ask spread (tighter → more liquid) when a quote is available,
    otherwise falls back to relative average volume trend.
    """
    if quote and quote.get("bid") and quote.get("ask"):
        bid, ask = quote["bid"], quote["ask"]
        if _is_bad_number(bid) or _is_bad_number(ask) or bid <= 0 or ask <= 0:
            logger.warning("liquidity_head: invalid bid/ask for %s", symbol)
        else:
            mid = (bid + ask) / 2.0
            spread_pct = (ask - bid) / mid if mid else None
            if spread_pct is not None and not _is_bad_number(spread_pct):
                # 0% spread → +1 (max liquid), 1% spread → -1 (illiquid).
                normalized = min(1.0, max(0.0, spread_pct / 0.01))
                return max(-1.0, min(1.0, 1.0 - normalized * 2.0))

    if not series or not series.get("volume") or len(series["volume"]) < 2:
        logger.warning("liquidity_head: insufficient volume/quote data for %s", symbol)
        return 0.0
    volumes = series["volume"]
    recent = volumes[-5:] if len(volumes) >= 5 else volumes
    baseline = volumes[-20:] if len(volumes) >= 20 else volumes
    recent_avg = sum(recent) / len(recent)
    baseline_avg = sum(baseline) / len(baseline) if baseline else 0.0
    if baseline_avg <= 0 or _is_bad_number(recent_avg) or _is_bad_number(baseline_avg):
        logger.warning("liquidity_head: NaN/zero volume baseline for %s", symbol)
        return 0.0
    liquidity_ratio = max(0.0, min(2.0, recent_avg / baseline_avg)) / 2.0  # → [0, 1], 0.5 neutral
    score = max(-1.0, min(1.0, (liquidity_ratio - 0.5) * 2.0))
    return score


def ml_confidence_head(
    probability: Optional[float] = None,
    side: str = "buy",
    symbol: str = "",
) -> float:
    """Pull model confidence (probability of buy/sell) from the ML Head output.

    ``probability`` should already be the ML model's own confidence in
    [0, 1] (e.g. a bot's ``evaluate_opportunity()``/``predict_proba()``
    output). Returns 0.0 with a logged warning when unavailable/invalid.
    """
    if probability is None or _is_bad_number(probability):
        logger.warning("ml_confidence_head: missing/NaN model probability for %s", symbol)
        return 0.0
    probability = max(0.0, min(1.0, float(probability)))
    side = str(side or "buy").lower()
    magnitude = (probability - 0.5) * 2.0
    score = magnitude if side in ("buy", "long") else -magnitude
    return max(-1.0, min(1.0, score))


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class HeadSignal:
    """Vote from one analytic head. score ∈ [-1, +1]."""
    head:        str
    score:       float          # -1 (max bearish) … 0 (neutral) … +1 (max bullish)
    weight:      float
    raw:         Dict[str, Any] = field(default_factory=dict)
    explanation: str = ""

    def weighted_contribution(self) -> float:
        return self.score * self.weight


@dataclass
class CosmicSnapshot:
    """Full output of one Cosmic Score evaluation."""
    timestamp:     str
    symbol:        Optional[str]
    cosmic_score:  float          # braided weighted sum ∈ [-1, +1]
    decision:      str            # BUY | SELL | HOLD
    cosmic_symbol: str            # 🔥 starfire | 🌑 eclipse | ⚖️ cosmic balance
    heads:         List[HeadSignal]
    context:       Dict[str, Any] = field(default_factory=dict)
    bot_name:      Optional[str] = None
    mode:          str = "paper"  # paper | live

    def to_dict(self) -> dict:
        d = asdict(self)
        d["heads"] = [asdict(h) for h in self.heads]
        return d


# ─── Head evaluators ─────────────────────────────────────────────────────────

def _eval_momentum(ctx: dict) -> HeadSignal:
    """Score based on short-term price momentum."""
    mom = ctx.get("momentum", ctx.get("price_momentum", 0.0))
    if isinstance(mom, (int, float)) and not math.isnan(mom):
        score = max(-1.0, min(1.0, float(mom)))
    else:
        score = 0.0
    return HeadSignal(
        head=HEAD_MOMENTUM, score=score,
        weight=DEFAULT_WEIGHTS[HEAD_MOMENTUM],
        raw={"momentum": mom},
        explanation=f"price momentum {score:+.3f}",
    )


def _eval_rsi(ctx: dict) -> HeadSignal:
    """Map RSI (0–100) to [-1, +1]. Oversold → bullish, overbought → bearish."""
    rsi = ctx.get("rsi", ctx.get("rsi_value", 50.0))
    try:
        rsi = float(rsi)
    except (TypeError, ValueError):
        rsi = 50.0
    rsi = max(0.0, min(100.0, rsi))
    # Linear mapping: RSI=30 → +0.6 (oversold/bullish), RSI=70 → -0.6 (overbought/bearish)
    score = (50.0 - rsi) / 50.0
    score = max(-1.0, min(1.0, score))
    return HeadSignal(
        head=HEAD_RSI, score=score,
        weight=DEFAULT_WEIGHTS[HEAD_RSI],
        raw={"rsi": rsi},
        explanation=f"RSI {rsi:.1f} → {score:+.3f}",
    )


def _eval_sentiment(ctx: dict) -> HeadSignal:
    """Market / news sentiment score.  Already expected in [-1, +1]."""
    raw = ctx.get("sentiment_score", ctx.get("sentiment", 0.0))
    try:
        score = float(raw)
    except (TypeError, ValueError):
        score = 0.0
    score = max(-1.0, min(1.0, score))
    return HeadSignal(
        head=HEAD_SENTIMENT, score=score,
        weight=DEFAULT_WEIGHTS[HEAD_SENTIMENT],
        raw={"sentiment_score": raw},
        explanation=f"sentiment {score:+.3f}",
    )


def _eval_volatility(ctx: dict) -> HeadSignal:
    """Low volatility → slightly bullish (less risk).  High vol → bearish."""
    vol = ctx.get("volatility_bandwidth", ctx.get("volatility", 0.5))
    try:
        vol = float(vol)
    except (TypeError, ValueError):
        vol = 0.5
    # Bandwidth 0 → +0.5 (very calm), 1 → -0.5 (very volatile)
    score = 0.5 - min(1.0, max(0.0, vol))
    score = max(-1.0, min(1.0, score))
    return HeadSignal(
        head=HEAD_VOLATILITY, score=score,
        weight=DEFAULT_WEIGHTS[HEAD_VOLATILITY],
        raw={"volatility_bandwidth": vol},
        explanation=f"volatility {vol:.3f} → {score:+.3f}",
    )


def _eval_liquidity(ctx: dict) -> HeadSignal:
    """High liquidity ratio → bullish (ample cash to act)."""
    liq = ctx.get("liquidity_ratio", ctx.get("liquidity", 0.5))
    try:
        liq = float(liq)
    except (TypeError, ValueError):
        liq = 0.5
    score = max(-1.0, min(1.0, (liq - 0.5) * 2))
    return HeadSignal(
        head=HEAD_LIQUIDITY, score=score,
        weight=DEFAULT_WEIGHTS[HEAD_LIQUIDITY],
        raw={"liquidity_ratio": liq},
        explanation=f"liquidity {liq:.3f} → {score:+.3f}",
    )


def _eval_ml_confidence(ctx: dict) -> HeadSignal:
    """ML model prediction probability → directional score.

    If bot also supplies predicted_side ('buy'/'sell') we use that to sign
    the score; otherwise we treat probability > 0.5 as bullish.
    """
    prob = ctx.get("execution_probability", ctx.get("prediction_probability", 0.5))
    side = str(ctx.get("predicted_side", ctx.get("action", "buy"))).lower()
    try:
        prob = float(prob)
    except (TypeError, ValueError):
        prob = 0.5
    prob = max(0.0, min(1.0, prob))
    # Convert probability to [-1, +1] centred on 0.5
    magnitude = (prob - 0.5) * 2.0   # ∈ [-1, +1]
    score = magnitude if side in ("buy", "long") else -magnitude
    score = max(-1.0, min(1.0, score))
    return HeadSignal(
        head=HEAD_ML_CONF, score=score,
        weight=DEFAULT_WEIGHTS[HEAD_ML_CONF],
        raw={"probability": prob, "side": side},
        explanation=f"ML p={prob:.3f} side={side} → {score:+.3f}",
    )


def _eval_spread(ctx: dict) -> HeadSignal:
    """Tight spread → bullish for execution.  Wide spread → bearish."""
    spread_bps = ctx.get("average_spread_bps", ctx.get("spread_bps", 20.0))
    try:
        spread_bps = float(spread_bps)
    except (TypeError, ValueError):
        spread_bps = 20.0
    # Normalize: 0 bps → +1, 45 bps (max tolerable) → -1
    score = 1.0 - min(1.0, spread_bps / 45.0) * 2.0
    score = max(-1.0, min(1.0, score))
    return HeadSignal(
        head=HEAD_SPREAD, score=score,
        weight=DEFAULT_WEIGHTS[HEAD_SPREAD],
        raw={"spread_bps": spread_bps},
        explanation=f"spread {spread_bps:.1f} bps → {score:+.3f}",
    )


def _eval_multiframe(ctx: dict) -> HeadSignal:
    """Cross-timeframe alignment.  Expects a list of per-TF scores or a scalar."""
    tf_signals = ctx.get("timeframe_signals", ctx.get("multi_timeframe", None))
    if isinstance(tf_signals, list) and tf_signals:
        try:
            scores = [float(s) for s in tf_signals]
            score = sum(scores) / len(scores)
        except (TypeError, ValueError):
            score = 0.0
    elif isinstance(tf_signals, (int, float)):
        score = float(tf_signals)
    else:
        score = 0.0
    score = max(-1.0, min(1.0, score))
    return HeadSignal(
        head=HEAD_MULTIFRAME, score=score,
        weight=DEFAULT_WEIGHTS[HEAD_MULTIFRAME],
        raw={"timeframe_signals": tf_signals},
        explanation=f"multi-TF alignment {score:+.3f}",
    )


# Ordered head evaluator registry
_HEAD_EVALUATORS = [
    _eval_momentum,
    _eval_rsi,
    _eval_sentiment,
    _eval_volatility,
    _eval_liquidity,
    _eval_ml_confidence,
    _eval_spread,
    _eval_multiframe,
]


# ─── Core function ────────────────────────────────────────────────────────────

def compute_cosmic_score(
    context: Dict[str, Any],
    *,
    symbol: Optional[str] = None,
    bot_name: Optional[str] = None,
    mode: str = "paper",
    weight_overrides: Optional[Dict[str, float]] = None,
) -> CosmicSnapshot:
    """Evaluate all analytic heads and braid them into a Cosmic Score.

    Parameters
    ----------
    context:
        Dict carrying signal inputs (RSI, momentum, probabilities, etc.).
        All keys are optional; missing keys fall back to neutral values.
    symbol:
        Ticker symbol being evaluated (informational).
    bot_name:
        Bot originating the evaluation (informational).
    mode:
        ``"live"`` or ``"paper"``.
    weight_overrides:
        Optional dict mapping head name → weight.  Missing heads keep
        the DEFAULT_WEIGHTS.  Overrides are re-normalised automatically.

    Returns
    -------
    CosmicSnapshot
        Full evaluation result including per-head votes and final decision.
    """
    ctx = dict(context)

    # Apply weight overrides
    weights = dict(DEFAULT_WEIGHTS)
    if weight_overrides:
        weights.update(weight_overrides)
    total_w = sum(weights.values()) or 1.0
    weights = {k: v / total_w for k, v in weights.items()}

    # Evaluate each head
    heads: List[HeadSignal] = []
    for evaluator in _HEAD_EVALUATORS:
        h = evaluator(ctx)
        h.weight = weights.get(h.head, h.weight)
        heads.append(h)

    # Braid
    cosmic_score = sum(h.weighted_contribution() for h in heads)
    cosmic_score = max(-1.0, min(1.0, cosmic_score))

    # Map to decision
    if cosmic_score > BUY_THRESHOLD:
        decision = DECISION_BUY
        cosmic_symbol = SYMBOL_STARFIRE
    elif cosmic_score < SELL_THRESHOLD:
        decision = DECISION_SELL
        cosmic_symbol = SYMBOL_ECLIPSE
    else:
        decision = DECISION_HOLD
        cosmic_symbol = SYMBOL_BALANCE

    return CosmicSnapshot(
        timestamp=datetime.now(timezone.utc).isoformat(),
        symbol=symbol,
        cosmic_score=round(cosmic_score, 6),
        decision=decision,
        cosmic_symbol=cosmic_symbol,
        heads=heads,
        context={k: v for k, v in ctx.items() if not callable(v)},
        bot_name=bot_name,
        mode=mode,
    )


def run_cosmic_engine_for_bot(
    bot_name: str,
    mode: str = "paper",
    *,
    symbol: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate one bot and return the payload needed by ``notify_signal``.

    This is the shared integration boundary for scheduled jobs and other
    callers that need a bot-level Cosmic Signal Engine result. Inputs may be
    supplied per bot through environment variables until bot-specific ML
    adapters are wired in.
    """
    normalized_mode = str(mode).strip().lower()
    if normalized_mode not in {"paper", "live"}:
        raise ValueError("mode must be 'paper' or 'live'")

    symbol = (
        symbol
        or os.getenv(f"COSMIC_SYMBOL_{bot_name.upper()}")
        or os.getenv("COSMIC_DEFAULT_SYMBOL")
        or _configured_bot_symbol(bot_name)
        or "SPY"
    ).strip() or "SPY"
    bot_key = bot_name.upper()

    # --- Live market data ingestion (Alpaca primary, yfinance fallback) ----
    series = fetch_market_series(symbol)
    quote = fetch_latest_quote(symbol)

    # --- ML confidence: prefer an explicit env override (manual testing /
    # bot-specific ML adapters can set this), otherwise fall back to a
    # momentum+RSI-derived proxy so the head is never a flat 0.5/neutral.
    env_probability = os.getenv(f"COSMIC_ML_PROBABILITY_{bot_key}") or os.getenv("COSMIC_ML_PROBABILITY")
    env_side = os.getenv(f"COSMIC_ML_SIDE_{bot_key}") or os.getenv("COSMIC_ML_SIDE")

    momentum_score = momentum_head(series, symbol=symbol)
    rsi_score = rsi_head(series, symbol=symbol)
    volatility_score = volatility_head(series, symbol=symbol)
    liquidity_score = liquidity_head(series, quote=quote, symbol=symbol)

    if env_probability is not None:
        probability = max(0.0, min(1.0, float(env_probability)))
        side = (env_side or "buy").strip().lower()
    else:
        # Derive a proxy confidence from head agreement when no bot-specific
        # ML model output is available, rather than a flat neutral default.
        proxy_signal = (momentum_score + rsi_score) / 2.0
        probability = max(0.0, min(1.0, 0.5 + proxy_signal / 2.0))
        side = "buy" if proxy_signal >= 0 else "sell"
        logger.warning(
            "run_cosmic_engine_for_bot(%s): no ML probability override set; "
            "using momentum/RSI proxy p=%.3f side=%s",
            bot_name, probability, side,
        )
    if side not in {"buy", "sell", "long", "short"}:
        side = "buy"

    ml_confidence_score = ml_confidence_head(probability, side, symbol=symbol)

    # Recompute rsi/volatility/liquidity in the raw units the existing
    # _eval_* evaluators expect (they re-derive the same [-1,+1] score from
    # these raw inputs), so compute_cosmic_score's normalization stays
    # authoritative and consistent with the standalone *_head() outputs above.
    rsi_raw = 50.0 - rsi_score * 50.0
    volatility_raw = max(0.0, min(1.0, 0.5 - volatility_score))
    liquidity_raw = max(0.0, min(1.0, liquidity_score / 2.0 + 0.5))

    if series is None:
        logger.warning(
            "run_cosmic_engine_for_bot(%s): no market data for %s — Momentum/RSI/"
            "Volatility/Liquidity heads will report neutral (0.0) until a data "
            "source is available.",
            bot_name, symbol,
        )

    context = {
        "execution_probability": probability,
        "predicted_side": side,
        "sentiment_score": float(
            os.getenv(f"COSMIC_SENTIMENT_{bot_key}", "0.0")
        ),
        "rsi": rsi_raw,
        "momentum": momentum_score,
        "average_spread_bps": float(
            os.getenv(f"COSMIC_SPREAD_BPS_{bot_key}", "12.0")
        ),
        "volatility_bandwidth": volatility_raw,
        "liquidity_ratio": liquidity_raw,
        "timeframe_signals": [momentum_score, rsi_score],
    }
    snapshot = compute_cosmic_score(
        context,
        symbol=symbol,
        bot_name=bot_name,
        mode=normalized_mode,
    )
    analytic_heads = {
        "Momentum": momentum_score,
        "RSI": rsi_score,
        "Volatility": volatility_score,
        "Liquidity": liquidity_score,
        "ML_Confidence": ml_confidence_score,
        "NS": max(-1.0, min(1.0, context["sentiment_score"])),
        "SD": (
            1.0 if side in {"buy", "long"} else -1.0
        ) * max(0.0, min(1.0, abs(probability - 0.5) * 2.0)),
        "CS": snapshot.cosmic_score,
        "MRC": probability,
        "RP": max(0.0, min(1.0, (snapshot.cosmic_score + 1.0) / 2.0)),
    }
    return {
        "bot_name": bot_name,
        "symbol": symbol,
        "decision": snapshot.decision,
        "cosmic_score": snapshot.cosmic_score,
        "heads": snapshot.to_dict()["heads"],
        "extra_fields": [
            {
                "name": "Scheduler Heads",
                "value": " | ".join(
                    f"{name}={value:+.3f}" for name, value in analytic_heads.items()
                ),
                "inline": False,
            },
            {"name": "ML Head", "value": f"{side} p={probability:.3f}", "inline": True},
            {
                "name": "Data Source",
                "value": (series or {}).get("source", "unavailable") if series else "unavailable",
                "inline": True,
            },
        ],
        "mode": normalized_mode,
        "snapshot": snapshot,
        "trades": [],
        "analytic_heads": analytic_heads,
        "data_source": (series or {}).get("source") if series else None,
    }


# ─── Engine class (stateful caching) ─────────────────────────────────────────

class CosmicSignalEngine:
    """Wrapper that caches the last snapshot per (symbol, bot_name) pair."""

    _TTL_SECONDS = 30  # re-evaluate after 30 s

    def __init__(self) -> None:
        self._cache: Dict[str, tuple[float, CosmicSnapshot]] = {}

    def evaluate(
        self,
        context: Dict[str, Any],
        *,
        symbol: Optional[str] = None,
        bot_name: Optional[str] = None,
        mode: str = "paper",
        force: bool = False,
    ) -> CosmicSnapshot:
        key = f"{bot_name or ''}:{symbol or ''}"
        cached_ts, cached_snap = self._cache.get(key, (0.0, None))  # type: ignore[assignment]

        if not force and cached_snap is not None and (time.monotonic() - cached_ts) < self._TTL_SECONDS:
            return cached_snap

        snap = compute_cosmic_score(
            context, symbol=symbol, bot_name=bot_name, mode=mode
        )
        self._cache[key] = (time.monotonic(), snap)
        return snap

    def last_snapshot(self, symbol: Optional[str] = None, bot_name: Optional[str] = None) -> Optional[CosmicSnapshot]:
        key = f"{bot_name or ''}:{symbol or ''}"
        _, snap = self._cache.get(key, (0.0, None))  # type: ignore[assignment]
        return snap

    def all_snapshots(self) -> List[CosmicSnapshot]:
        return [snap for _, snap in self._cache.values() if snap is not None]


# ─── Module-level singleton ───────────────────────────────────────────────────

_engine = CosmicSignalEngine()


def get_engine() -> CosmicSignalEngine:
    """Return the module-level engine singleton."""
    return _engine


# ─── CLI smoke-test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo_ctx = {
        "rsi": 35,
        "momentum": 0.3,
        "sentiment_score": 0.4,
        "volatility_bandwidth": 0.2,
        "liquidity_ratio": 0.7,
        "execution_probability": 0.72,
        "predicted_side": "buy",
        "average_spread_bps": 8.0,
        "timeframe_signals": [0.3, 0.5, 0.2],
    }
    snap = compute_cosmic_score(demo_ctx, symbol="BTCUSD", bot_name="Procryon", mode="paper")
    print(f"\nCosmic Score: {snap.cosmic_score:+.4f}")
    print(f"Decision: {snap.decision}  {snap.cosmic_symbol}")
    for h in snap.heads:
        print(f"  {h.head:20s}  score={h.score:+.3f}  weight={h.weight:.2f}  → {h.weighted_contribution():+.4f}")
