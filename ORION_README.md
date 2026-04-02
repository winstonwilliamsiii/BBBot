# Orion Bot README

## Overview

Orion is the Mansa Minerals bot for Gold RSI cycle evaluation plus scheduled
feed-forward neural network training with Bentley dashboard refresh support.

Primary components:

- Gold RSI cycle runner: `scripts/orion_bot.py`
- FFNN trainer: `scripts/train_orion_ffnn.py`
- Orchestration helper: `scripts/stars_orchestration.py`
- Scheduled Airflow DAG: `airflow/dags/stars_orchestration_dag.py`

## What Orion Does

- Evaluates a Gold RSI signal using GLD price history.
- Falls back to deterministic synthetic data when market data is unavailable.
- Trains a feed-forward neural network on RSI and price-derived features.
- Persists latest training snapshot for dashboard refresh consumers.
- Sends completion notifications to the Noomo Discord channel.

## Schedule

Orion training is wired into the `stars_orchestration` DAG and scheduled for:

- 7:00 AM Monday through Friday
- Timezone: `America/New_York`

Trading branches remain Titan-gated, but Orion training is scheduled to run even
when Titan blocks downstream trade execution.

## Discord Notifications

The Orion orchestration path sends messages through:

- `DISCORD_WEBHOOK_NOOMO`

If that variable is not set, the code falls back to the broader Discord webhook
environment variables already used elsewhere in the repo.

## Runtime Outputs

Latest Orion training snapshot is written to:

- `airflow/config/logs/orion_training_latest.json`

This payload includes:

- training status
- accuracy metrics
- model artifact paths
- Discord delivery result
- whether MLflow logging succeeded

## Manual Commands

Run one Orion RSI cycle:

```powershell
python scripts/orion_bot.py --days 180
```

Run one Orion FFNN training pass:

```powershell
python scripts/train_orion_ffnn.py --days 365 --max-iter 250 --hidden-layer-sizes 32 16
```

Trigger the Airflow DAG manually:

```powershell
docker compose -f docker/docker-compose-airflow.yml exec airflow-webserver airflow dags trigger stars_orchestration
```

## Environment Variables

Common Orion-related settings:

- `MLFLOW_TRACKING_URI`
- `DISCORD_WEBHOOK_NOOMO`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `BENTLEY_REPO_ROOT`

## Current Status

Completed:

- Orion weekday 7:00 AM Airflow schedule is in place.
- Orion training runs from the orchestration path.
- Noomo Discord notifications are verified.
- Dashboard refresh snapshot generation is verified.

Open follow-up:

- MLflow reliability for the containerized Airflow worker path is being tracked in
  GitHub issue `#39`.

Issue link:

- `https://github.com/winstonwilliamsiii/BBBot/issues/39`

## Known Limitation

When the MLflow service inside Docker is unhealthy or still warming up, Orion
training completes but may record `"mlflow_logged": "false"` in the latest
snapshot. Training and Discord notification still complete successfully.

## Related Files

- `scripts/orion_bot.py`
- `scripts/train_orion_ffnn.py`
- `scripts/stars_orchestration.py`
- `airflow/dags/stars_orchestration_dag.py`
- `docker/docker-compose-airflow.yml`
- `docker/Dockerfile.mlflow`
