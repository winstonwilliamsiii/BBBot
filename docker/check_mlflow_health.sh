#!/bin/bash
# Quick MLflow Docker Health Check Script
#
# Usage:
#   ./docker/check_mlflow_health.sh
#
# This script performs basic health checks on the MLflow Docker setup

set -e

COMPOSE_FILE="docker/docker-compose-airflow.yml"
CONTAINER_NAME="bentley-mlflow"

echo "=========================================="
echo "MLflow Docker Health Check"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "✗ Docker is not running"
    exit 1
fi
echo "✓ Docker is running"

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "✗ Compose file not found: $COMPOSE_FILE"
    exit 1
fi
echo "✓ Compose file found"

# Check if MLflow container exists
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "✗ MLflow container not found: $CONTAINER_NAME"
    echo "  Start with: docker compose -f $COMPOSE_FILE up mlflow -d"
    exit 1
fi
echo "✓ MLflow container exists"

# Check if MLflow container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "✗ MLflow container is not running"
    echo "  Start with: docker compose -f $COMPOSE_FILE up mlflow -d"
    exit 1
fi
echo "✓ MLflow container is running"

# Check container health status
HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null || echo "none")
echo "  Health status: $HEALTH_STATUS"

if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo "✓ MLflow container is healthy"
elif [ "$HEALTH_STATUS" = "starting" ]; then
    echo "⚠ MLflow container is still starting (this can take up to 60s)"
    echo "  Wait a moment and run this script again"
elif [ "$HEALTH_STATUS" = "unhealthy" ]; then
    echo "✗ MLflow container is unhealthy"
    echo "  Check logs: docker compose -f $COMPOSE_FILE logs mlflow"
    exit 1
else
    echo "⚠ Health check not configured"
fi

# Check if MySQL container is running
if docker ps --format '{{.Names}}' | grep -q "bentley-mysql"; then
    echo "✓ MySQL container is running"

    MYSQL_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' bentley-mysql 2>/dev/null || echo "none")
    if [ "$MYSQL_HEALTH" != "none" ]; then
        echo "  MySQL health: $MYSQL_HEALTH"
    fi
else
    echo "✗ MySQL container is not running"
    echo "  MLflow needs MySQL to be running"
    exit 1
fi

# Test MLflow HTTP endpoint from host
echo ""
echo "Testing MLflow HTTP endpoint..."
if curl -f -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✓ MLflow /health endpoint is accessible"
elif curl -f -s http://localhost:5000/ > /dev/null 2>&1; then
    echo "✓ MLflow root endpoint is accessible"
else
    echo "✗ MLflow HTTP endpoint is not accessible"
    echo "  URL: http://localhost:5000"
    echo "  Check logs: docker compose -f $COMPOSE_FILE logs mlflow"
    exit 1
fi

# Test from Airflow worker container (if running)
if docker ps --format '{{.Names}}' | grep -q "bentley-airflow-worker"; then
    echo ""
    echo "Testing MLflow connectivity from Airflow worker..."
    if docker exec bentley-airflow-worker curl -f -s http://mlflow:5000/ > /dev/null 2>&1; then
        echo "✓ Airflow worker can reach MLflow at http://mlflow:5000"
    else
        echo "✗ Airflow worker cannot reach MLflow"
        echo "  This will cause mlflow_logged=false in training runs"
        exit 1
    fi

    # Check MLFLOW_TRACKING_URI environment variable
    MLFLOW_URI=$(docker exec bentley-airflow-worker printenv MLFLOW_TRACKING_URI 2>/dev/null || echo "NOT_SET")
    echo "  MLFLOW_TRACKING_URI: $MLFLOW_URI"
    if [ "$MLFLOW_URI" = "http://mlflow:5000" ]; then
        echo "✓ MLFLOW_TRACKING_URI is correctly configured"
    else
        echo "⚠ MLFLOW_TRACKING_URI should be http://mlflow:5000"
    fi
else
    echo ""
    echo "⚠ Airflow worker container not running (skipping connectivity test)"
fi

# Show recent logs
echo ""
echo "Recent MLflow logs:"
echo "=========================================="
docker compose -f $COMPOSE_FILE logs --tail=10 mlflow

echo ""
echo "=========================================="
echo "✓ MLflow Health Check Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  • Access MLflow UI: http://localhost:5000"
echo "  • Run validation: python3 docker/validate_mlflow_setup.py"
echo "  • View full logs: docker compose -f $COMPOSE_FILE logs -f mlflow"
