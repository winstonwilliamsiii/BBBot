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

import math
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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
