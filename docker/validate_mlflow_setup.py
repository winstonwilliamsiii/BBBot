#!/usr/bin/env python3
"""
Validate MLflow setup and connectivity for Bentley Bot Orion training.

This script tests:
1. MLflow server accessibility
2. Experiment creation and retrieval
3. Run logging capabilities
4. MySQL backend connectivity

Run from repository root:
    python3 docker/validate_mlflow_setup.py

Or from within Airflow worker container:
    docker compose -f docker/docker-compose-airflow.yml exec airflow-worker python3 /opt/bentley/docker/validate_mlflow_setup.py
"""

import os
import sys
import time
from typing import Dict, Any

try:
    import mlflow
    from mlflow.exceptions import MlflowException
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    print("ERROR: mlflow package not installed")
    print("Install with: pip install mlflow==2.8.1")
    sys.exit(1)

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False
    print("WARNING: pymysql not installed (MySQL backend validation will be skipped)")


def test_mlflow_connectivity(tracking_uri: str) -> Dict[str, Any]:
    """Test basic MLflow server connectivity."""
    print(f"\n=== Testing MLflow Connectivity ===")
    print(f"Tracking URI: {tracking_uri}")

    result = {
        "test": "connectivity",
        "tracking_uri": tracking_uri,
        "success": False,
        "error": None
    }

    try:
        mlflow.set_tracking_uri(tracking_uri)

        # Test connection by listing experiments
        experiments = mlflow.search_experiments()
        result["success"] = True
        result["experiment_count"] = len(experiments)

        print(f"✓ MLflow server is accessible")
        print(f"✓ Found {len(experiments)} experiments")

        return result

    except Exception as e:
        result["error"] = str(e)
        print(f"✗ MLflow connection failed: {e}")
        return result


def test_experiment_creation(experiment_name: str = "Test_Validation") -> Dict[str, Any]:
    """Test experiment creation and retrieval."""
    print(f"\n=== Testing Experiment Creation ===")
    print(f"Experiment: {experiment_name}")

    result = {
        "test": "experiment_creation",
        "experiment_name": experiment_name,
        "success": False,
        "error": None
    }

    try:
        # Create or get experiment
        experiment_id = mlflow.create_experiment(
            experiment_name,
            tags={"purpose": "validation", "bot": "test"}
        ) if not mlflow.get_experiment_by_name(experiment_name) else \
            mlflow.get_experiment_by_name(experiment_name).experiment_id

        result["experiment_id"] = experiment_id
        result["success"] = True

        print(f"✓ Experiment created/retrieved: {experiment_id}")

        return result

    except Exception as e:
        result["error"] = str(e)
        print(f"✗ Experiment creation failed: {e}")
        return result


def test_run_logging(experiment_name: str = "Test_Validation") -> Dict[str, Any]:
    """Test MLflow run logging capabilities."""
    print(f"\n=== Testing Run Logging ===")

    result = {
        "test": "run_logging",
        "success": False,
        "error": None
    }

    try:
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run(run_name="validation_test") as run:
            # Log parameters
            mlflow.log_param("test_param", "validation")
            mlflow.log_param("bot", "Orion")

            # Log metrics
            mlflow.log_metric("test_metric", 0.95)
            mlflow.log_metric("accuracy", 0.87)

            # Log tags
            mlflow.set_tag("validation", "true")

            result["run_id"] = run.info.run_id
            result["success"] = True

            print(f"✓ Run logged successfully: {run.info.run_id}")
            print(f"✓ Parameters and metrics recorded")

        return result

    except Exception as e:
        result["error"] = str(e)
        print(f"✗ Run logging failed: {e}")
        return result


