"""
Bentley Budget Bot - Service Diagnostic and Fix Script
Diagnoses and fixes common issues with Airflow, MLflow, and Airbyte
"""

import requests
import time
from typing import Dict, Tuple

def check_service(name: str, url: str, timeout: int = 5) -> Tuple[bool, str]:
    """Check if a service is accessible"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return True, f"✅ {name} is accessible at {url}"
        else:
            return False, f"❌ {name} returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, f"❌ {name} connection refused at {url}"
    except requests.exceptions.Timeout:
        return False, f"❌ {name} timeout at {url}"
    except Exception as e:
        return False, f"❌ {name} error: {str(e)}"

def main():
    print("="*60)
    print("🔍 Bentley Budget Bot - Service Diagnostics")
    print("="*60)
    print()
    
    services = {
        "Airflow Webserver": "http://localhost:8080/health",
        "MLflow": "http://localhost:5000/health",
        "Airbyte Webapp": "http://localhost:8000",
        "Airbyte API": "http://localhost:8001/api/v1/health",
    }
    
    results = {}
    
    print("📊 Checking Services...")
    print()
    
    for name, url in services.items():
        is_up, message = check_service(name, url)
        results[name] = is_up
        print(f"  {message}")
        time.sleep(0.5)
    
    print()
    print("="*60)
    print("📋 Summary")
    print("="*60)
    print()
    
    total = len(results)
    up = sum(1 for v in results.values() if v)
    
    print(f"Services Up: {up}/{total}")
    print()
    
    # Provide specific diagnostics
    if not results.get("Airflow Webserver"):
        print("⚠️  Airflow Issue:")
        print("   - Check if DAGs folder exists: C:/Users/winst/BentleyBudgetBot/dags")
        print("   - Restart: docker restart bentley-airflow-webserver bentley-airflow-scheduler")
        print()
    
    if not results.get("MLflow"):
        print("⚠️  MLflow Issue:")
        print("   - Container showing memory issues (WORKER TIMEOUT)")
        print("   - Recommendation: Restart with lower worker count")
        print("   - Fix: docker restart bentley-mlflow")
        print()
    
    if not results.get("Airbyte API"):
        print("⚠️  Airbyte Issue:")
        print("   - Worker has SecretPersistence configuration error")
        print("   - Temporal service is restarting")
        print("   - Recommendation: Use simpler Airbyte compose file")
        print()
    
    # Check DAG folder
    import os
    dag_folder = r"C:\Users\winst\BentleyBudgetBot\dags"
    
    print("📁 DAG Folder Check:")
    if os.path.exists(dag_folder):
        dag_files = [f for f in os.listdir(dag_folder) if f.endswith('.py')]
        print(f"   ✅ DAG folder exists with {len(dag_files)} Python files")
        if dag_files:
            print("   DAG files:")
            for f in dag_files[:5]:  # Show first 5
                print(f"     - {f}")
            if len(dag_files) > 5:
                print(f"     ... and {len(dag_files) - 5} more")
    else:
        print(f"   ❌ DAG folder not found at {dag_folder}")
    
    print()
    print("="*60)
    print("🔧 Recommended Actions:")
    print("="*60)
    print()
    
    if up < total:
        print("1. Restart unhealthy services:")
        print("   docker restart bentley-mlflow bentley-airbyte-worker")
        print()
        print("2. Wait 30 seconds for Airflow to detect DAGs:")
        print("   Then check: http://localhost:8080/home")
        print()
        print("3. For Airbyte, use the simpler compose file:")
        print("   docker-compose -f docker-compose-airbyte-simple.yml up -d")
        print()
    else:
        print("✅ All services are up!")
        print()
        print("Access your services:")
        print("  - Airflow: http://localhost:8080")
        print("  - MLflow: http://localhost:5000")
        print("  - Airbyte: http://localhost:8000")
        print()

if __name__ == "__main__":
    main()
