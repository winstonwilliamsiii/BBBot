#!/bin/bash
set -e

# Default MySQL connection parameters
MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-root}"
MYSQL_DATABASE="${MYSQL_DATABASE:-mlflow_db}"

# Wait for MySQL to be ready
echo "Waiting for MySQL at ${MYSQL_HOST}:${MYSQL_PORT}..."
max_attempts=30
attempt=0

while ! nc -z "${MYSQL_HOST}" "${MYSQL_PORT}"; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "ERROR: MySQL not available after ${max_attempts} attempts"
        exit 1
    fi
    echo "MySQL not ready yet (attempt ${attempt}/${max_attempts})..."
    sleep 2
done

echo "MySQL is ready!"

# Test MySQL connection with Python
echo "Testing MySQL connection..."
python3 << EOF
import pymysql
import time
import sys

max_retries = 10
for attempt in range(max_retries):
    try:
        conn = pymysql.connect(
            host="${MYSQL_HOST}",
            port=${MYSQL_PORT},
            user="${MYSQL_USER}",
            password="${MYSQL_PASSWORD}",
            connect_timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE};")
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        print(f"MySQL connection successful (database: ${MYSQL_DATABASE})")
        sys.exit(0)
    except Exception as e:
        print(f"MySQL connection attempt {attempt+1}/{max_retries} failed: {e}")
        if attempt < max_retries - 1:
            time.sleep(3)
        else:
            print("ERROR: Could not connect to MySQL")
            sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "ERROR: MySQL connection test failed"
    exit 1
fi

# Build MySQL backend store URI
BACKEND_STORE_URI="mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE}"
ARTIFACT_ROOT="${MLFLOW_DEFAULT_ARTIFACT_ROOT:-/mlflow/artifacts}"

echo "Starting MLflow server with MySQL backend..."
echo "  Backend URI: ${BACKEND_STORE_URI}"
echo "  Artifact Root: ${ARTIFACT_ROOT}"

# Start MLflow server with MySQL backend
exec mlflow server \
    --backend-store-uri "${BACKEND_STORE_URI}" \
    --default-artifact-root "mlflow-artifacts:/" \
    --artifacts-destination "${ARTIFACT_ROOT}" \
    --host 0.0.0.0 \
    --port 5000 \
    --allowed-hosts "mlflow,mlflow:5000,bentley-mlflow,bentley-mlflow:5000,localhost,localhost:5000,127.0.0.1,127.0.0.1:5000" \
    --serve-artifacts
