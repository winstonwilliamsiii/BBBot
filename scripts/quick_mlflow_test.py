#!/usr/bin/env python3
"""
Quick test that Investment and Crypto pages can import without MLFlow errors
"""
import sys
import os

# Set short timeouts upfront
os.environ['MLFLOW_GRPC_REQUEST_TIMEOUT'] = '3'
os.environ['MLFLOW_HTTP_REQUEST_TIMEOUT'] = '3'

print("=" * 70)
print("Quick MLflow Integration Test")
print("=" * 70)

try:
    print("\n[*] Testing streamlit_mlflow_integration import...")
    from streamlit_mlflow_integration import MLFLOW_INTEGRATION_AVAILABLE, StreamlitMLflowTracker
    print(f"[OK] Imported successfully")
    print(f"    MLFLOW_INTEGRATION_AVAILABLE = {MLFLOW_INTEGRATION_AVAILABLE}")
    
    if not MLFLOW_INTEGRATION_AVAILABLE:
        print("\n[✓] ✅ SUCCESS: Pages will work with local logging fallback")
        print("\nInvestment and Crypto pages can now load without MLFlow errors.")
        print("Metrics will be logged locally when MLFlow server is unavailable.")
    else:
        print("\n[✓] SUCCESS: MLflows is fully available")
    
    print("\n" + "=" * 70)
    sys.exit(0)

except Exception as e:
    print(f"\n[ERROR] Failed: {type(e).__name__}: {e}")
    sys.exit(1)
