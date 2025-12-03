# Airflow Connections Configuration Guide

## Overview

This guide explains how to configure Airflow connections for the Bentley Budget Bot data pipeline.

## Required Connections

### 1. MySQL Connection (mysql_bbbot1)

**Purpose**: Connect to MySQL database for raw data tables and dbt models

**Configuration**:
- **Connection ID**: `mysql_bbbot1`
- **Connection Type**: `MySQL`
- **Host**: `bentley-mysql` (if using Docker network) OR `127.0.0.1` (from host)
- **Schema**: `bbbot1`
- **Login**: `root`
- **Password**: `root`
- **Port**: `3306` (inside Docker) OR `3307` (from host)
- **Extra**: `{"charset": "utf8mb4"}`

**Setup via Airflow UI**:
1. Navigate to: `Admin` → `Connections`
2. Click `+` to add new connection
3. Fill in the fields above
4. Click `Test` to verify connection
5. Click `Save`

**Setup via CLI**:
```bash
docker exec -it airflow-webserver airflow connections add \
  mysql_bbbot1 \
  --conn-type mysql \
  --conn-host bentley-mysql \
  --conn-schema bbbot1 \
  --conn-login root \
  --conn-password root \
  --conn-port 3306
```

**Setup via Environment Variable** (docker-compose):
```yaml
environment:
  AIRFLOW_CONN_MYSQL_BBBOT1: mysql://root:root@bentley-mysql:3306/bbbot1
```

---

### 2. MLFlow Connection (mlflow_tracking)

**Purpose**: Connect to MLFlow tracking server for experiment logging

**Configuration**:
- **Connection ID**: `mlflow_tracking`
- **Connection Type**: `HTTP`
- **Host**: `http://127.0.0.1` OR `http://mlflow` (if using Docker network)
- **Port**: `5000`
- **Extra**: `{"backend_store_uri": "mysql+pymysql://root:root@bentley-mysql:3306/mlflow_db"}`

**Setup via Airflow UI**:
1. Navigate to: `Admin` → `Connections`
2. Click `+` to add new connection
3. Fill in the fields above
4. Click `Save`

**Setup via Environment Variable**:
```yaml
environment:
  AIRFLOW_CONN_MLFLOW_TRACKING: http://mlflow:5000
  MLFLOW_TRACKING_URI: mysql+pymysql://root:root@bentley-mysql:3307/mlflow_db
```

**Verify MLFlow Connection**:
```python
# In Airflow Python operator or DAG
import mlflow
from bbbot1_pipeline.mlflow_config import get_mlflow_tracking_uri

mlflow.set_tracking_uri(get_mlflow_tracking_uri())
print(f"MLFlow URI: {mlflow.get_tracking_uri()}")
```

---

## Connection Testing

### Test MySQL Connection

**From Airflow UI**:
1. Go to `Admin` → `Connections`
2. Find `mysql_bbbot1`
3. Click the test button (if available)

**From Python**:
```python
from airflow.providers.mysql.hooks.mysql import MySqlHook

hook = MySqlHook(mysql_conn_id='mysql_bbbot1')
result = hook.get_first("SELECT COUNT(*) FROM prices_daily")
print(f"Price records: {result[0]}")
```

**From Bash**:
```bash
# Inside Airflow container
docker exec -it airflow-webserver python -c "
from airflow.providers.mysql.hooks.mysql import MySqlHook
hook = MySqlHook(mysql_conn_id='mysql_bbbot1')
print(hook.get_first('SELECT DATABASE()'))
"
```

### Test MLFlow Connection

```python
import mlflow
from bbbot1_pipeline.mlflow_config import get_mlflow_tracking_uri

mlflow.set_tracking_uri(get_mlflow_tracking_uri())

# Create test experiment
mlflow.set_experiment("connection_test")

with mlflow.start_run():
    mlflow.log_param("test", "success")
    mlflow.log_metric("value", 1.0)
    
print("✅ MLFlow connection successful")
```

---

## Docker Compose Configuration

Add these connections to your `docker-compose.yml` for Airflow services:

```yaml
services:
  airflow-webserver:
    environment:
      # MySQL Connection
      AIRFLOW_CONN_MYSQL_BBBOT1: mysql://root:root@bentley-mysql:3306/bbbot1
      
      # MLFlow Connection
      MLFLOW_TRACKING_URI: mysql+pymysql://root:root@bentley-mysql:3306/mlflow_db
      
      # Python path for bbbot1_pipeline
      PYTHONPATH: /opt/airflow:/opt/airflow/bbbot1_pipeline

  airflow-scheduler:
    environment:
      # Same as webserver
      AIRFLOW_CONN_MYSQL_BBBOT1: mysql://root:root@bentley-mysql:3306/bbbot1
      MLFLOW_TRACKING_URI: mysql+pymysql://root:root@bentley-mysql:3306/mlflow_db
      PYTHONPATH: /opt/airflow:/opt/airflow/bbbot1_pipeline

  airflow-worker:
    environment:
      # Same as scheduler
      AIRFLOW_CONN_MYSQL_BBBOT1: mysql://root:root@bentley-mysql:3306/bbbot1
      MLFLOW_TRACKING_URI: mysql+pymysql://root:root@bentley-mysql:3306/mlflow_db
      PYTHONPATH: /opt/airflow:/opt/airflow/bbbot1_pipeline
```

