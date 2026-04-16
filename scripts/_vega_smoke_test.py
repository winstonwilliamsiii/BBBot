"""
Vega Bot endpoint smoke test — runs against http://127.0.0.1:5001
Execute with: .venv\Scripts\python.exe scripts\_vega_smoke_test.py
"""

import json
import sys
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:5001"
TICKER = "AAPL"
PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
results = []


def get(path, timeout=120):
    url = BASE + path
    print(f"  GET {url} ... ", end="", flush=True)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = json.loads(resp.read())
            print(f"{PASS} {resp.status}")
            return body, resp.status
    except urllib.error.HTTPError as exc:
        body = {}
        try:
            body = json.loads(exc.read())
        except Exception:
            pass
        print(f"{FAIL} HTTP {exc.code}: {body}")
        return body, exc.code
    except Exception as exc:
        print(f"{FAIL} {exc}")
        return {}, 0


def post(path, payload, timeout=120):
    url = BASE + path
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    print(f"  POST {url} ... ", end="", flush=True)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
            print(f"{PASS} {resp.status}")
            return body, resp.status
    except urllib.error.HTTPError as exc:
        body = {}
        try:
            body = json.loads(exc.read())
        except Exception:
            pass
        print(f"{FAIL} HTTP {exc.code}: {body}")
        return body, exc.code
    except Exception as exc:
        print(f"{FAIL} {exc}")
        return {}, 0


def check(label, body, status, expect_status=200, required_keys=None):
    ok = status == expect_status
    if required_keys:
        for k in required_keys:
            if k not in body:
                ok = False
    tag = PASS if ok else FAIL
    print(f"  [{tag}] {label}")
    if not ok:
        print(f"        status={status}, keys={list(body.keys())}")
    results.append((label, ok))


print("\n=== Vega Bot Smoke Test ===\n")

# 1. Main API health
print("[1] Main health")
body, status = get("/healthz", timeout=5)
check("GET /healthz → status ok", body, status, required_keys=["status"])

# 2. Vega health (includes IBKR socket probe + dependencies)
print("\n[2] Vega health")
body, status = get("/vega/healthz", timeout=5)
check(
    "GET /vega/healthz → Vega fields present",
    body, status,
    required_keys=["status", "bot_name", "trading_enabled", "ibkr_socket_reachable", "dependencies"],
)
if "ibkr_socket_reachable" in body:
    print(f"        ibkr_socket_reachable={body['ibkr_socket_reachable']}"
          f"  ibkr_port={body.get('ibkr_port')}")
if "dependencies" in body:
    print(f"        dependencies={body['dependencies']}")

# 3. Technical endpoint (warm-up may take a while due to yfinance)
print(f"\n[3] Technical endpoint — ticker={TICKER} (up to 120s)")
body, status = get(f"/vega/technical?ticker={TICKER}", timeout=120)
check(
    "GET /vega/technical → technical payload present",
    body, status,
    required_keys=["ticker", "rsi_14"],
)
if "rsi_14" in body:
    print(f"        ticker={body.get('ticker')}  rsi_14={body.get('rsi_14'):.2f}"
          f"  signal={body.get('signal')}  close={body.get('close')}")

# 4. Fundamental endpoint
print(f"\n[4] Fundamental — ticker={TICKER}")
body, status = get(f"/vega/fundamental?ticker={TICKER}", timeout=60)
check("GET /vega/fundamental → ticker present", body, status, required_keys=["ticker"])

# 5. Signal endpoint (combined technical + fundamental → Vega signal)
print(f"\n[5] Signal — ticker={TICKER}")
body, status = post("/vega/signal", {"ticker": TICKER, "news_headlines": []}, timeout=120)
check(
    "POST /vega/signal → signal present",
    body, status,
    required_keys=["ticker", "signal", "technicals", "fundamentals"],
)
if "signal" in body:
    print(f"        signal={body['signal']}")

# 6. Trade (dry run — VEGA_ENABLE_TRADING not set)
print("\n[6] Trade (dry run expected)")
trade_payload = {"ticker": TICKER, "side": "buy", "qty": 1, "broker": "ibkr"}
body, status = post("/vega/trade", trade_payload, timeout=15)
check("POST /vega/trade → dry_run status", body, status, required_keys=["status"])
if "status" in body:
    print(f"        status={body['status']}  message={body.get('message', '')}")

# Summary
print("\n=== Results ===")
passed = sum(1 for _, ok in results if ok)
total = len(results)
for label, ok in results:
    tag = PASS if ok else FAIL
    print(f"  [{tag}] {label}")
print(f"\n{passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
