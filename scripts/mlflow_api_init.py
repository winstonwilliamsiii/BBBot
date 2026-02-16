#!/usr/bin/env python3
"""
Initialize MLFlow database schema using Python API
"""
import os
os.environ['MLFLOW_BACKEND_STORE_URI'] = 'mysql+pymysql://root:cBlIUSygvPJCgPbNKHePJekQlClRamri@nozomi.proxy.rlwy.net:54537/mlflow_db'
os.environ['MLFLOW_TRACKING_URI'] = 'mysql+pymysql://root:cBlIUSygvPJCgPbNKHePJekQlClRamri@nozomi.proxy.rlwy.net:54537/mlflow_db'

print("=" * 70)
print("MLFlow Database Schema Initialization")
print("=" * 70)

try:
    print("\n[*] Importing MLFlow...")
    import mlflow
    print(f"[OK] MLFlow {mlflow.__version__} imported")
    
    print("\n[*] Initializing MLFlow client...")
    from mlflow.store.db.db_store import DatabaseStore
    
    # This should trigger database initialization
    db_url = 'mysql+pymysql://root:cBlIUSygvPJCgPbNKHePJekQlClRamri@nozomi.proxy.rlwy.net:54537/mlflow_db'
    print(f"[*] Creating DatabaseStore with URL: {db_url}")
    
    store = DatabaseStore(db_url, default_artifact_root=None)
    print("[OK] DatabaseStore initialized - schema created!")
    
    print("\n[*] Verifying by listing experiments...")
    experiments = store.search_experiments()
    print(f"[OK] Found {len(experiments)} experiments")
    
    print("\n" + "=" * 70)
    print("SUCCESS: MLFlow database initialized and ready!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
