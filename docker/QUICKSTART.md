# MLflow Stabilization - Quick Start Guide

## What Was Fixed

The MLflow Docker service was experiencing reliability issues:
- **Before**: Used SQLite backend, became unhealthy during startup, couldn't be reached by Airflow worker
- **After**: Uses MySQL backend with proper startup sequencing, health checks, and validation tools

## Changes Made

### 1. Docker Configuration
- **Dockerfile.mlflow**: Now uses MySQL backend and startup script
- **mlflow-entrypoint.sh**: Waits for MySQL to be ready before starting MLflow
- **docker-compose-airflow.yml**: Configured with MySQL environment variables and extended health check

### 2. Database Setup
- **mysql_setup.sql**: Creates `mlflow_db` database automatically

### 3. Validation Tools
- **validate_mlflow_setup.py**: Comprehensive MLflow connectivity tests
- **check_mlflow_health.sh**: Quick health check script
- **MLFLOW_SETUP.md**: Full documentation

## Getting Started

### Step 1: Start the Stack

```bash
# From repository root
cd docker

# Start all services (MySQL, MLflow, Airflow, Redis)
docker compose -f docker-compose-airflow.yml up -d

# Or start just MLflow and its dependencies
docker compose -f docker-compose-airflow.yml up mysql mlflow -d
```

### Step 2: Verify MLflow Health

```bash
# Quick health check
./check_mlflow_health.sh

# Comprehensive validation
python3 validate_mlflow_setup.py
```

Expected output:
```
✓ PASS: connectivity
✓ PASS: experiment_creation
✓ PASS: run_logging
✓ PASS: mysql_backend
✓ PASS: orion_experiment

Tests Passed: 5/5

✓ ALL TESTS PASSED - MLflow is ready for Orion training!
```

### Step 3: Access MLflow UI

Open browser: http://localhost:5000

You should see the MLflow UI with experiments list.

### Step 4: Test Orion Training

```bash
# Run Orion training manually (from repository root)
python3 scripts/train_orion_ffnn.py

# Check the result
cat models/orion/orion_ffnn_model.pkl && echo "✓ Model saved"

# Or run via orchestration
python3 scripts/stars_orchestration.py
```

Check the training logs:
```bash
cat airflow/config/logs/orion_training_latest.json
```

Look for: `"mlflow_logged": "true"`

## Verifying Scheduled Training

The Orion training is scheduled to run Monday-Friday at 7:00 AM EST.

### Check Airflow DAG Status

```bash
# Access Airflow UI
open http://localhost:8080
# Login: admin / admin

# Check stars_orchestration DAG
# Look for: train_orion_model task
```

### Check Training Logs

After a scheduled run:
```bash
# View latest training result
cat airflow/config/logs/orion_training_latest.json | jq

# Look for these fields:
{
  "mlflow_logged": "true",
  "run_id": "...",
  "accuracy": 0.87,
  "discord": {
    "sent": true
  }
}
```

## Troubleshooting

### MLflow Container Not Starting

```bash
# Check logs
docker compose -f docker/docker-compose-airflow.yml logs mlflow

# Common issues:
# 1. MySQL not ready - wait 60 seconds for initialization
# 2. Port 5000 in use - stop conflicting service
# 3. Permission issues on /mlflow volume - check docker/data/mlflow permissions
```

### Airflow Worker Can't Reach MLflow

```bash
# Test from worker container
docker compose -f docker/docker-compose-airflow.yml exec airflow-worker \
  curl -v http://mlflow:5000/

# Check environment variable
docker compose -f docker/docker-compose-airflow.yml exec airflow-worker \
  env | grep MLFLOW_TRACKING_URI

# Should show: MLFLOW_TRACKING_URI=http://mlflow:5000
```

### MLflow Logging Fails in Training

```bash
# Check MLflow server accessibility
curl http://localhost:5000/health

# Test Python connectivity
python3 << 'EOF'
import mlflow
mlflow.set_tracking_uri("http://localhost:5000")
print(mlflow.search_experiments())
EOF

# Run validation script
python3 docker/validate_mlflow_setup.py
```

## Rebuilding After Changes

If you modify Dockerfile.mlflow or mlflow-entrypoint.sh:

```bash
cd docker

# Rebuild MLflow image
docker compose -f docker-compose-airflow.yml build mlflow --no-cache

# Restart the service
docker compose -f docker-compose-airflow.yml up mlflow -d

# Check health
./check_mlflow_health.sh
```

## Acceptance Criteria Verification

### ✓ MLflow Container Health
```bash
docker compose -f docker/docker-compose-airflow.yml ps mlflow
# Should show: Status: Up, Health: healthy
```

### ✓ Network Connectivity
```bash
docker compose -f docker/docker-compose-airflow.yml exec airflow-worker curl http://mlflow:5000/
# Should return HTML response
```

### ✓ Training Logs MLflow Success
```bash
cat airflow/config/logs/orion_training_latest.json | grep mlflow_logged
# Should show: "mlflow_logged": "true"
```

### ✓ Scheduled Runs Continue
- Orion training runs Monday-Friday at 7:00 AM EST
- Discord notifications to Noomo continue to send
- Check Airflow UI for successful `train_orion_model` task execution

## Next Steps

1. Monitor the first scheduled run (Monday-Friday 7:00 AM EST)
2. Verify `mlflow_logged: true` in training logs
3. Check MLflow UI for new experiment runs
4. Confirm Discord notifications to Noomo
5. Review MLflow server logs for any warnings

## Support

For issues or questions:
- View logs: `docker compose -f docker/docker-compose-airflow.yml logs mlflow`
- Check documentation: `docker/MLFLOW_SETUP.md`
- Run health check: `./docker/check_mlflow_health.sh`
- Run validation: `python3 docker/validate_mlflow_setup.py`
