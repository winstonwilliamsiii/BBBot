# Mansa Tech - Titan Bot Setup

## 1) Environment

Use `.env.titan.example` as the baseline and copy values into your active `.env`.

Key project-aligned defaults:
- `MYSQL_HOST=127.0.0.1`
- `MYSQL_PORT=3307`
- `MYSQL_USER=root`
- `MYSQL_PASSWORD=root`
- `MYSQL_DATABASE=mansa_bot`
- `MLFLOW_TRACKING_URI=http://localhost:5000`
- `AIRFLOW_BASE_URL=http://localhost:8080`
- `AIRBYTE_BASE_URL=http://localhost:8001`

## 2) Database

Apply Titan schema:

```powershell
docker exec -i bentley-mysql mysql -uroot -proot < mysql_config/mansa_titan_bot_schema.sql
```

This creates:
- `mansa_bot.titan_trades`
- `mansa_bot.titan_service_health`

## 3) Bot Entrypoint

Primary module: `scripts/mansa_titan_bot.py`  
Compatibility entrypoint: `#MANSA_FUND TITAN_BOT.py`

## 4) Dashboard Visualization

Open Streamlit and use page:
- `pages/97_🚀_Titan_Bot_Monitor.py`

It displays:
- Titan trade metrics
- MLflow/Airflow/Airbyte health status
- Recent Titan trade table
- Prediction probability trend chart

## 5) Tests

Run:

```powershell
pytest tests/test_mansa_titan_bot.py -q
```
