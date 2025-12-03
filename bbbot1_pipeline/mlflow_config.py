"""
MLFlow Database Configuration for BentleyBot
Centralized configuration for MLFlow tracking with MySQL backend
"""

import os
from typing import Optional

# MySQL Connection Details for MLFlow
MLFLOW_MYSQL_CONFIG = {
    "name": "Bentley_Budget",
    "host": "127.0.0.1",
    "port": 3307,  # MySQL container maps 3306 -> 3307 on host
    "user": "root",
    "password": "root",
    "database": "mlflow_db"
}

def get_mlflow_tracking_uri() -> str:
    """
    Get MLFlow tracking URI for MySQL backend
    
    Returns:
        str: MySQL connection string for MLFlow
    """
    return (
        f"mysql+pymysql://{MLFLOW_MYSQL_CONFIG['user']}:{MLFLOW_MYSQL_CONFIG['password']}"
        f"@{MLFLOW_MYSQL_CONFIG['host']}:{MLFLOW_MYSQL_CONFIG['port']}"
        f"/{MLFLOW_MYSQL_CONFIG['database']}"
    )

def get_mlflow_artifact_path() -> str:
    """
    Get MLFlow artifact storage path
    
    Returns:
        str: File path for MLFlow artifacts
    """
    artifact_dir = os.path.join(os.path.dirname(__file__), '../data/mlflow_artifacts')
    os.makedirs(artifact_dir, exist_ok=True)
    return artifact_dir

# Connection Details for MySQL Workbench
MYSQL_WORKBENCH_INFO = {
    "Connection Name": "Bentley_Budget",
    "Host": MLFLOW_MYSQL_CONFIG['host'],
    "Port": MLFLOW_MYSQL_CONFIG['port'],
    "Login User": MLFLOW_MYSQL_CONFIG['user'],
    "Current User": "root@localhost",
    "Database": MLFLOW_MYSQL_CONFIG['database']
}

def print_connection_details():
    """Print MySQL connection details for reference"""
    print("=" * 60)
    print("MLFlow MySQL Connection Details")
    print("=" * 60)
    for key, value in MYSQL_WORKBENCH_INFO.items():
        print(f"{key:20}: {value}")
    print("=" * 60)
    print(f"Tracking URI: {get_mlflow_tracking_uri()}")
    print(f"Artifact Path: {get_mlflow_artifact_path()}")
    print("=" * 60)

def initialize_mlflow(experiment_name: str = "bentley_bot_analysis") -> None:
    """
    Initialize MLFlow with MySQL backend
    
    Args:
        experiment_name: Name of experiment to create/use
    """
    import mlflow
    
    # Set tracking URI to MySQL
    tracking_uri = get_mlflow_tracking_uri()
    mlflow.set_tracking_uri(tracking_uri)
    
    # Set experiment
    mlflow.set_experiment(experiment_name)
    
    print(f"✅ MLFlow initialized with MySQL backend")
    print(f"   Tracking URI: {tracking_uri}")
    print(f"   Experiment: {experiment_name}")

def get_mlflow_client():
    """
    Get MLFlow tracking client
    
    Returns:
        MlflowClient: Configured client instance
    """
    from mlflow.tracking import MlflowClient
    import mlflow
    
    mlflow.set_tracking_uri(get_mlflow_tracking_uri())
    return MlflowClient()

def validate_connection() -> bool:
    """
    Validate MLFlow MySQL connection
    
    Returns:
        bool: True if connection successful
    """
    try:
        import mlflow
        from mlflow.tracking import MlflowClient
        
        # Set tracking URI
        tracking_uri = get_mlflow_tracking_uri()
        mlflow.set_tracking_uri(tracking_uri)
        
        # Try to create client and list experiments
        client = MlflowClient()
        experiments = client.search_experiments()
        
        print(f"✅ MLFlow connection successful!")
        print(f"   Found {len(experiments)} experiment(s)")
        return True
        
    except Exception as e:
        print(f"❌ MLFlow connection failed: {e}")
        return False

if __name__ == "__main__":
    print_connection_details()
    print()
    validate_connection()
