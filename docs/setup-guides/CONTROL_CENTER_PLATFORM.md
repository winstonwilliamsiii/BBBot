# Bentley Control Center Platform

This document describes the current local platform architecture used by Bentley Budget Bot. It reflects the runtime paths that are actually wired in the repo today rather than older Flask-only or single-service assumptions.

## Runtime Topology

- FastAPI control center: `Main.py`
- PowerShell launcher: `start_control_center_api.ps1`
- Streamlit shell: `streamlit_app.py`
- Trading bot page: `pages/08_🤖_Trading_Bot.py`
- Admin control center page: `pages/99_🔧_Admin_Control_Center.py`
- Vercel serverless edge handler: `api/index.py`

The local app model is:

1. Streamlit provides the Bentley UI.
2. FastAPI provides the unified control-center and bot API.
3. MySQL stores trading signals, trade history, and bot data.
4. MLflow tracks experiments and model runs.
5. Docker hosts local service dependencies such as MySQL, MLflow, Airflow, and Airbyte.
6. Railway and Appwrite are optional external services surfaced through health probes.

## FastAPI

The primary local backend is the shared FastAPI application in `Main.py`.

Primary endpoints:

- `/health` and `/status`
- `/platform/health`
- `/platform/architecture`
- `/hydra/*`
- `/triton/*`
- `/procryon/*`
- `/ibkr/*`
- `/admin/liquidity`

Default local URL:

- `http://localhost:5001`

Primary launch paths:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_control_center_api.ps1
```

or

```powershell
c:/Users/winst/BentleyBudgetBot/.venv/Scripts/python.exe -m uvicorn Main:app --host 0.0.0.0 --port 5001 --reload
```

## Bentley UI

The Bentley UI is a Streamlit application that acts as a client of the FastAPI control center.

Key pages for operations:

- `streamlit_app.py` as the app entrypoint
- `pages/08_🤖_Trading_Bot.py` for bot quick-launch and trading visibility
- `pages/99_🔧_Admin_Control_Center.py` for services, brokers, bot management, and platform status

Hydra-specific UI alignment now includes:

- Hydra launch controls in the trading page sidebar
- Hydra quick-launch visibility in the trading page launcher section
- Hydra operations in the admin control center
- platform-level architecture and health visibility in the admin overview

Default local URL:

- `http://localhost:8501`

## MySQL

MySQL is the primary relational store for local and deployed trading state.

Relevant schema paths:

- `mysql_config/ml_trading_bot_schema.sql`
- `migrations/`

Core tables already used by the app include:

- `trading_signals`
- `trades_history`

Hydra persistence now adds:

- `hydra_analysis_runs`
- `hydra_trade_decisions`

Hydra persistence helper:

- `backend/api/hydra_persistence.py`

Resolution behavior:

1. Use `frontend/utils/secrets_helper.py` when available.
2. Fall back to environment variables.
3. Default local fallback is host `127.0.0.1`, port `3307`, database `bentleybot`.

## Railway

Railway is treated as a deployed MySQL provider rather than the primary local runtime.

Current behavior:

- environment-aware MySQL resolution detects Railway-style hosts
- platform health and architecture endpoints surface the resolved provider
- Streamlit admin overview shows the effective MySQL provider

## Appwrite

Appwrite is an optional platform service used for auth, storage, and cloud-side integrations.

Current behavior:

- FastAPI probes `APPWRITE_ENDPOINT` through `/platform/health`
- `/platform/architecture` includes the resolved Appwrite endpoint
- if Appwrite is not configured locally, the service is reported as `not_configured`

## Docker

Docker remains the standard local service orchestration path.

Relevant compose files:

- `docker/docker-compose.yml`
- `docker/docker-compose-consolidated.yml`
- `docker/docker-compose-mlflow.yml`
- `docker/docker-compose-airflow.yml`

Typical local startup:

```powershell
docker compose -f docker/docker-compose.yml up -d
docker compose -f docker/docker-compose-consolidated.yml up -d mysql mlflow
```

## MLflow

MLflow is the experiment and run-tracking layer.

Relevant paths:

- `docker/docker-compose-mlflow.yml`
- `bbbot1_pipeline/mlflow_config.py`

Current behavior:

- FastAPI platform health probes the configured tracking URI
- Hydra and Triton can log analysis and model activity into MLflow
- Streamlit admin services view probes MLflow reachability and presents the resolved URL

Default local URL:

- `http://localhost:5000`

## Vercel

Vercel remains the stateless deployment path for `api/index.py`, but it is not the primary local control-center runtime.

Practical distinction:

- local operations and bot control use FastAPI in `Main.py`
- Vercel remains useful for edge/serverless routing in deployment scenarios

## Hydra Integration

Hydra is now integrated into the shared platform rather than being treated as a standalone script.

Relevant files:

- `hydra_bot.py`
- `backend/api/hydra_persistence.py`
- `workflows/airflow/dags/hydra_mansa_health_dag.py`
- `airbyte/sources/stocktwits/hydra_mansa_config.json`
- `test_hydra_api.ps1`

Current Hydra behavior:

- FastAPI health and status routes are available at `/hydra/health` and `/hydra/status`
- `/hydra/analyze` now returns persistence metadata
- `/hydra/trade` now returns both analysis persistence and trade persistence metadata
- Streamlit trading and admin pages expose Hydra controls
- VS Code tasks support API start, Hydra health test, and Hydra bootstrap smoke tests

## Validation Notes

Validated during this integration pass:

- `tests/test_hydra_bot.py` passes
- Hydra API routing works through the shared FastAPI app
- Hydra persistence wiring is active in the route layer

Known repo-wide debt still present:

- `pages/08_🤖_Trading_Bot.py` has substantial pre-existing flake8 issues unrelated to this Hydra change set
- `pages/99_🔧_Admin_Control_Center.py` also has substantial pre-existing flake8 issues unrelated to this Hydra change set
- `Main.py` still contains older broad exception patterns outside the Hydra edits