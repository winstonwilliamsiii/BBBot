#!/usr/bin/env python3
"""
Orion ML Paper Trade — Dual Venue Flow Analysis
================================================
April 16, 2026

Runs a full RSI + FFNN ML signal flow analysis on the Orion minerals basket,
then submits paper trades to BOTH FTMO and AXI via MT5.

Flow:
  1. Fetch today's market data for all scan symbols (GDX, GDXJ, GLD, ...)
  2. Compute FFNN features (ret_1d, ret_5d, vol_10d, sma_ratio, rsi, rsi_delta)
  3. Load orion_ffnn_model.pkl + scaler → predict direction + probability
  4. Combine RSI signal with ML prediction → final signal
  5. Print full flow analysis table
  6. Execute paper trade on FTMO and AXI
  7. Report pass/fail rubric per venue
"""
from __future__ import annotations

import os
import sys
import copy
import dataclasses
import logging
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv(override=False)
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("orion_ml_both")

# ─── Lazy imports ────────────────────────────────────────────────────────────

try:
    import joblib
except ImportError:
    joblib = None

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    from scripts.orion_settings import load_orion_settings
except ModuleNotFoundError:
    from orion_settings import load_orion_settings  # type: ignore[no-redef]

try:
    from scripts.orion_bot import (
        _compute_rsi,
        _evaluate_symbol,
        _execute_broker_order,
        _fetch_symbol_history,
        _signal_from_rsi,
    )
except ModuleNotFoundError:
    from orion_bot import (  # type: ignore[no-redef]
        _compute_rsi,
        _evaluate_symbol,
        _execute_broker_order,
        _fetch_symbol_history,
        _signal_from_rsi,
    )

# ─── Constants ───────────────────────────────────────────────────────────────

MODELS_DIR = PROJECT_ROOT / "models" / "orion"
MODEL_PATH = MODELS_DIR / "orion_ffnn_model.pkl"
SCALER_PATH = MODELS_DIR / "orion_ffnn_scaler.pkl"
FEATURE_COLS = ["ret_1d", "ret_5d", "vol_10d", "sma_ratio", "rsi", "rsi_delta"]
LOOKBACK_DAYS = 60
VENUES = ["ftmo", "axi"]


# ─── Feature engineering ─────────────────────────────────────────────────────

def _build_features_from_history(close: pd.Series) -> Optional[Dict[str, float]]:
    """Compute the FFNN feature vector for the latest bar."""
    if len(close) < 35:
        return None
    ret_1d = close.pct_change(1).iloc[-1]
    ret_5d = close.pct_change(5).iloc[-1]
    vol_10d = close.pct_change(1).rolling(10).std().iloc[-1]
    sma_10 = close.rolling(10).mean().iloc[-1]
    sma_30 = close.rolling(30).mean().iloc[-1]
    sma_ratio = sma_10 / sma_30 if sma_30 and sma_30 != 0 else float("nan")
    rsi_series = pd.Series(index=close.index, dtype=float)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, pd.NA)
    rsi_full = 100 - (100 / (1 + rs))
    rsi_val = float(rsi_full.iloc[-1]) if not pd.isna(rsi_full.iloc[-1]) else float("nan")
    rsi_delta = float(rsi_full.diff().iloc[-1]) if not pd.isna(rsi_full.diff().iloc[-1]) else float("nan")

    if any(np.isnan(v) for v in [ret_1d, ret_5d, vol_10d, sma_ratio, rsi_val, rsi_delta]):
        return None

    return {
        "ret_1d": float(ret_1d),
        "ret_5d": float(ret_5d),
        "vol_10d": float(vol_10d),
        "sma_ratio": float(sma_ratio),
        "rsi": rsi_val,
        "rsi_delta": rsi_delta,
    }


# ─── ML model loader ─────────────────────────────────────────────────────────

def _load_ml_model():
    if joblib is None:
        logger.warning("joblib not available — ML predictions disabled")
        return None, None
    if not MODEL_PATH.exists() or not SCALER_PATH.exists():
        logger.warning("Model artifacts not found at %s — run train_orion_ffnn.py first", MODELS_DIR)
        return None, None
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    logger.info("Loaded FFNN model from %s (trained %s)",
                MODEL_PATH.name,
                datetime.fromtimestamp(MODEL_PATH.stat().st_mtime).strftime("%Y-%m-%d %H:%M"))
    return model, scaler


# ─── Flow analysis ────────────────────────────────────────────────────────────

