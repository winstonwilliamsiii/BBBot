# Triton Bot README

## Overview

Triton Bot (`triton_bot.py`) is a swing-trading runtime for the **Mansa Transportation Fund**. It forecasts transportation leaders and ETFs using multi-factor scoring (ARIMA trend confirmation, technical indicators, fundamental health, sentiment) routed through FastAPI and tracked in MLflow.

**Bot ID:** 7  
**Fund:** Mansa Transportation  
**Strategy:** ARIMA and LSTM Swing Trading  
**Primary Broker:** Alpaca (paper + live)  
**Fallback Broker:** IBKR  

---

## Universe

| Symbol | Description |
|--------|-------------|
| IYT    | iShares Transportation Average ETF (proxy) |
| UNP    | Union Pacific (rail) |
| CSX    | CSX Corporation (rail) |
| NSC    | Norfolk Southern (rail) |
| UPS    | United Parcel Service (logistics) |
| FDX    | FedEx Corporation (logistics) |
| DAL    | Delta Air Lines (air) |
| UBER   | Uber Technologies (mobility) |

---

## Main Files

| File | Purpose |
|------|---------|
| `triton_bot.py` | Core runtime: analysis, scoring, trade execution, MLflow logging |
| `bentley-bot/config/bots/triton.yml` | Bot config: universe, risk, services, Discord settings |
| `tests/test_triton_bot.py` | Unit/integration tests |
| `Main.py` | FastAPI routes: `/triton/*` |
| `pages/99_🔧_Admin_Control_Center.py` | Streamlit admin UI panel |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `ALPACA_API_KEY` | — | Alpaca key (or `APCA_API_KEY_ID`) |
| `ALPACA_SECRET_KEY` | — | Alpaca secret (or `APCA_API_SECRET_KEY`) |
| `ALPACA_BASE_URL` | `https://paper-api.alpaca.markets` | Paper or live Alpaca endpoint |
| `TRITON_ENABLE_TRADING` | `false` | Set `true` to enable live order submission |
| `TRITON_TRADING_MODE` | `paper` | `paper` or `live` |
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | MLflow server |
| `TRITON_MLFLOW_EXPERIMENT` | `Triton_Mansa_Transportation` | Experiment name |
| `DISCORD_BOT_TALK_WEBHOOK` | — | Discord webhook for trade notifications (Bot_Talk channel) |
| `DISCORD_ALPACA_WEBHOOK` | — | Fallback Discord webhook |

---

## FastAPI Routes

Served via `Main.py` (Control Center API) on port **5001**.

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/triton/health` | Health snapshot (broker readiness, MLflow reachability) |
| GET | `/triton/status` | Full status: execution_enabled from `broker_modes.json`, last analysis |
| POST | `/triton/analyze` | Run multi-factor analysis on a ticker |
| POST | `/triton/bootstrap` | Re-initialize bot singleton |
| POST | `/triton/trade` | Submit a trade (BUY/SELL) or dry-run |
| POST | `/triton/configure` | Override config fields at runtime |

### Example: Submit a paper BUY

```powershell
Invoke-WebRequest http://localhost:5001/triton/trade `
  -Method POST -ContentType "application/json" `
  -Body '{"broker":"alpaca","ticker":"IYT","action":"BUY","qty":1,"dry_run":false}'
```

---

## Scoring Model

| Component | Weight | Source |
|-----------|--------|--------|
| Technical score | ~0.65 | RSI, MACD, SMA crossover |
| Fundamental score | ~0.35 | Forward P/E, profit margin, revenue growth, beta |
| Forecast score | 0.0 (if statsmodels absent) | ARIMA(5,1,0) direction bias |
| Composite | Weighted sum | Triggers BUY > 0.18, SELL < −0.18 |

---

## Starting the Bot

### 1. Start the Control Center API

```powershell
# Via VS Code task
# "🚀 Start Control Center API"

# Or directly:
.\.venv\Scripts\python.exe -m uvicorn Main:app --host 0.0.0.0 --port 5001
```

### 2. Turn Triton ON

```powershell
.\start_bot_mode.ps1 -Bot Triton -Mode ON -Broker Alpaca -TradingMode paper
```

This writes `active_bots.Triton: true` to `config/broker_modes.json` and sends a Discord ON notification.

### 3. Verify Status

```powershell
Invoke-WebRequest http://localhost:5001/triton/status | ConvertFrom-Json | Select-Object name, execution_enabled
```

Expected: `execution_enabled: True`

---

## Discord Notifications (Bot_Talk)

Triton sends Discord notifications on every trade (submitted or simulated) via the `Bot_Talk` webhook.

Set the webhook URL in `.env`:

```
DISCORD_BOT_TALK_WEBHOOK=https://discord.com/api/webhooks/...
```

The notification embed includes: symbol, side (BUY/SELL), qty, order type, status, and order_id.

Bot ON/OFF events are also posted to Discord via `start_bot_mode.ps1` using `DISCORD_WEBHOOK`.

---

## MLflow Tracking

Triton logs signal runs to MLflow under the `Triton_Mansa_Transportation` experiment.

```powershell
# Verify MLflow is reachable
Invoke-WebRequest http://localhost:5000/health
```

Each run logs: ticker, action, composite_score, technical_score, fundamental_score, forecast_score.

---

## Risk Parameters

| Parameter | Value |
|-----------|-------|
| Min volume | 500,000 |
| Max daily loss | 1.0% |
| Max open positions | 3 |
| BUY threshold | composite ≥ 0.18 |
| SELL threshold | composite ≤ −0.18 |

---

## Running Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_triton_bot.py -v
```

Tests: 2 — `test_triton_analysis_and_dry_run`, `test_triton_fastapi_routes`

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `execution_enabled: false` in API but bot is ON | Restart the Control Center API — `start_control_center_api.ps1` kills old port-5001 process and reloads `broker_modes.json` |
| `statsmodels not installed` in forecast | Install: `pip install statsmodels` or ignore — Triton degrades gracefully without it |
| Alpaca order fails | Verify `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, and `ALPACA_BASE_URL` |
| No Discord notification | Confirm `DISCORD_BOT_TALK_WEBHOOK` is set in `.env` and non-empty |
| `ib_insync` unavailable | IBKR broker will fail; use `broker: alpaca` in trade requests |
