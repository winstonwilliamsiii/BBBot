# MLflow Docker Setup for Bentley Bot

## Overview

MLflow tracking server is configured to use MySQL as the backend store for improved stability and reliability during Airflow-scheduled training runs.

## Architecture

- **MLflow Server**: Runs on port 5000 with gunicorn
- **Backend Store**: MySQL database (`mlflow_db`) on port 3306
- **Artifact Store**: File-based storage at `/mlflow/artifacts`
- **Network**: Connected via Docker Compose network for service discovery

## Key Features

### 1. MySQL Backend (Stable)
- Uses MySQL instead of SQLite for better concurrent access
- Database: `mlflow_db` (auto-created on startup)
- Connection: `mysql+pymysql://root:root@mysql:3306/mlflow_db`

### 2. Startup Reliability
- **Wait-for-MySQL**: Entrypoint script waits up to 60 seconds for MySQL
- **Connection Testing**: Validates MySQL connectivity before starting MLflow
- **Auto-create Database**: Creates `mlflow_db` if it doesn't exist

### 3. Health Checks
- **Test Command**: `curl -f http://localhost:5000/health || curl -f http://localhost:5000/`
- **Start Period**: 60s (allows time for MySQL connection and initialization)
- **Timeout**: 15s
- **Retries**: 5 attempts with 30s intervals

## Usage

### Starting MLflow with Docker Compose

```bash
# From the repository root
cd docker
docker compose -f docker-compose-airflow.yml up mlflow -d

# Check status
docker compose -f docker-compose-airflow.yml ps mlflow

# View logs
docker compose -f docker-compose-airflow.yml logs -f mlflow
```

### Accessing MLflow

- **MLflow UI**: http://localhost:5000
- **From Airflow Worker**: http://mlflow:5000
- **From Python/Scripts**: Use `MLFLOW_TRACKING_URI=http://localhost:5000` (host) or `http://mlflow:5000` (container)

## Environment Variables

The MLflow container accepts these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MYSQL_HOST` | `mysql` | MySQL container hostname |
| `MYSQL_PORT` | `3306` | MySQL port |
| `MYSQL_USER` | `root` | MySQL username |
| `MYSQL_PASSWORD` | `root` | MySQL password |
| `MYSQL_DATABASE` | `mlflow_db` | MLflow backend database name |
| `MLFLOW_DEFAULT_ARTIFACT_ROOT` | `/mlflow/artifacts` | Artifact storage location |

## Troubleshooting

### MLflow Container Unhealthy

1. **Check MySQL Connection**:
   ```bash
   docker compose -f docker-compose-airflow.yml logs mysql
   docker compose -f docker-compose-airflow.yml exec mysql mysql -uroot -proot -e "SHOW DATABASES;"
   ```

2. **Check MLflow Logs**:
   ```bash
   docker compose -f docker-compose-airflow.yml logs mlflow
   ```

3. **Verify Network Connectivity**:
   ```bash
   docker compose -f docker-compose-airflow.yml exec airflow-worker ping -c 3 mlflow
   docker compose -f docker-compose-airflow.yml exec airflow-worker curl -v http://mlflow:5000/
   ```

### MLflow Not Logging from Airflow

1. **Verify Environment Variable**:
   ```bash
   docker compose -f docker-compose-airflow.yml exec airflow-worker env | grep MLFLOW
   ```
   Should show: `MLFLOW_TRACKING_URI=http://mlflow:5000`

2. **Test Connection from Worker**:
   ```bash
   docker compose -f docker-compose-airflow.yml exec airflow-worker python3 << 'EOF'
   import mlflow
   mlflow.set_tracking_uri("http://mlflow:5000")
   print(f"MLflow Version: {mlflow.__version__}")
   print(f"Tracking URI: {mlflow.get_tracking_uri()}")
   try:
       experiments = mlflow.search_experiments()
       print(f"Found {len(experiments)} experiments")
   except Exception as e:
       print(f"Error: {e}")
   EOF
   ```

3. **Check Orion Training Logs**:
   ```bash
   cat airflow/config/logs/orion_training_latest.json | grep mlflow_logged
   ```
   Should show: `"mlflow_logged": "true"`

### Rebuild After Changes

If you modify Dockerfile.mlflow or mlflow-entrypoint.sh:

```bash
cd docker
docker compose -f docker-compose-airflow.yml build mlflow --no-cache
docker compose -f docker-compose-airflow.yml up mlflow -d
```

## Files

- `docker/Dockerfile.mlflow` - MLflow container image definition
- `docker/mlflow-entrypoint.sh` - Startup script with MySQL wait logic
- `docker/docker-compose-airflow.yml` - Orchestration configuration
- `scripts/setup/mysql_setup.sql` - MySQL initialization (creates mlflow_db)

## Integration with Orion Training

The Orion bot training flow (`scripts/train_orion_ffnn.py`) automatically:

1. Reads `MLFLOW_TRACKING_URI` from environment (set to `http://mlflow:5000` in Airflow worker)
2. Creates/uses experiment `Orion_FFNN_Gold_RSI`
3. Logs parameters: bot, fund, strategy, days, max_iter, hidden_layer_sizes
4. Logs metrics: train_samples, test_samples, accuracy, precision, recall
5. Logs artifacts: model pickle, scaler pickle
6. Returns `mlflow_logged` flag in result JSON

Training results are persisted to `airflow/config/logs/orion_training_latest.json` for dashboard visibility.

## Scheduled Training

The `stars_orchestration` DAG runs Monday-Friday at 7:00 AM EST and includes:
- Task: `train_orion_model` - Trains Orion FFNN and logs to MLflow
- Notification: Discord webhook to Noomo with run_id and accuracy
- Fail-safe: Training completes even if MLflow is unavailable

## Performance Considerations

- **Workers**: 1 gunicorn worker (sufficient for scheduled training)
- **Timeout**: 180s for long-running model logging operations
- **Worker Class**: sync (simple, stable for our use case)
- **Memory**: Shared with MySQL and Airflow services
- **Artifacts**: File-based storage in `/mlflow/artifacts` (fast local access)

## Future Enhancements

Potential improvements for production scaling:
- [ ] Use PostgreSQL instead of MySQL for better MLflow support
- [ ] Configure S3/MinIO for artifact storage (distributed access)
- [ ] Add Nginx proxy for MLflow UI authentication
- [ ] Increase gunicorn workers for concurrent experiment tracking
- [ ] Add Prometheus metrics exporter for monitoring
