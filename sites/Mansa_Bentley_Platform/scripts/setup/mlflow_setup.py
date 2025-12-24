#!/usr/bin/env python3
"""
Bentley Budget Bot - MLflow Setup and Test Script
Comprehensive script to set up and test MLflow tracking
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path
import json
from datetime import datetime

def check_requirements():
    """Check if required packages are installed"""
    print("🔍 Checking requirements...")
    
    required_packages = [
        'mlflow',
        'requests', 
        'pandas'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install'
        ] + missing_packages)
        print("✅ Packages installed successfully")
    
    return True

def setup_directories():
    """Create necessary directories for MLflow"""
    print("📁 Setting up directories...")
    
    directories = [
        'data/mlflow',
        'data/mlflow/db',
        'logs'
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {directory}")
    
    return True

def check_docker_running():
    """Check if Docker is running"""
    print("🐳 Checking Docker...")
    
    try:
        result = subprocess.run(
            ['docker', 'version'], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode == 0:
            print("  ✅ Docker is running")
            return True
        else:
            print("  ❌ Docker command failed")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("  ❌ Docker not found or not running")
        return False

def start_mlflow_standalone():
    """Start MLflow server in standalone mode"""
    print("🚀 Starting MLflow standalone server...")
    
    # Set environment variables
    os.environ['MLFLOW_TRACKING_URI'] = 'http://localhost:5000'
    
    try:
        # Start MLflow server in background
        command = [
            'mlflow', 'server',
            '--backend-store-uri', 'sqlite:///data/mlflow/db/mlflow.db',
            '--default-artifact-root', './data/mlflow',
            '--host', '0.0.0.0',
            '--port', '5000'
        ]
        
        print(f"  Command: {' '.join(command)}")
        
        # Start in background
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"  Started MLflow server (PID: {process.pid})")
        
        # Wait for server to start
        print("  Waiting for server to start...")
        for i in range(30):
            try:
                response = requests.get('http://localhost:5000', timeout=2)
                if response.status_code == 200:
                    print("  ✅ MLflow server is running")
                    return process
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
            print(f"  Attempt {i+1}/30...")
        
        print("  ❌ MLflow server failed to start within 30 seconds")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"  ❌ Failed to start MLflow: {e}")
        return None

def start_mlflow_docker():
    """Start MLflow using Docker Compose"""
    print("🐳 Starting MLflow with Docker Compose...")
    
    if not Path('docker-compose-mlflow.yml').exists():
        print("  ❌ docker-compose-mlflow.yml not found")
        return False
    
    try:
        # Start MLflow service
        subprocess.run([
            'docker-compose', 
            '-f', 'docker-compose-mlflow.yml',
            'up', '-d', 'mlflow'
        ], check=True)
        
        print("  ✅ MLflow Docker container started")
        
        # Wait for health check
        print("  Waiting for health check...")
        for i in range(60):
            try:
                response = requests.get('http://localhost:5000', timeout=2)
                if response.status_code == 200:
                    print("  ✅ MLflow Docker service is healthy")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
            print(f"  Health check {i+1}/60...")
        
        print("  ❌ MLflow Docker service health check failed")
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Docker Compose failed: {e}")
        return False

def test_mlflow_connection():
    """Test MLflow connection and basic functionality"""
    print("🧪 Testing MLflow connection...")
    
    try:
        # Import MLflow
        import mlflow
        from mlflow_config import test_mlflow_connection
        
        # Set tracking URI
        mlflow.set_tracking_uri('http://localhost:5000')
        
        # Test basic connection
        client = mlflow.tracking.MlflowClient()
        experiments = client.search_experiments()
        print(f"  ✅ Connected to MLflow - {len(experiments)} experiments found")
        
        # Run comprehensive test
        print("  Running comprehensive test...")
        test_mlflow_connection()
        
        print("  ✅ MLflow test completed successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ MLflow test failed: {e}")
        return False

def test_streamlit_integration():
    """Test Streamlit MLflow integration"""
    print("🖥️ Testing Streamlit integration...")
    
    try:
        from streamlit_mlflow_integration import (
            track_page_load,
            track_portfolio_update,
            track_yfinance_call,
            get_session_summary
        )
        
        # Test tracking functions
        track_page_load("test_dashboard", 1.5)
        
        test_portfolio = {
            "total_value": 100000,
            "positions": 10,
            "daily_return": 2.3,
            "source": "test_data"
        }
        track_portfolio_update(test_portfolio)
        
        track_yfinance_call(["AAPL", "GOOGL"], True, 0.8, 250)
        
        summary = get_session_summary()
        print(f"  ✅ Streamlit integration test completed")
        print(f"  Session: {summary['session_id']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Streamlit integration test failed: {e}")
        return False

def generate_setup_report():
    """Generate a setup report"""
    print("📊 Generating setup report...")
    
    report = {
        "setup_timestamp": datetime.now().isoformat(),
        "mlflow_tracking_uri": "http://localhost:5000",
        "files_created": [
            "mlflow_config.py",
            "streamlit_mlflow_integration.py", 
            "docker-compose-mlflow.yml"
        ],
        "directories_created": [
            "data/mlflow",
            "data/mlflow/db"
        ],
        "next_steps": [
            "Integrate tracking calls in streamlit_app.py",
            "Set up Airflow DAGs with MLflow logging",
            "Configure production MLflow with MySQL backend",
            "Set up automated model training pipelines"
        ]
    }
    
    # Save report
    with open('mlflow_setup_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("  ✅ Setup report saved to mlflow_setup_report.json")
    
    # Print summary
    print("\n" + "="*60)
    print("🎉 MLFLOW SETUP COMPLETE!")
    print("="*60)
    print(f"📍 MLflow UI: http://localhost:5000")
    print(f"📁 Artifacts: ./data/mlflow/")
    print(f"🗄️ Database: ./data/mlflow/db/mlflow.db")
    print()
    print("🚀 Next Steps:")
    for step in report["next_steps"]:
        print(f"  • {step}")
    print()
    print("💡 Quick Start Commands:")
    print("  • Start MLflow: python mlflow_setup.py --start")
    print("  • Test tracking: python mlflow_config.py")
    print("  • Docker mode: docker-compose -f docker-compose-mlflow.yml up -d")
    print("="*60)
    
    return report

def main():
    """Main setup function"""
    print("🏁 Starting Bentley Budget Bot MLflow Setup")
    print("="*60)
    
    # Parse arguments
    start_server = '--start' in sys.argv
    docker_mode = '--docker' in sys.argv
    test_only = '--test' in sys.argv
    
    if test_only:
        print("🧪 Running tests only...")
        test_mlflow_connection()
        test_streamlit_integration()
        return
    
    # Setup steps
    steps = [
        ("Check Requirements", check_requirements),
        ("Setup Directories", setup_directories),
    ]
    
    if docker_mode:
        steps.append(("Check Docker", check_docker_running))
    
    # Run setup steps
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        try:
            result = step_func()
            if not result:
                print(f"❌ {step_name} failed")
                return
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            return
    
    # Start MLflow if requested
    mlflow_started = False
    if start_server:
        if docker_mode:
            mlflow_started = start_mlflow_docker()
        else:
            process = start_mlflow_standalone()
            mlflow_started = process is not None
    
    # Run tests if MLflow is running
    if mlflow_started or not start_server:
        if mlflow_started or test_only:
            print("\n🧪 Running Tests...")
            test_mlflow_connection()
            test_streamlit_integration()
    
    # Generate report
    generate_setup_report()

if __name__ == "__main__":
    main()