def run_flow_analysis(days: int = LOOKBACK_DAYS) -> Dict[str, Any]:
    """Fetch data, compute RSI + ML signals, rank symbols."""
    settings = load_orion_settings()
    model, scaler = _load_ml_model()

    rows: List[Dict[str, Any]] = []
    for symbol in settings.scan_symbols:
        prices = _fetch_symbol_history(symbol, days)
        close = pd.to_numeric(prices["Close"], errors="coerce").dropna()
        latest_price = float(close.iloc[-1]) if not close.empty else None
        rsi_val = _compute_rsi(close, period=settings.rsi_period)
        rsi_signal = (
            _signal_from_rsi(rsi_val, settings.rsi_oversold, settings.rsi_overbought)
            if rsi_val is not None
            else "HOLD"
        )

        # ML features + prediction
        ml_signal = "UNKNOWN"
        ml_prob_up = None
        features = _build_features_from_history(close)

        if model is not None and scaler is not None and features is not None:
            x = np.array([[features[f] for f in FEATURE_COLS]])
            x_scaled = scaler.transform(x)
            pred = int(model.predict(x_scaled)[0])
            proba = model.predict_proba(x_scaled)[0]
            ml_prob_up = float(proba[1]) if len(proba) > 1 else float(proba[0])
            ml_signal = "BUY" if pred == 1 else "SELL"
        elif features is None:
            ml_signal = "INSUFFICIENT_DATA"

        # Final signal: require RSI + ML agreement (or RSI only if ML unavailable)
        if ml_signal == "UNKNOWN" or model is None:
            final_signal = rsi_signal
            confirmed = False
        elif rsi_signal == ml_signal and rsi_signal != "HOLD":
            final_signal = rsi_signal
            confirmed = True
        elif rsi_signal == "HOLD" and ml_signal == "BUY" and ml_prob_up is not None and ml_prob_up >= 0.60:
            final_signal = "BUY"
            confirmed = True
        elif rsi_signal == "HOLD" and ml_signal == "SELL" and ml_prob_up is not None and ml_prob_up <= 0.40:
            final_signal = "SELL"
            confirmed = True
        else:
            final_signal = "HOLD"
            confirmed = False

        rows.append({
            "symbol": symbol,
            "latest_price": latest_price,
            "rsi": round(rsi_val, 2) if rsi_val is not None else None,
            "rsi_signal": rsi_signal,
            "ml_signal": ml_signal,
            "ml_prob_up": round(ml_prob_up, 4) if ml_prob_up is not None else None,
            "final_signal": final_signal,
            "confirmed": confirmed,
            "features": features,
        })

    # Rank: confirmed signals first, then by ml_prob_up, then RSI extremity
    def _rank_key(r):
        confirmed_rank = 0 if r["confirmed"] else 1
        if r["final_signal"] == "BUY":
            direction_rank = 0
        elif r["final_signal"] == "SELL":
            direction_rank = 1
        else:
            direction_rank = 2
        prob_rank = -(r["ml_prob_up"] or 0.5)
        return (confirmed_rank, direction_rank, prob_rank)

    ranked = sorted(rows, key=_rank_key)
    selected = ranked[0] if ranked else None

    return {
        "settings": settings,
        "scan_results": ranked,
        "selected": selected,
        "model_loaded": model is not None,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


# ─── Venue execution ─────────────────────────────────────────────────────────

def _run_for_venue(settings, selected: Dict[str, Any], venue: str) -> Dict[str, Any]:
    """Clone settings with venue override, execute paper order."""
    venue_settings = dataclasses.replace(settings, execution_venue=venue.lower())

    symbol = selected["symbol"]
    signal = selected["final_signal"]

    logger.info("Running %s order via %s venue — %s %s",
                signal, venue.upper(), signal, symbol)

    execution = _execute_broker_order(venue_settings, symbol, signal)
    return {"venue": venue, "execution": execution}


# ─── Pretty print ─────────────────────────────────────────────────────────────

def _print_flow_table(analysis: Dict[str, Any]) -> None:
    print("\n" + "=" * 76)
    print("  ORION ML FLOW ANALYSIS — April 16, 2026")
    print(f"  Model loaded: {'YES' if analysis['model_loaded'] else 'NO (RSI-only)'}")
    print(f"  Timestamp:    {analysis['timestamp_utc']}")
    print("=" * 76)
    print(f"  {'Symbol':<8} {'Price':>8} {'RSI':>6} {'RSI-Sig':<10} {'ML-Sig':<10} {'ML-P↑':>7} {'Final':<8} {'OK':>4}")
    print("-" * 76)
    for r in analysis["scan_results"]:
        price_str = f"${r['latest_price']:,.2f}" if r["latest_price"] else "  N/A"
        rsi_str = f"{r['rsi']:5.1f}" if r["rsi"] is not None else "  N/A"
        prob_str = f"{r['ml_prob_up']:.2%}" if r["ml_prob_up"] is not None else "   N/A"
        check = "✓" if r["confirmed"] else " "
        print(
            f"  {r['symbol']:<8} {price_str:>8} {rsi_str:>6}  {r['rsi_signal']:<10} {r['ml_signal']:<10} "
            f"{prob_str:>7}  {r['final_signal']:<8} {check:>4}"
        )

    sel = analysis["selected"]
    prob_label = f"{sel['ml_prob_up']:.2%}" if sel.get("ml_prob_up") is not None else "N/A"
    print("-" * 76)
    print(
        f"\n  ★  SELECTED:  {sel['symbol']} | Signal: {sel['final_signal']} "
        f"| ML-P↑: {prob_label} "
        f"| Confirmed: {'YES' if sel['confirmed'] else 'NO'}"
    )
    print()


def _print_rubric(results: List[Dict[str, Any]]) -> None:
    print("\n" + "=" * 76)
    print("  EXECUTION RUBRIC — Paper Trade Results")
    print("=" * 76)
    for item in results:
        venue = item["venue"].upper()
        ex = item["execution"]
        status = ex.get("status", "unknown")
        ticket = ex.get("paper_ticket", "N/A")
        mode = ex.get("mode", "?")
        detail = ex.get("detail", "")
        symbol = ex.get("execution_symbol", ex.get("selected_symbol", "?"))
        mt5_url = ex.get("mt5_api_url", "?")

        if status in ("submitted", "filled", "accepted"):
            verdict = "PASS"
        elif not ex.get("enabled"):
            verdict = "SKIP (disabled)"
        elif not ex.get("attempted"):
            verdict = "SKIP (no trade signal)"
        else:
            verdict = "FAIL"

        print(f"\n  Venue: {venue}")
        print(f"  [{verdict}] {status.upper()} — {symbol} | mode={mode} | ticket={ticket}")
        print(f"  Bridge:  {mt5_url}")
        print(f"  Detail:  {detail}")

    print()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n[Orion ML Paper Trade — Dual Venue]")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Flow analysis
    logger.info("Running flow analysis across Orion minerals basket...")
    analysis = run_flow_analysis()
    _print_flow_table(analysis)

    selected = analysis["selected"]
    if selected is None:
        print("[ERROR] No symbols evaluated. Aborting.")
        sys.exit(1)

    if selected["final_signal"] == "HOLD":
        print("[INFO] Final signal is HOLD — no paper trade will execute.")
        print("       RSI and ML do not agree on a directional signal today.")
        print()
        # Show what each would look like if forced
        print("  HOLD override: showing what each venue would return...")

    settings = analysis["settings"]

    # 2. Execute both venues
    venue_results = []
    for venue in VENUES:
        try:
            result = _run_for_venue(settings, selected, venue)
            venue_results.append(result)
        except Exception as exc:  # noqa: BLE001
            logger.error("Error running venue %s: %s", venue, exc)
            venue_results.append({
                "venue": venue,
                "execution": {
                    "status": "error",
                    "detail": str(exc),
                    "enabled": True,
                    "attempted": True,
                    "mode": "paper",
                    "mt5_api_url": os.getenv(f"{venue.upper()}_MT5_API_URL", "N/A"),
                },
            })

    # 3. Print rubric
    _print_rubric(venue_results)

    # 4. Save snapshot
    snapshot_path = PROJECT_ROOT / "airflow" / "config" / "logs" / "orion_ml_paper_both_latest.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "timestamp_utc": analysis["timestamp_utc"],
        "model_loaded": analysis["model_loaded"],
        "selected_symbol": selected["symbol"],
        "final_signal": selected["final_signal"],
        "ml_prob_up": selected.get("ml_prob_up"),
        "confirmed": selected["confirmed"],
        "venues": [
            {
                "venue": r["venue"],
                "status": r["execution"].get("status"),
                "ticket": r["execution"].get("paper_ticket"),
                "symbol": r["execution"].get("execution_symbol", selected["symbol"]),
            }
            for r in venue_results
        ],
        "scan_summary": [
            {
                "symbol": r["symbol"],
                "rsi": r["rsi"],
                "rsi_signal": r["rsi_signal"],
                "ml_signal": r["ml_signal"],
                "ml_prob_up": r["ml_prob_up"],
                "final_signal": r["final_signal"],
                "confirmed": r["confirmed"],
            }
            for r in analysis["scan_results"]
        ],
    }
    with open(snapshot_path, "w") as fh:
        json.dump(snapshot, fh, indent=2, default=str)
    print(f"  Snapshot saved → {snapshot_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
