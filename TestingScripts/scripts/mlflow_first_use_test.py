#!/usr/bin/env python3
"""
Minimal MLFlow initialization test - create an experiment
This should trigger database schema creation
"""
import os
os.environ['MLFLOW_BACKEND_STORE_URI'] = 'mysql+pymysql://root:cBlIUSygvPJCgPbNKHePJekQlClRamri@nozomi.proxy.rlwy.net:54537/mlflow_db'
os.environ['MLFLOW_TRACKING_URI'] = 'mysql+pymysql://root:cBlIUSygvPJCgPbNKHePJekQlClRamri@nozomi.proxy.rlwy.net:54537/mlflow_db'

print("=" * 70)
print("MLFlow First-Use Initialization Test")
print("=" * 70)

try:
    print("\n[*] Importing mlflow...")
    import mlflow
    print(f"[OK] MLFlow {mlflow.__version__}")
    
    print("\n[*] Creating test experiment...")
    exp_id = mlflow.create_experiment("test_initialization")
    print(f"[OK] Created experiment with ID: {exp_id}")
    
    print("\n[*] Searching experiments...")
    experiments = mlflow.search_experiments()
    print(f"[OK] Found {len(experiments)} experiment(s)")
    
    print("\n" + "=" * 70)
    print("SUCCESS: MLFlow database is initialized!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    import traceback
    print("\nTraceback:")
    traceback.print_exc()
    exit(1)
