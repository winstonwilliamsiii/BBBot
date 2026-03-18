"""
Quick verification script for MLflow connection
Tests MLflow server connectivity and basic operations
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("=" * 70)
    print("MLflow Connection Verification")
    print("=" * 70)
    print()
    
    # Test 1: Import MLflow
    print("1. Testing MLflow import...")
    try:
        import mlflow
        print(f"   ✅ MLflow version: {mlflow.__version__}")
    except ImportError as e:
        print(f"   ❌ Failed to import MLflow: {e}")
        return False
    
    # Test 2: Get tracking URI from config
    print("\n2. Loading MLflow configuration...")
    try:
        from bbbot1_pipeline.mlflow_config import get_mlflow_tracking_uri, MLFLOW_MYSQL_CONFIG
        tracking_uri = get_mlflow_tracking_uri()
        print(f"   ✅ Tracking URI: {tracking_uri}")
        print(f"   📍 Environment: {MLFLOW_MYSQL_CONFIG['name']}")
    except Exception as e:
        print(f"   ❌ Failed to load config: {e}")
        return False
    
    # Test 3: Connect to MLflow server
    print("\n3. Testing MLflow server connection...")
    try:
        # For Docker, use HTTP endpoint
        mlflow.set_tracking_uri("http://localhost:5000")
        from mlflow.tracking import MlflowClient
        client = MlflowClient()
        
        # Try to list experiments
        experiments = client.search_experiments()
        print(f"   ✅ Connected to MLflow server")
        print(f"   📊 Found {len(experiments)} experiment(s)")
        
        for exp in experiments[:3]:  # Show first 3
            print(f"      • {exp.name} (ID: {exp.experiment_id})")
            
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print(f"   💡 Make sure MLflow Docker container is running")
        return False
    
    # Test 4: Create a test experiment
    print("\n4. Testing experiment creation...")
    try:
        experiment_name = "bentley_bot_verification_test"
        
# Try to create or get experiment
        try:
            experiment_id = mlflow.create_experiment(experiment_name)
            print(f"   ✅ Created test experiment: {experiment_name}")
        except Exception:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            experiment_id = experiment.experiment_id
            print(f"   ℹ️  Test experiment already exists: {experiment_name}")
        
        print(f"   📝 Experiment ID: {experiment_id}")
        
    except Exception as e:
        print(f"   ⚠️  Could not create test experiment: {e}")
    
    # Test 5: Test a simple run
    print("\n5. Testing MLflow run logging...")
    try:
        mlflow.set_experiment(experiment_name)
        
        with mlflow.start_run(run_name="verification_run") as run:
            # Log some metrics
            mlflow.log_param("test_param", "verification")
            mlflow.log_metric("test_metric", 0.95)
            mlflow.log_metric("success_rate", 100.0)
            
            run_id = run.info.run_id
            print(f"   ✅ Created test run: {run_id[:8]}...")
            print(f"   📊 Logged parameters and metrics")
            
    except Exception as e:
        print(f"   ⚠️  Could not create test run: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ MLflow Verification Complete!")
    print("=" * 70)
    print()
    print("🎯 Next Steps:")
    print("   1. Visit MLflow UI: http://localhost:5000")
    print("   2. Open Streamlit: streamlit run streamlit_app.py")
    print("   3. Open Prediction Analytics and validate forecast outputs")
    print("   4. Validate optimization/rebalancing pipeline logs")
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
