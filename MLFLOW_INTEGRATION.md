# MLflow Integration with Airflow - Complete Guide

## 🎯 Overview

This guide explains how to use MLflow with Airflow to track ML workflows and 
experiments in the Bentley Budget Bot project.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Bentley Budget Bot Stack                 │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  Streamlit   │   Airflow    │   Airbyte    │    MLflow      │
│  Port 8501   │  Port 8080   │  Port 8000   │   Port 5000    │
│              │              │              │                │
│ • Portfolio  │ • DAG Mgmt   │ • ETL        │ • Tracking     │
│ • Dashboard  │ • Scheduler  │ • API Sync   │ • Experiments  │
│ • Yahoo Data │ • Workers    │ • Transform  │ • Artifacts    │
└──────────────┴──────────────┴──────────────┴────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              MySQL Database      MLflow Storage
              (Port 3307)         (Artifacts)
```

## 🚀 Quick Start

### 1. Start All Services

```powershell
# Start all services including MLflow
.\manage_services.ps1 -Service all -Action start
```

### 2. Access MLflow UI

Open your browser and navigate to:
- **MLflow UI**: http://localhost:5000

You should see the MLflow tracking interface with experiments.

### 3. Verify Airflow Integration

- **Airflow UI**: http://localhost:8080 (admin/admin)
- Look for the `bentleybot_dag` DAG
- Enable and trigger the DAG
- Monitor execution in Airflow UI
- View tracked metrics in MLflow UI

## 📋 What Was Changed

### 1. Docker Compose Configuration

**File**: `docker-compose-airflow.yml`

Added MLflow service:
```yaml
mlflow:
  container_name: bentley-mlflow
  ports:
    - "5000:5000"
  environment:
    - MLFLOW_BACKEND_STORE_URI=mysql+pymysql://root:root@mysql:3306/mlflow_db
    - MLFLOW_DEFAULT_ARTIFACT_ROOT=/mlflow/artifacts
```

### 2. MySQL Database Setup

**File**: `mysql_setup.sql`

Added MLflow database:
```sql
CREATE DATABASE IF NOT EXISTS mlflow_db;
GRANT ALL PRIVILEGES ON mlflow_db.* TO 'root'@'%';
```

### 3. Airflow Dependencies

**File**: `Dockerfile.airflow`

Added MLflow packages:
```dockerfile
RUN pip install --no-cache-dir \
    mlflow \
    cryptography \
    requests \
    pandas
```

### 4. DAG Code Quality

**File**: `src/Bentleybot_dag.py`

- Fixed all PEP 8 line length violations (max 79 chars)
- Improved code readability
- Maintained all functionality

## 🔧 MLflow Configuration

### Backend Store (Metadata)

MLflow uses MySQL to store:
- Experiment metadata
- Run parameters
- Metrics and tags
- Model registry information

**Connection String**:
```
mysql+pymysql://root:root@mysql:3306/mlflow_db
```

### Artifact Store

MLflow stores artifacts (models, plots, data) in:
```
/mlflow/artifacts
```

This is persisted in a Docker volume: `mlflow_artifacts`

## 📊 Using MLflow in Your DAGs

### Example: Logging Metrics

The `bentleybot_dag` already includes MLflow integration:

```python
import mlflow

def log_to_mlflow():
    # Set tracking server
    mlflow.set_tracking_uri("http://mlflow:5000")
    
    # Set experiment name
    mlflow.set_experiment("BentleyBudgetBot-Trading")
    
    # Start a run and log metrics
    with mlflow.start_run():
        mlflow.log_metric("buy_signals", buy_count)
        mlflow.log_metric("sell_signals", sell_count)
        mlflow.log_artifact("trade_signals.csv")
