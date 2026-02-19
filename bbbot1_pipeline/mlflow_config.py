"""
MLFlow Database Configuration for BentleyBot
Centralized configuration for MLFlow tracking with MySQL backend
Supports both local Docker (port 3307) and Railway cloud deployment
"""

import os
from typing import Optional
from urllib.parse import urlparse

def get_mlflow_config() -> dict:
    """
    Get MLFlow MySQL configuration from environment variables
    Supports both local and Railway deployments
    
    Returns:
        dict: MySQL configuration for MLFlow
    """
    # Check for Railway/Cloud environment (Streamlit secrets or Railway env vars)
    mlflow_host = os.getenv('MLFLOW_MYSQL_HOST')
    
    if mlflow_host and mlflow_host != '127.0.0.1':
        # Railway/Cloud configuration
        return {
            "name": "Railway_MLFlow",
            "host": mlflow_host,
            "port": int(os.getenv('MLFLOW_MYSQL_PORT', '54537')),
            "user": os.getenv('MLFLOW_MYSQL_USER', 'root'),
            "password": os.getenv('MLFLOW_MYSQL_PASSWORD', ''),
            "database": os.getenv('MLFLOW_MYSQL_DATABASE', 'mlflow_db')
        }
    else:
        # Local Docker configuration
        return {
            "name": "Local_Docker",
            "host": "127.0.0.1",
            "port": 3307,
            "user": "root",
            "password": "root",
            "database": "mlflow_db"  # Changed from bbbot1 to mlflow_db
        }

# Get configuration based on environment
MLFLOW_MYSQL_CONFIG = get_mlflow_config()


def _is_http_uri(uri: str) -> bool:
    """Return True when URI is HTTP(S)."""
    if not uri:
        return False
    scheme = urlparse(uri).scheme.lower()
    return scheme in ("http", "https")


def get_mlflow_server_url() -> str:
    """
    Get MLflow web/server URL.

    Priority:
    1. MLFLOW_SERVER_URL (explicit web endpoint)
    2. MLFLOW_TRACKING_URI if it's HTTP(S)
    3. Default local MLflow server URL
    """
    explicit_server = os.getenv("MLFLOW_SERVER_URL", "").strip()
    if _is_http_uri(explicit_server):
        return explicit_server.rstrip("/")

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "").strip()
    if _is_http_uri(tracking_uri):
        return tracking_uri.rstrip("/")

    return "http://localhost:5000"


def get_mlflow_backend_store_uri() -> str:
    """
    Get MLflow backend store URI.

    Uses explicit env var first, then builds from MySQL config.
    """
    backend_uri = os.getenv("MLFLOW_BACKEND_STORE_URI", "").strip()
    if backend_uri:
        return backend_uri

    return (
        f"mysql+pymysql://{MLFLOW_MYSQL_CONFIG['user']}:{MLFLOW_MYSQL_CONFIG['password']}"
        f"@{MLFLOW_MYSQL_CONFIG['host']}:{MLFLOW_MYSQL_CONFIG['port']}"
        f"/{MLFLOW_MYSQL_CONFIG['database']}"
    )

def get_mlflow_tracking_uri() -> str:
    """
    Get MLFlow tracking URI for MySQL backend
    
    Returns:
        str: MySQL connection string for MLFlow
    """
    tracking_uri = os.getenv('MLFLOW_TRACKING_URI', '').strip()
    if tracking_uri:
        if _is_http_uri(tracking_uri):
            return tracking_uri

    return get_mlflow_server_url()

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
    
    # Set tracking URI to MLflow server endpoint
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
        
        # Set tracking URI (HTTP endpoint preferred)
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
        if "Can't locate revision identified by" in str(e):
            print("ℹ️ MLflow database migration mismatch detected.")
            print("   Run: mlflow db upgrade <MLFLOW_BACKEND_STORE_URI>")
        return False

if __name__ == "__main__":
    print_connection_details()
    print()
    validate_connection()
