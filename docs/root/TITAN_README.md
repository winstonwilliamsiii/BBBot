# Titan Bot README

## Overview
Titan Bot (`scripts/mansa_titan_bot.py`) is the **Mansa Tech fund** bot. It targets Mag7 and large-cap technology stocks, screening candidates by fundamental health before applying a CNN sequence model to generate trade signals.

Core capabilities:
- Tech fundamental screening (PE, ROE, debt/equity, volume gates)
- CNN sequence model (`TitanRiskModel/Production`) for risk/signal prediction
- Alpaca execution support
- MySQL persistence for trade and service-health logs
- MLflow prediction integration
- Airflow and Airbyte health checks
- Screener-based candidate loading

---

## Strategy: Tech Fundamentals + CNN Sequence Model

### Fund
Mansa Tech — Bot ID: 1

### Universe
Mag7 + large-cap technology stocks loaded from `titan_tech_fundamentals.csv` (screener output).

### Stage 1: Fundamental Screening

Candidates from the screener are filtered by:

| Rule | Threshold |
|------|-----------|
| Minimum average daily volume | 5,000,000 shares |
| Maximum P/E ratio | 40x |
| Minimum Return on Equity | 15% |
| Maximum Debt-to-Equity ratio | 0.8 |

Candidates that fail any filter are dropped before the ML stage.

### Stage 2: CNN Sequence Model

Titan feeds a sequence of recent price and feature data into a pre-trained CNN:
- Model: `TitanRiskModel/Production` (MLflow model registry)
- Model type: CNN (Convolutional Neural Network) v2 — sequence-to-signal
- Output: risk score / signal confidence
- Prediction artifacts loaded at runtime from MLflow

### Signal Logic

```
IF candidate passes fundamental filters
AND CNN model confidence >= threshold:
    → Signal: BUY
ELSE:
    → Signal: HOLD / SKIP
```

### Position Sizing

| Parameter | Value |
|-----------|-------|
| Default position size | $5,000 |
| Execution | Alpaca (paper by default) |
| Persistence | MySQL (`titan_trades`, `titan_service_health`) |

---

## Main File
- `scripts/mansa_titan_bot.py`

## Default Config Behavior
Titan loads a default profile and can override it from:
- `config/fundamentals_bots.yml`

It reads the active bot from:
- `ACTIVE_BOT` or `BOT_NAME`

If config is missing or invalid, Titan falls back to internal defaults.

## Environment Variables
Common variables used by Titan:
- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`
- `ALPACA_BASE_URL` (default: `https://paper-api.alpaca.markets`)
- `MYSQL_HOST` (default: `127.0.0.1`)
- `MYSQL_PORT` (default: `3307`)
- `MYSQL_USER` (default: `root`)
- `MYSQL_PASSWORD` (default: `root`)
- `MYSQL_DATABASE` (default: `mansa_bot`)
- `TITAN_TRADES_TABLE` (default: `titan_trades`)
- `TITAN_SERVICE_HEALTH_TABLE` (default: `titan_service_health`)
- `MLFLOW_TRACKING_URI` (default: `http://localhost:5000`)
- `TITAN_MODEL_URI` (default: `models:/TitanRiskModel/Production`)
- `AIRFLOW_BASE_URL` (default: `http://localhost:8080`)
- `AIRBYTE_BASE_URL` (default: `http://localhost:8001`)
- `AIRBYTE_CONNECTION_ID`
- `BOT_CONFIG_PATH` (default: `config/fundamentals_bots.yml`)
- `ACTIVE_BOT`
- `BOT_NAME`

## Run Titan
From repo root:

```powershell
python scripts/mansa_titan_bot.py
```

If you are using the local venv in this repo:

```powershell
.\.venv\Scripts\Activate.ps1
python scripts/mansa_titan_bot.py
```

## Related Files
- `tests/test_mansa_titan_bot.py`
- `mysql_config/mansa_titan_bot_schema.sql`
- `scripts/load_screener_csv.py`

## Troubleshooting
- If MySQL connection fails, verify Docker MySQL is running and env vars match your container mapping.
- If config load fails, confirm `config/fundamentals_bots.yml` exists and has valid YAML.
- If trade execution fails, validate Alpaca keys and base URL.
