"""Procryon live execution test — FTMO Railway bridge + AXI local bridge."""
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from procryon_bot import ProcryonBot, ProcryonConfig  # noqa: E402

# ── ENV CHECK ──────────────────────────────────────────────────────────────────
print("=== ENV CHECK ===")
print("FTMO_MT5_API_URL :", os.getenv("FTMO_MT5_API_URL"))
print("AXI_MT5_API_URL  :", os.getenv("AXI_MT5_API_URL"))
print("MT5_API_URL      :", os.getenv("MT5_API_URL"))

# ── CONFIG ─────────────────────────────────────────────────────────────────────
config = ProcryonConfig.from_env()
print()
print("=== CONFIG ===")
print("fastapi_base_url :", config.fastapi_base_url)
print("mt5_api_url      :", config.mt5_api_url)

bot = ProcryonBot(config)
metrics = bot.bootstrap_demo_models()
print()
print("=== MODEL BOOTSTRAP ===")
print(json.dumps(metrics, indent=2))

# ── BROKER HEALTH + LOGIN ──────────────────────────────────────────────────────
print()
print("=== BROKER HEALTH + LOGIN ===")
brokers = bot.check_brokers(attempt_login=True)
for name, info in brokers.items():
    print(f"{name.upper()}:")
    print(f"  api_url   : {info['api_url']}")
    print(f"  health    : {info['health']}")
    print(f"  connected : {info['connected']}")
    missing = info.get("missing_credentials") or []
    print(f"  missing   : {missing}")
    acc = info.get("account_info") or {}
    if acc:
        print(f"  balance   : {acc.get('balance')}")
        print(f"  equity    : {acc.get('equity')}")
        print(f"  server    : {acc.get('server') or acc.get('trade_server')}")

# ── PROCRYON EVALUATE ──────────────────────────────────────────────────────────
print()
print("=== PROCRYON EVALUATE ===")
result = bot.evaluate_opportunity(
    [0.0036, 0.0029, 0.0041],
    [30, 0.85, 6, 2, 0.78],
)
print(json.dumps(result, indent=2))

# ── MLflow ─────────────────────────────────────────────────────────────────────
print()
print("=== MLFLOW ===")
mlflow_status = bot.check_mlflow()
print(json.dumps(mlflow_status, indent=2))

# ── FULL HEALTH SNAPSHOT ───────────────────────────────────────────────────────
print()
print("=== HEALTH SNAPSHOT ===")
snap = bot.health_snapshot(attempt_broker_login=False, probe_fastapi=False)
for key, value in snap.items():
    if key != "brokers":
        print(f"{key}: {value}")
print("brokers.ftmo.health:", snap.get("brokers", {}).get("ftmo", {}).get("health"))
print("brokers.axi.health :", snap.get("brokers", {}).get("axi", {}).get("health"))