---

## Network Configuration

### Docker Network Setup

Ensure all services are on the same Docker network:

```bash
# Create network (if not exists)
docker network create bentley-network

# Connect services
docker network connect bentley-network bentley-mysql
docker network connect bentley-network airflow-webserver
docker network connect bentley-network airflow-scheduler
```

### Host vs. Container Addressing

| From | To | Host | Port |
|------|-----|------|------|
| Host | MySQL | 127.0.0.1 | 3307 |
| Docker | MySQL | bentley-mysql | 3306 |
| Host | MLFlow | 127.0.0.1 | 5000 |
| Docker | MLFlow | mlflow | 5000 |
| Host | Airflow | 127.0.0.1 | 8080 |

---

## Troubleshooting

### MySQL Connection Failed

**Error**: `Access denied for user 'root'@'%'`

**Solution**:
```sql
-- Grant permissions from Docker network
docker exec -it bentley-mysql mysql -uroot -proot -e "
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
"
```

### MLFlow Connection Failed

**Error**: `Connection refused` or `Could not connect to tracking server`

**Solution**:
1. Verify MLFlow server is running:
   ```bash
   curl http://localhost:5000/health
   ```

2. Check environment variable:
   ```bash
   docker exec airflow-webserver env | grep MLFLOW
   ```

3. Restart Airflow services:
   ```bash
   docker-compose restart airflow-webserver airflow-scheduler
   ```

### Module Import Errors

**Error**: `ModuleNotFoundError: No module named 'bbbot1_pipeline'`

**Solution**:
1. Verify `bbbot1_pipeline` is in `/opt/airflow` directory
2. Add to PYTHONPATH:
   ```yaml
   environment:
     PYTHONPATH: /opt/airflow:/opt/airflow/bbbot1_pipeline
   ```

3. Install package in Airflow containers:
   ```bash
   docker exec airflow-webserver pip install -e /opt/airflow/bbbot1_pipeline
   ```

---

## Verification Checklist

- [ ] MySQL connection `mysql_bbbot1` created and tested
- [ ] MLFlow tracking URI configured
- [ ] Docker network connectivity verified
- [ ] bbbot1_pipeline module importable in Airflow
- [ ] Raw tables (prices_daily, fundamentals_raw, etc.) accessible
- [ ] dbt project accessible at `/opt/airflow/dbt_project`
- [ ] MLFlow experiments can be created from Airflow

---

## Quick Setup Script

Run this script to configure all connections automatically:

```bash
#!/bin/bash
# setup_airflow_connections.sh

echo "Setting up Airflow connections..."

# MySQL connection
docker exec airflow-webserver airflow connections delete mysql_bbbot1 || true
docker exec airflow-webserver airflow connections add \
  mysql_bbbot1 \
  --conn-type mysql \
  --conn-host bentley-mysql \
  --conn-schema bbbot1 \
  --conn-login root \
  --conn-password root \
  --conn-port 3306

echo "✅ MySQL connection created"

# Test MySQL connection
docker exec airflow-webserver python -c "
from airflow.providers.mysql.hooks.mysql import MySqlHook
hook = MySqlHook(mysql_conn_id='mysql_bbbot1')
result = hook.get_first('SELECT DATABASE()')
print(f'Connected to database: {result[0]}')
"

echo "✅ All connections configured successfully"
```

Make executable and run:
```bash
chmod +x setup_airflow_connections.sh
./setup_airflow_connections.sh
```

---

## Next Steps

After configuring Airflow connections:

1. ✅ **Configure Airflow connections** (this document)
2. ⏭️ **Set up Airbyte connections** (see AIRBYTE_SETUP.md)
3. ⏭️ **Enable dbt_transformation_pipeline DAG**
4. ⏭️ **Enable stock_pipeline_comprehensive DAG**
5. ⏭️ **Monitor pipeline execution in Airflow UI**

---

## Resources

- **Airflow Connections Docs**: https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html
- **MySQL Hook**: https://airflow.apache.org/docs/apache-airflow-providers-mysql/stable/
- **MLFlow Tracking**: https://www.mlflow.org/docs/latest/tracking.html
