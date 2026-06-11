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

Dedicated Vega runtime entrypoint:
- `scripts/vega_bot.py`

## 3.1) Switch Titan/Vega without code edits

Shared config file:
- `config/fundamentals_bots.yml`

Scaffolded bot keys (13):
- `Titan_Bot`
- `Vega_Bot`
- `Rigel_Bot`
- `Dogon_Bot`
- `Orion_Bot`
- `Sirius_Bot`
- `Altair_Bot`
- `Deneb_Bot`
- `Arcturus_Bot`
- `Polaris_Bot`
- `Betelgeuse_Bot`
- `Procyon_Bot`
- `Antares_Bot`

How switching works:
- Set `active_bot` in YAML to `Titan_Bot` or `Vega_Bot`, then run the bot normally.
- Optional override from environment: `ACTIVE_BOT=Titan_Bot` (or `Vega_Bot`).
- Optional custom file path: `BOT_CONFIG_PATH=path/to/your.yml`.
- Vega_Bot uses the display fund label `Mansa_Retail` and strategy label `Vega Mansa Retail MTF-ML` in current dashboard surfaces.

Example:

```yaml
active_bot: Vega_Bot
bots:
	Titan_Bot:
		strategy_label: Tech_Fundamentals_Mag7
	Vega_Bot:
		strategy_label: Vega Mansa Retail MTF-ML
```

## 3.2) Vega automation

Register the task expected by Admin Control Center:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup_vega_task.ps1 -Action Create
```

This creates the weekday `Bentley-Vega` task and runs:

- `run_vega.ps1`
- `start_bot_mode.ps1 -Bot Vega -Mode ON -Broker IBKR`
- `scripts/vega_bot.py`

Use `-Action List`, `-Action Test`, or `-Action Delete` for task management.

Runtime override examples:

```powershell
$env:ACTIVE_BOT = "Rigel_Bot"
python "#MANSA_FUND TITAN_BOT.py"
```

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
