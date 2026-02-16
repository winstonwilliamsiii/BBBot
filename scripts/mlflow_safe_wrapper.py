"""
MLFlow Error Handling Wrapper
Gracefully handles MLFlow initialization failures in Streamlit apps
"""

import os
import logging

logger = logging.getLogger(__name__)

# Try to import mlflow at module level
try:
    import mlflow
    MLFLOW_IMPORTED = True
except ImportError:
    MLFLOW_IMPORTED = False
    logger.warning("MLflow not installed")

class MLFlowSafeWrapper:
    """
    Wraps MLFlow initialization to gracefully handle schema errors
    Allows your Investment and Crypto pages to work even if MLFlow has issues
    """
    
    def __init__(self):
        self.available = False
        self.client = None
        self._initialize_safely()
    
    def _initialize_safely(self):
        """Initialize MLFlow, but catch schema errors gracefully"""
        if not MLFLOW_IMPORTED:
            logger.warning("MLflow not available - skipping initialization")
            return
            
        try:
            tracking_uri = os.getenv(
                'MLFLOW_TRACKING_URI',
                'mysql+pymysql://root:cBlIUSygvPJCgPbNKHePJekQlClRamri@nozomi.proxy.rlwy.net:54537/mlflow_db'
            )
            
            # Try to initialize
            mlflow.set_tracking_uri(tracking_uri)
            self.client = mlflow.tracking.MlflowClient()
            self.available = True
            logger.info("MLFlow initialized successfully")
            
        except Exception as e:
            error_msg = str(e)
            
            # Log the error but don't crash
            if "Duplicate column" in error_msg or "Table" in error_msg:
                logger.warning(
                    "MLFlow database schema mismatch detected. "
                    "This is a known issue with database migrations. "
                    "Your app will continue to work without ML experiment tracking. "
                    f"Error: {error_msg[:100]}"
                )
            elif "already exists" in error_msg.lower():
                logger.warning(
                    "MLFlow database tables are in an inconsistent state. "
                    "Your app will continue running without ML logging."
                )
            else:
                logger.warning(f"MLFlow initialization failed: {error_msg}")
            
            #self.available remains False - app operates without MLFlow
    
    def log_metric(self, key, value, step=0):
        """Log a metric if MLFlow is available"""
        if not self.available or not MLFLOW_IMPORTED:
            return
        try:
            if hasattr(self.client, '_tracking_client'):
                # MLFlow v2.x
                mlflow.log_metric(key, value, step=step)
        except Exception as e:
            logger.debug(f"Could not log metric {key}: {e}")
    
    def log_params(self, params):
        """Log parameters if MLFlow is available"""
        if not self.available or not MLFLOW_IMPORTED:
            return
        try:
            if hasattr(self.client, '_tracking_client'):
                mlflow.log_params(params)
        except Exception as e:
            logger.debug(f"Could not log params: {e}")
    
    def start_run(self, experiment_name=None, run_name=None):
        """Safely start a run - returns a mock if MLFlow unavailable"""
        if not self.available:
            # Return a no-op context manager
            class NoOpRun:
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
                info = type('obj', (object,), {'run_id': 'no-mlflow'})()
            return NoOpRun()
        
        try:
            import mlflow
            if experiment_name:
                mlflow.set_experiment(experiment_name)
            return mlflow.start_run(run_name=run_name)
        except Exception as e:
            logger.debug(f"Could not start MLFlow run: {e}")
            # Return no-op context  manager
            class NoOpRun:
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
                info = type('obj', (object,), {'run_id': 'no-mlflow'})()
            return NoOpRun()

# Create global instance
mlflow_tracker = MLFlowSafeWrapper()

# Usage in your Streamlit apps:
# ==============================
# from mlflow_safe_wrapper import mlflow_tracker
# 
# with mlflow_tracker.start_run(experiment_name="investment_analysis"):
#     mlflow_tracker.log_metric("portfolio_return", 0.15)
#     mlflow_tracker.log_params({"risk_level": "medium"})
#
# Your code runs fine even if MLFlow has issues!