def test_mysql_backend(tracking_uri: str) -> Dict[str, Any]:
    """Test MySQL backend connectivity (if available)."""
    print(f"\n=== Testing MySQL Backend ===")

    result = {
        "test": "mysql_backend",
        "success": False,
        "error": None
    }

    if not PYMYSQL_AVAILABLE:
        result["error"] = "pymysql not installed"
        print(f"✗ pymysql not available, skipping MySQL test")
        return result

    # Parse MySQL connection from tracking URI or environment
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = int(os.getenv("MYSQL_PORT", "3307"))  # Docker host port
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "root")
    mysql_database = os.getenv("MYSQL_DATABASE", "mlflow_db")

    # If we're in a container, use internal port
    if os.path.exists("/.dockerenv"):
        mysql_host = os.getenv("MYSQL_HOST", "mysql")
        mysql_port = 3306

    print(f"MySQL: {mysql_user}@{mysql_host}:{mysql_port}/{mysql_database}")

    try:
        conn = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            connect_timeout=10
        )

        cursor = conn.cursor()

        # Check for MLflow tables
        cursor.execute("SHOW TABLES;")
        tables = [row[0] for row in cursor.fetchall()]

        result["table_count"] = len(tables)
        result["has_experiments_table"] = "experiments" in tables
        result["has_runs_table"] = "runs" in tables
        result["success"] = True

        cursor.close()
        conn.close()

        print(f"✓ MySQL connection successful")
        print(f"✓ Found {len(tables)} tables")
        print(f"✓ MLflow schema: {'initialized' if 'experiments' in tables else 'not initialized'}")

        return result

    except Exception as e:
        result["error"] = str(e)
        print(f"✗ MySQL connection failed: {e}")
        return result


def test_orion_experiment() -> Dict[str, Any]:
    """Test Orion experiment accessibility."""
    print(f"\n=== Testing Orion Experiment ===")

    result = {
        "test": "orion_experiment",
        "success": False,
        "error": None
    }

    try:
        experiment = mlflow.get_experiment_by_name("Orion_FFNN_Gold_RSI")

        if experiment:
            result["experiment_id"] = experiment.experiment_id
            result["lifecycle_stage"] = experiment.lifecycle_stage

            # Get recent runs
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                max_results=5,
                order_by=["start_time DESC"]
            )

            result["run_count"] = len(runs)
            result["success"] = True

            print(f"✓ Orion experiment found: {experiment.experiment_id}")
            print(f"✓ Recent runs: {len(runs)}")

            if len(runs) > 0:
                latest_run = runs.iloc[0]
                print(f"✓ Latest run: {latest_run['run_id']}")
                if 'metrics.accuracy' in runs.columns:
                    print(f"  - Accuracy: {latest_run.get('metrics.accuracy', 'N/A')}")
        else:
            result["error"] = "Orion experiment not found"
            print(f"✗ Orion experiment not found (will be created on first training)")
            result["success"] = True  # Not an error, just hasn't been created yet

        return result

    except Exception as e:
        result["error"] = str(e)
        print(f"✗ Orion experiment check failed: {e}")
        return result


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("MLflow Setup Validation for Bentley Bot")
    print("=" * 60)

    # Determine tracking URI
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

    # Check if we're in a Docker container
    in_container = os.path.exists("/.dockerenv")
    if in_container:
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        print(f"\n[Running inside Docker container]")
    else:
        print(f"\n[Running on host machine]")

    print(f"MLflow version: {mlflow.__version__}")

    # Run all tests
    results = []

    # Test 1: Connectivity
    results.append(test_mlflow_connectivity(tracking_uri))
    time.sleep(1)

    if not results[-1]["success"]:
        print("\n" + "=" * 60)
        print("VALIDATION FAILED: Cannot connect to MLflow server")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("1. Ensure MLflow container is running:")
        print("   docker compose -f docker/docker-compose-airflow.yml ps mlflow")
        print("2. Check MLflow logs:")
        print("   docker compose -f docker/docker-compose-airflow.yml logs mlflow")
        print("3. Verify MySQL is healthy:")
        print("   docker compose -f docker/docker-compose-airflow.yml ps mysql")
        sys.exit(1)

    # Test 2: Experiment Creation
    results.append(test_experiment_creation())
    time.sleep(1)

    # Test 3: Run Logging
    results.append(test_run_logging())
    time.sleep(1)

    # Test 4: MySQL Backend
    results.append(test_mysql_backend(tracking_uri))
    time.sleep(1)

    # Test 5: Orion Experiment
    results.append(test_orion_experiment())

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r["success"])
    total = len(results)

    for r in results:
        status = "✓ PASS" if r["success"] else "✗ FAIL"
        print(f"{status}: {r['test']}")
        if r.get("error"):
            print(f"  Error: {r['error']}")

    print(f"\nTests Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ ALL TESTS PASSED - MLflow is ready for Orion training!")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} TESTS FAILED - Review errors above")
        sys.exit(1)


if __name__ == "__main__":
    main()
