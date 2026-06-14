"""
MLFlow Connection Verification Test
Confirms the database schema fix was successful
"""

import os
import mlflow
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set the tracking URI to your remote database
tracking_uri = "mysql+pymysql://root:cBlIUSygvPJCgPbNKHePJekQlClRamri@nozomi.proxy.rlwy.net:54537/mlflow_db"

print("\n" + "="*60)
print("MLFlow Connection Verification")
print("="*60)

try:
    print(f"\n[*] Setting MLFlow tracking URI...")
    mlflow.set_tracking_uri(tracking_uri)
    print(f"[OK] Tracking URI set")
    
    print(f"\n[*] Initializing MLFlow client...")
    client = mlflow.tracking.MlflowClient()
    print("[OK] MLFlow client initialized")
    
    print(f"\n[*] Testing experiment access...")
    experiments = client.search_experiments()
    print(f"[OK] Found {len(experiments)} experiments")
    
    print(f"\n[*] Testing new run creation...")
    with mlflow.start_run(experiment_id="0") as run:
        mlflow.log_metric("test_metric", 1.0)
        print(f"[OK] Created test run: {run.info.run_id}")
    
    print("\n" + "="*60)
    print("SUCCESS: MLFlow is fully operational!")
    print("="*60)
    print("\nYour Investment and Crypto pages are now ready:")
    print("  [OK] MLFlow logging enabled")
    print("  [OK] Database schema compatible")
    print("  [OK] Experiment tracking active")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
