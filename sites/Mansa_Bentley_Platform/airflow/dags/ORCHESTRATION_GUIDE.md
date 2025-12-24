# 🤖 Bentley Budget Bot - DAG Orchestration Architecture

## 📊 Complete Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   BENTLEY BUDGET BOT PIPELINE                    │
│                  Airbyte → KNIME → MLflow                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Master DAG      │  ← Coordinates entire pipeline
│  (Manual/Daily)  │     Triggers and monitors all stages
└────────┬─────────┘
         │
         ▼
┌──────────────────┐      Dataset: mysql://mansa_bot/binance_ohlcv
│  1. Airbyte      │ ────────────────────────────────┐
│  Sync DAG        │                                  │
│  (@hourly)       │  Ingests external data          │
└──────────────────┘  → Writes to MySQL              │
                                                      │
                                                      ▼
                    ┌──────────────────┐      Dataset: mysql://mansa_bot/knime_processed
                    │  2. KNIME        │ ────────────────────────────────┐
                    │  CLI Workflow    │                                  │
                    │  (Dataset)       │  Processes data                 │
                    └──────────────────┘  → Transforms & Cleans          │
                                                                          │
                                                                          ▼
                                        ┌──────────────────┐
                                        │  3. MLflow       │
                                        │  Logging DAG     │
                                        │  (Dataset)       │  Tracks experiments
                                        └──────────────────┘  → Logs metrics
```

## 🔗 DAG Connections via Datasets

### Orchestration Flow:
1. **Airbyte Sync DAG** (`airbyte_sync_dag`)
   - **Schedule**: `@hourly`
   - **Produces**: `Dataset("mysql://mansa_bot/binance_ohlcv")`
   - **Action**: Fetches data from external sources → MySQL

2. **KNIME CLI Workflow** (`knime_cli_workflow`)
   - **Schedule**: `[airbyte_dataset]` (triggered by Airbyte)
   - **Consumes**: `Dataset("mysql://mansa_bot/binance_ohlcv")`
   - **Produces**: `Dataset("mysql://mansa_bot/knime_processed")`
   - **Action**: Processes raw data → Transformed data

3. **MLflow Logging DAG** (`mlflow_logging_dag`)
   - **Schedule**: `[airbyte_dataset, knime_dataset]` (triggered by both)
   - **Consumes**: Both Airbyte & KNIME datasets
   - **Action**: Logs metrics, tracks experiments

4. **Master Orchestration DAG** (`bentley_master_orchestration`)
   - **Schedule**: `@daily` (or manual trigger)
   - **Action**: Coordinates and monitors all pipeline stages

## 📋 DAG Inventory

| DAG Name | Status | Owner | Schedule | Purpose |
|----------|--------|-------|----------|---------|
| `airbyte_sync_dag` | ✅ Active | airflow | @hourly | Data ingestion from Airbyte |
| `knime_cli_workflow` | ✅ Active | airflow | Dataset | Data processing via KNIME |
| `mlflow_logging_dag` | ✅ Active | bentley-bot | Dataset | Experiment tracking |
| `bentley_master_orchestration` | ✅ NEW | bentley-bot | @daily | Pipeline coordination |
| `bentleybot_dag` | ✅ Active | airflow | Manual | Trading logic |
| `stock_ingestion_pipeline` | ✅ Active | winston | @hourly | Multi-source stock data |
| `tiingo_data_pull` | ✅ Active | airflow | @daily | Tiingo financial data |

## 🎯 Dataset-Driven Architecture

### What are Datasets?
Airflow **Datasets** enable data-aware scheduling where DAGs automatically trigger when their input data is ready. This creates a truly event-driven pipeline.

### Benefits:
- ✅ **Automatic orchestration** - No manual triggers needed
- ✅ **Data lineage** - Track data flow through pipeline
- ✅ **Decoupled DAGs** - Each DAG is independent
- ✅ **Event-driven** - React to data availability

## 🚀 Getting Started

### 1. Enable DAGs in Airflow UI
```bash
# All DAGs start in paused state
# In Airflow UI (http://localhost:8080):
# Toggle the switch next to each DAG to unpause
```

### 2. Verify Dataset Connections
```bash
# In Airflow UI, click on any DAG
# Navigate to "Graph" tab
# Look for dataset connections (shown as orange boxes)
```

### 3. Trigger Master Orchestration
```bash
# Option 1: Via Airflow UI
# Go to DAGs → bentley_master_orchestration → Play button

# Option 2: Via CLI
docker exec bentley-airflow-scheduler airflow dags trigger bentley_master_orchestration

# Option 3: Via VS Code Airflow Extension
# Right-click on bentley_master_orchestration → Trigger DAG
```

### 4. Monitor Pipeline Execution
```bash
# View in Airflow UI:
http://localhost:8080/dags/bentley_master_orchestration/grid

# Or use VS Code Airflow Extension:
# - View DAG runs
# - Check task logs
# - Monitor progress
```

## 📊 VS Code Airflow Extension Features

Once connected, you can:

1. **View DAG Graph** - Visualize task dependencies
2. **Trigger DAGs** - Start pipeline with one click
3. **View Logs** - Debug task execution
4. **Monitor Status** - Real-time DAG status
5. **Browse Datasets** - See dataset lineage

### Access in VS Code:
- Click Airflow icon in sidebar
- Or: `Ctrl+Shift+P` → "Airflow: Open"

## 🔧 Configuration Status

| Component | Status | Details |
|-----------|--------|---------|
| Airflow Webserver | ✅ Running | Port 8080 |
| Airflow Scheduler | ✅ Running | Processing DAGs |
| MySQL Database | ✅ Running | Port 3307 |
| MLflow Server | ✅ Running | Port 5000 |
| VS Code Extension | ✅ Configured | admin/admin |
| DAG Folder | ✅ Mounted | ./dags |
| Dataset Orchestration | ✅ Enabled | 3 datasets defined |

## 📖 Next Steps

### To make orchestration operational:

1. **Unpause all DAGs** in Airflow UI
2. **Configure Airbyte** connection ID in `Airbyt_sync_DAG_3.py`
3. **Configure KNIME** path in `Dag_Knime_CLI.py`
4. **Test individual DAGs** before full orchestration
5. **Monitor execution** via VS Code extension or Airflow UI

### Recommended Testing Order:

```bash
# 1. Test Airbyte sync first
docker exec bentley-airflow-scheduler airflow dags trigger airbyte_sync_dag

# 2. Verify KNIME triggers automatically (via dataset)
# Check in Airflow UI after ~1 minute

# 3. Verify MLflow triggers automatically (via dataset)
# Check in Airflow UI after KNIME completes

# 4. Run full orchestration
docker exec bentley-airflow-scheduler airflow dags trigger bentley_master_orchestration
```

## 🎓 Learning Resources

- [Airflow Datasets Documentation](https://airflow.apache.org/docs/apache-airflow/stable/concepts/datasets.html)
- [Data-Aware Scheduling](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/datasets.html)
- [DAG Dependencies](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html)

---

**Status**: ✅ Orchestration configured and ready to use!  
**Last Updated**: November 23, 2025