```

### Key MLflow Functions

1. **`mlflow.set_tracking_uri()`** - Connect to tracking server
2. **`mlflow.set_experiment()`** - Organize runs by experiment
3. **`mlflow.start_run()`** - Begin tracking a run
4. **`mlflow.log_metric()`** - Log numerical metrics
5. **`mlflow.log_param()`** - Log configuration parameters
6. **`mlflow.log_artifact()`** - Save files (models, plots, data)

## 🔍 Troubleshooting

### MLflow UI Not Loading

**Check if service is running:**
```powershell
docker ps | findstr mlflow
```

**View MLflow logs:**
```powershell
docker logs bentley-mlflow
```

**Restart MLflow:**
```powershell
docker restart bentley-mlflow
```

### Connection Issues from Airflow

**Inside Docker network, use container name:**
```python
mlflow.set_tracking_uri("http://mlflow:5000")  # ✓ Correct
```

**From your local machine:**
```python
mlflow.set_tracking_uri("http://localhost:5000")  # ✓ Correct
```

### Database Connection Errors

**Verify MySQL is running:**
```powershell
docker exec -it bentley-mysql mysql -u root -p
# Password: root
```

**Check if mlflow_db exists:**
```sql
SHOW DATABASES;
USE mlflow_db;
SHOW TABLES;
```

### Port Conflicts

If port 5000 is already in use:

1. Check what's using it:
   ```powershell
   netstat -ano | findstr :5000
   ```

2. Kill the process or change MLflow port in 
   `docker-compose-airflow.yml`:
   ```yaml
   ports:
     - "5001:5000"  # Map to different host port
   ```

## 📈 Viewing Experiments

### MLflow UI Features

1. **Experiments Tab**
   - View all experiments
   - Compare runs side-by-side
   - Filter and search runs

2. **Run Details**
   - Parameters and metrics
   - Artifacts (files, models)
   - Tags and notes

3. **Model Registry**
   - Register models
   - Version tracking
   - Stage transitions (Staging, Production)

### Example Workflow

1. **Trigger Airflow DAG** (http://localhost:8080)
   - Navigate to DAGs
   - Enable `bentleybot_dag`
   - Click "Trigger DAG"

2. **Monitor Execution** (Airflow UI)
   - View task progress
   - Check logs for each task
   - Verify `log_mlflow` task completes

3. **View Results** (http://localhost:5000)
   - Go to MLflow UI
   - Select "BentleyBudgetBot-Trading" experiment
   - View latest run with metrics

## 🎓 Best Practices

### 1. Organize with Experiments

```python
# Group related runs
mlflow.set_experiment("portfolio-optimization")
mlflow.set_experiment("risk-analysis")
mlflow.set_experiment("trading-signals")
```

### 2. Log Meaningful Metrics

```python
# Log both training and validation metrics
mlflow.log_metric("train_accuracy", 0.95)
mlflow.log_metric("val_accuracy", 0.92)

# Log business metrics
mlflow.log_metric("profit_usd", 1250.50)
mlflow.log_metric("sharpe_ratio", 1.8)
```

### 3. Version Your Models

```python
# Save and register models
mlflow.sklearn.log_model(model, "model")

# Register in model registry
result = mlflow.register_model(
    f"runs:/{run_id}/model",
    "BentleyBot-Predictor"
)
```

### 4. Tag Your Runs

```python
# Add searchable tags
mlflow.set_tag("model_type", "RandomForest")
mlflow.set_tag("data_version", "v2.0")
mlflow.set_tag("environment", "production")
```

## 🔗 Integration Examples

### Example 1: Portfolio Rebalancing

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
import mlflow

def optimize_portfolio():
    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("portfolio-optimization")
    
    with mlflow.start_run():
        # Your optimization code
        optimal_weights = calculate_weights()
        
        # Log results
        mlflow.log_params({"risk_tolerance": 0.5})
        mlflow.log_metric("expected_return", 0.12)
        mlflow.log_metric("portfolio_variance", 0.03)

dag = DAG("portfolio_optimization", ...)
task = PythonOperator(
    task_id="optimize",
    python_callable=optimize_portfolio,
    dag=dag
)
```

### Example 2: Risk Assessment

```python
def assess_risk():
    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("risk-analysis")
    
    with mlflow.start_run():
        risk_score = calculate_var()
        
        mlflow.log_metric("value_at_risk", risk_score)
        mlflow.log_metric("max_drawdown", 0.15)
        
        # Save risk report
        generate_report("risk_report.html")
        mlflow.log_artifact("risk_report.html")
```

## 📚 Additional Resources

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Airflow MLflow Provider](https://airflow.apache.org/docs/apache-airflow-providers-mlflow/)
- [MLflow on Docker](https://github.com/mlflow/mlflow/tree/master/examples/docker)

## 🆘 Getting Help

If you encounter issues:

1. Check service status: `.\manage_services.ps1 -Action status`
2. View logs: `.\manage_services.ps1 -Service airflow -Action logs`
3. Restart services: `.\manage_services.ps1 -Service all -Action stop` 
   then `.\manage_services.ps1 -Service all -Action start`

## ✅ Verification Checklist

- [ ] All services start without errors
- [ ] MLflow UI accessible at http://localhost:5000
- [ ] Airflow UI accessible at http://localhost:8080
- [ ] Airbyte UI accessible at http://localhost:8000
- [ ] DAG appears in Airflow
- [ ] DAG can be triggered manually
- [ ] MLflow experiment appears after DAG runs
- [ ] Metrics and artifacts logged successfully

---

**Status**: ✅ MLflow integration complete and ready for use!
