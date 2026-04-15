"""Orion paper trade runner with connectivity check and pass/fail rubric."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(override=False)

# ── Pass/fail rubric ────────────────────────────────────────────────────────
RUBRIC = {
    "submitted":        ("PASS", "Order sent to broker — check AXI portal for ticket"),
    "position_exists":  ("PASS", "Correct position already open — no duplicate needed"),
    "reverse_blocked":  ("WARN", "Opposite position open + close_on_reverse=false — set true in orion.yml"),
    "close_failed":     ("FAIL", "Could not close opposite position — check broker margin/connection"),
    "order_failed":     ("FAIL", "Broker rejected order — check symbol, lot size, margin"),
    "connection_failed":("FAIL", "Bridge up but MT5 terminal not connected — fix Railway MT5_API_URL env var"),
    "missing_credentials":("FAIL", "No creds for venue — ensure AXI_MT5_USER/PASSWORD/HOST in .env"),
    "connector_unavailable":("FAIL", "MT5Connector module not importable"),
    "unsupported_broker":("FAIL", "primary_client must be mt5_client"),
    "unmapped_symbol":  ("FAIL", "Add symbol to orion.yml execution.symbol_map"),
    "skipped":          ("INFO", "Signal is HOLD — no trade today"),
    "disabled":         ("INFO", "Execution disabled in YAML"),
}


def _verdict(status: str) -> str:
    grade, msg = RUBRIC.get(status, ("UNKN", "Unrecognised status"))
    return f"[{grade}] {status}: {msg}"


def main() -> None:
    import requests

    # ── 1. Bridge connectivity check ────────────────────────────────────────
    bridge_url = os.getenv("AXI_MT5_API_URL", "https://bbbot-production.up.railway.app")
    print(f"\n=== Connectivity ===")
    try:
        r = requests.get(f"{bridge_url}/health", timeout=12)
        print(f"  BRIDGE  {r.status_code}  {r.json()}")
    except Exception as exc:
        print(f"  BRIDGE  UNREACHABLE  {exc}")
        print("  ⚠ DNS still not resolved — run: ipconfig /flushdns  then retry")
        sys.exit(1)

    # ── 2. Load settings & verify AXI credential resolution ─────────────────
    from scripts.orion_settings import load_orion_settings
    from scripts.orion_bot import _resolve_mt5_credentials, _resolve_mt5_api_url

    settings = load_orion_settings()
    print(f"\n=== Orion Config ===")
    print(f"  venue          : {settings.execution_venue}")
    print(f"  mode           : {settings.execution_mode}")
    print(f"  execution_enabled: {settings.execution_enabled}")
    print(f"  volume_lots    : {settings.volume_lots}")
    print(f"  rsi_oversold   : {settings.rsi_oversold}  overbought: {settings.rsi_overbought}")

    resolved_url = _resolve_mt5_api_url(settings)
    user, password, host, port = _resolve_mt5_credentials(settings)
    print(f"  mt5_api_url    : {resolved_url}")
    print(f"  mt5_user       : {user or 'MISSING'}")
    print(f"  mt5_host       : {host or 'MISSING'}")
    print(f"  mt5_port       : {port}")

    missing = [k for k, v in [("user", user), ("password", password), ("host", host)] if not v]
    if missing:
        print(f"  ❌ Missing credentials: {missing}")
        sys.exit(1)
    print("  ✅ All AXI credentials present")

    # ── 3. Run full Orion cycle ──────────────────────────────────────────────
    print(f"\n=== Running Orion cycle (days=60) ===")
    from scripts.orion_bot import run_cycle

    result = run_cycle(days=60, log_mlflow=False)

    signal   = result.get("signal", "HOLD")
    symbol   = result.get("selected_symbol", "?")
    rsi_val  = result.get("rsi_value")
    exec_res = result.get("execution", {})
    status   = exec_res.get("status", "unknown")

    print(f"\n=== Cycle Result ===")
    print(f"  selected_symbol: {symbol}")
    print(f"  signal         : {signal}")
    print(f"  rsi_value      : {rsi_val:.2f}" if rsi_val is not None else "  rsi_value      : None")
    print(f"  exec status    : {status}")
    print(f"  exec detail    : {exec_res.get('detail', '')}")
    if exec_res.get('execution_symbol'):
        print(f"  mt5_symbol     : {exec_res['execution_symbol']}")

    print(f"\n=== Pass/Fail Rubric ===")
    print(f"  {_verdict(status)}")

    # Full JSON dump for inspection
    print(f"\n--- Full execution payload ---")
    print(json.dumps(exec_res, indent=2, default=str))


if __name__ == "__main__":
    main()
