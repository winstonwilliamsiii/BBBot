# Hydra Quick Start

Hydra is the Mansa Health momentum bot. The production scaffold lives in [hydra_bot.py](hydra_bot.py) and exposes FastAPI, Airbyte, Airflow, and MLflow integration points.

## Components

- FastAPI routes: `/hydra/health`, `/hydra/status`, `/hydra/bootstrap`, `/hydra/analyze`, `/hydra/trade`, `/hydra/airbyte-config`
- Airflow DAG: `hydra_mansa_health`
- Airbyte source config: `airbyte/sources/stocktwits/hydra_mansa_config.json`
- MLflow experiment: `Hydra_Mansa_Health`

## Required Environment Variables

Add these to `.env` or your local shell session:

```env
HYDRA_FASTAPI_URL=http://127.0.0.1:5001
HYDRA_AIRBYTE_API_BASE=http://localhost:8001/api/v1
HYDRA_AIRBYTE_CONNECTION_ID=replace-me
HYDRA_AIRFLOW_DAG_ID=hydra_mansa_health
HYDRA_MLFLOW_EXPERIMENT=Hydra_Mansa_Health
HYDRA_ENABLE_TRADING=false
HYDRA_ENABLE_MLFLOW_LOGGING=true
HYDRA_UNIVERSE=XLV,UNH,ELV,CI,CVS,HCA,ISRG,LLY,ABBV
```

For live execution also set:

```env
ALPACA_API_KEY=replace-me
ALPACA_SECRET_KEY=replace-me
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=6
```

## Start Sequence

1. Start the shared FastAPI app:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_control_center_api.ps1
```

2. Verify Hydra is reachable:

```powershell
curl http://localhost:5001/hydra/health
curl http://localhost:5001/hydra/status
```

3. Bootstrap a demo state:

```powershell
curl -X POST http://localhost:5001/hydra/bootstrap
```

4. Analyze a symbol:

```powershell
curl -X POST http://localhost:5001/hydra/analyze `
  -H "Content-Type: application/json" `
  -d '{"ticker":"UNH","news_headlines":["Healthcare leaders upgraded after strong guidance"]}'
```

5. Simulate a trade:

```powershell
curl -X POST http://localhost:5001/hydra/trade `
  -H "Content-Type: application/json" `
  -d '{"broker":"alpaca","ticker":"UNH","action":"BUY","qty":5,"dry_run":true}'
```

## Airbyte

Hydra uses the Stocktwits source config in `airbyte/sources/stocktwits/hydra_mansa_config.json`. Create a connection in Airbyte and export the resulting connection id into `HYDRA_AIRBYTE_CONNECTION_ID`.

Hydra can return its source config directly from FastAPI:

```powershell
curl http://localhost:5001/hydra/airbyte-config
```

## Airflow

The DAG file is `workflows/airflow/dags/hydra_mansa_health_dag.py`.

It runs three stages:

- trigger Hydra Airbyte sync
- scan the configured universe
- log the daily scan to MLflow

If `HYDRA_AIRBYTE_CONNECTION_ID` is not set, the sync stage is skipped instead of failing the DAG.

## MLflow

Hydra logs analysis payloads into the `Hydra_Mansa_Health` experiment when MLflow logging is enabled. Keep `HYDRA_ENABLE_TRADING=false` until both broker credentials and MLflow/Airbyte endpoints are validated.

## Safety Notes

- Hydra defaults to simulated execution.
- Live Alpaca or IBKR submission only happens when `HYDRA_ENABLE_TRADING=true` and the trade endpoint is called with `dry_run=false`.
- The health check targets the shared control-center FastAPI port `5001` by default.