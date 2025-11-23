# Airbyte Cloud Setup Guide

## Current Status
✅ **Placeholder Mode Active** - Orchestration works without actual Airbyte sync

Your Airbyte DAG is now configured as a placeholder that:
- Successfully triggers and updates datasets
- Allows downstream DAGs (KNIME, MLflow) to execute
- Logs configuration instructions when run
- Can be upgraded to full Airbyte Cloud integration when ready

## Why This Works

The dataset-driven orchestration doesn't require actual data transfer to function. When `airbyte_sync_dag` completes, it marks the dataset as "updated," which triggers `knime_cli_workflow` via Airflow's data-aware scheduling.

## To Enable Full Airbyte Cloud Integration

### Step 1: Get Airbyte Cloud Connection ID

1. Log in to Airbyte Cloud: https://cloud.airbyte.com
2. Navigate to **Connections**
3. Find your MySQL → Binance connection
4. Copy the **Connection ID** (looks like: `3fa85f64-5717-4562-b3fc-2c963f66afa6`)

### Step 2: Generate API Key

1. Go to: https://cloud.airbyte.com/workspaces/{your-workspace-id}/settings/api-keys
2. Click **Create API Key**
3. Name it: "Bentley Airflow Integration"
4. Copy the generated key (starts with `abx_...`)

### Step 3: Configure Environment Variables

Add to your `.env` file:

```env
# Airbyte Cloud Configuration
AIRBYTE_API_URL=https://api.airbyte.com/v1
AIRBYTE_CONNECTION_ID=your_connection_id_from_step_1
AIRBYTE_API_KEY=abx_your_api_key_from_step_2
```

### Step 4: Uncomment API Call in DAG

Edit `dags/Airbyt_sync_DAG_3.py` around line 37:

```python
# Uncomment these lines:
import requests
headers = {"Authorization": f"Bearer {api_key}"}
response = requests.post(
    f"{api_url}/jobs",
    json={"connectionId": connection_id, "jobType": "sync"},
    headers=headers
)
response.raise_for_status()
return response.json()
```

### Step 5: Restart Airflow

```powershell
docker-compose -f docker-compose-airflow.yml down
docker-compose -f docker-compose-airflow.yml up -d
```

## Current Workflow (Placeholder Mode)

```
┌─────────────────────┐
│ airbyte_sync_dag    │ ← Runs hourly or manually
│ (placeholder)       │ ← Marks dataset as updated
└──────────┬──────────┘
           │ Dataset: mysql://mansa_bot/binance_ohlcv
           ↓
┌─────────────────────┐
│ knime_cli_workflow  │ ← Triggers automatically
│ (placeholder)       │
└──────────┬──────────┘
           │ Dataset: mysql://mansa_bot/knime_processed
           ↓
┌─────────────────────┐
│ mlflow_logging_dag  │ ← Triggers automatically
│ (stub functions)    │
└─────────────────────┘
```

## Advantages of Placeholder Mode

✅ Test orchestration without external dependencies
✅ Verify dataset-driven triggering works correctly
✅ Develop and test KNIME/MLflow logic independently
✅ No API rate limits or costs during development
✅ Easy to upgrade to production when ready

## Verify Placeholder Works

```powershell
# Trigger Airbyte DAG
docker exec bentley-airflow-scheduler airflow dags trigger airbyte_sync_dag

# Watch logs
docker exec bentley-airflow-scheduler airflow tasks test airbyte_sync_dag trigger_airbyte 2025-11-23

# Should see: "⚠️ Airbyte connection not configured!"
# Followed by: "✅ Dataset update complete"
```

## Database Connection Details (Already Configured)

Your MySQL is configured for Airbyte Cloud access:
- **Host**: 186.112.188.47 (your public IP)
- **Port**: 3307
- **Database**: mansa_bot
- **20 whitelisted users** for Airbyte Cloud IPs (US + EU regions)

See `mysql_config/airbyte_ip_whitelist.sql` for full list.

## Troubleshooting

**"Connection refused" error**: Normal in placeholder mode - DAG handles it gracefully

**Dataset not triggering**: Check Airflow UI → Datasets tab to verify connections

**Want to test without Airbyte**: Current setup already does this! Just trigger `airbyte_sync_dag`

## Next Steps

1. ✅ Test placeholder orchestration (current state)
2. Configure KNIME workflow path in `Dag_Knime_CLI.py`
3. Implement actual MLflow logging in `mlflow_import DAG.py`
4. (Optional) Enable Airbyte Cloud integration when ready

---

**Remember**: The orchestration is fully functional right now. Airbyte Cloud integration is optional and can be added later without disrupting the pipeline.
