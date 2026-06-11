# Triton Quick Start

Triton is the Mansa Transportation swing bot. It runs on the shared FastAPI control-center backend, surfaces through the Bentley UI quick-launch buttons, uses the shared MySQL and platform health stack, and can log signal runs to MLflow.

## Runtime Paths

- FastAPI app: `Main.py`
- Triton runtime: `triton_bot.py`
- Control-center wrapper: `bentley-bot/bots/triton.py`
- Launcher: `start_bot_mode.ps1`
- Streamlit quick launch: `pages/08_🤖_Trading_Bot.py`

## Start the Stack

```powershell
# Start the shared FastAPI app
powershell -ExecutionPolicy Bypass -File .\start_control_center_api.ps1

# Optional: start local MySQL/MLflow through Docker
docker compose -f docker/docker-compose-consolidated.yml up -d mysql mlflow
```

Platform assumptions:
- FastAPI control center: `http://localhost:5001`
- Bentley UI: `http://localhost:8501`
- MLflow: `http://localhost:5000`
- Local MySQL: `127.0.0.1:3307`
- Railway/Appwrite stay external and are reported through shared health endpoints

## Triton API

```powershell
# Health
curl http://localhost:5001/triton/health

# Status
curl http://localhost:5001/triton/status

# Bootstrap demo state
curl -X POST http://localhost:5001/triton/bootstrap

# Analyze a transport ticker
curl -X POST http://localhost:5001/triton/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker":"IYT","news_headlines":["Parcel and rail demand improved this week"]}'
```

## ON/OFF Launcher

```powershell
# Enable Triton in paper mode
powershell -ExecutionPolicy Bypass -File .\start_bot_mode.ps1 -Bot Triton -Mode ON -Broker Alpaca -TradingMode paper

# Disable Triton
powershell -ExecutionPolicy Bypass -File .\start_bot_mode.ps1 -Bot Triton -Mode OFF -Broker Alpaca -TradingMode paper
```

Launcher behavior:
- Persists Triton active state to `config/broker_modes.json`
- Writes launcher events to `logs/bot_mode_events.jsonl`
- Writes latest event to `logs/last_bot_mode_event.json`
- Runs a local Triton bootstrap probe on `ON`

## MLflow

Triton logs to:
- `TRITON_MLFLOW_TRACKING_URI`, if set
- otherwise `MLFLOW_TRACKING_URI`

Default experiment:
- `Triton_Mansa_Transportation`

## Architecture Notes

- FastAPI is the primary local API layer.
- Vercel `api/index.py` stays stateless for deployment-specific endpoints.
- Docker remains the local service orchestration path.
- Railway hosts MySQL in deployed environments.
- Appwrite remains available for auth/storage integrations reported by platform health.