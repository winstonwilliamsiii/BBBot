"""
Draco endpoint smoke test — runs against http://127.0.0.1:5001
Execute with: .venv\Scripts\python.exe scripts\_draco_smoke_test.py
"""

import json
import sys
import urllib.request
import urllib.error
import urllib.parse

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
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
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


print("\n=== Draco Smoke Test ===\n")

# 1. Main health
print("[1] Main health")
body, status = get("/healthz", timeout=5)
check("GET /healthz → status ok", body, status, required_keys=["status"])

# 2. Draco health
print("\n[2] Draco health")
body, status = get("/draco/healthz", timeout=5)
check("GET /draco/healthz → fields present", body, status,
      required_keys=["status", "trading_enabled", "dependencies"])

# 3. Technical (warm-up may take a while due to yfinance)
print(f"\n[3] Technical endpoint — ticker={TICKER} (up to 120s)")
body, status = get(f"/draco/technical?ticker={TICKER}", timeout=120)
check("GET /draco/technical → technical payload present", body, status, required_keys=["ticker", "rsi_14"])

# 4. Fundamentals
print(f"\n[4] Fundamentals — ticker={TICKER}")
body, status = get(f"/draco/fundamental?ticker={TICKER}", timeout=60)
check("GET /draco/fundamental → ticker present", body, status, required_keys=["ticker"])

# 5. Forecast
print(f"\n[5] Forecast — ticker={TICKER}")
payload = {"ticker": TICKER, "steps": 5}
body, status = post("/draco/forecast", payload, timeout=120)
check("POST /draco/forecast → forecast list", body, status, required_keys=["forecast", "model"])
if "model" in body:
    print(f"        model={body['model']}, forecast={body.get('forecast', [])[:3]}...")

# 6. Sentiment (textblob absent → should return neutral or fallback)
print(f"\n[6] Sentiment — headline")
payload2 = {
    "ticker": TICKER,
    "news_headlines": [
        "Apple reports record revenue",
        "Stock market falls sharply",
    ],
}
body, status = post("/draco/sentiment", payload2, timeout=30)
check(
    "POST /draco/sentiment → sentiment present",
    body,
    status,
    required_keys=["ticker", "sentiment_score"],
)

# 7. Trade (dry run — DRACO_ENABLE_TRADING not set)
print("\n[7] Trade (dry run expected)")
trade_payload = {
    "ticker": TICKER,
    "side": "buy",
    "qty": 1,
    "broker": "alpaca",
}
body, status = post("/draco/trade", trade_payload, timeout=15)
check("POST /draco/trade → dry_run status", body, status,
      required_keys=["status"])
if "status" in body:
    print(f"        status={body['status']}")

# Summary
print("\n=== Results ===")
passed = sum(1 for _, ok in results if ok)
total = len(results)
for label, ok in results:
    tag = PASS if ok else FAIL
    print(f"  [{tag}] {label}")
print(f"\n{passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
