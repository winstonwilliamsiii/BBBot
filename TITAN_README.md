# Titan Bot README

## Overview
Titan Bot (`scripts/mansa_titan_bot.py`) is a tech-focused trading bot module aligned with the Bentley platform.

Core capabilities:
- Alpaca execution support
- MySQL persistence for trade and service-health logs
- MLflow prediction integration
- Airflow and Airbyte health checks
- Screener-based candidate loading

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
