"""
Bentley Budget Bot - MLflow Tracking Configuration
Centralized MLflow setup for experiment tracking and model management
"""

import os
import mlflow
from typing import Dict, Any, Optional
import logging

# Set short connection timeout to prevent hanging when MLflow server is unavailable
os.environ['MLFLOW_GRPC_REQUEST_TIMEOUT'] = '5'  # 5 seconds
os.environ['MLFLOW_HTTP_REQUEST_TIMEOUT'] = '5'  # 5 seconds

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BentleyMLflowClient:
    """Centralized MLflow client for Bentley Budget Bot tracking"""
    
    def __init__(self, 
                 tracking_uri: str = None,
                 experiment_name: str = "BentleyBudgetBot-Production"):
        """
        Initialize MLflow client with graceful degradation on failure
        
        Args:
            tracking_uri: MLflow tracking server URI
            experiment_name: Default experiment name
        """
        # Set tracking URI (Docker or local)
        self.tracking_uri = tracking_uri or os.getenv(
            'MLFLOW_TRACKING_URI', 
            'http://localhost:5000'
        )
        self.client = None
        self.available = False
        self.experiment_name = experiment_name
        
        try:
            mlflow.set_tracking_uri(self.tracking_uri)
            logger.info(f"📍 Attempting MLflow initialization with URI: {self.tracking_uri}")
            
            # Try to initialize the client
            try:
                self.client = mlflow.tracking.MlflowClient()
            except Exception as client_init_error:
                logger.warning(f"⚠️ MLflow client initialization failed: {client_init_error}")
                logger.info("💡 Continuing with graceful MLflow degradation mode")
                self.available = False
                return
            
            # Try to create experiment if it doesn't exist
            try:
                self._ensure_experiment_exists()
            except Exception as exp_error:
                logger.warning(f"⚠️ Could not create experiment: {exp_error}")
                # Continue anyway - we can still log metrics
            
            logger.info(f"✅ MLflow client initialized successfully")
            self.available = True
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize MLflow: {e}")
            logger.info("💡 Metrics will be logged locally instead")
            self.available = False
    
    def _ensure_experiment_exists(self):
        """Create experiment if it doesn't exist"""
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                mlflow.create_experiment(self.experiment_name)
                logger.info(f"✅ Created experiment: {self.experiment_name}")
            else:
                logger.info(f"📊 Using existing experiment: {self.experiment_name}")
        except Exception as e:
            logger.error(f"❌ Error managing experiment: {e}")
    
    def start_run(self, 
                  run_name: str = None,
                  experiment_name: str = None,
                  tags: Dict[str, str] = None) -> Optional[mlflow.ActiveRun]:
        """Start MLflow run with proper error handling"""
        if not self.available:
            logger.warning("MLflow not available, skipping run creation")
            return None
        
        try:
            # Set experiment
            exp_name = experiment_name or self.experiment_name
            mlflow.set_experiment(exp_name)
            
            # Start run
            run = mlflow.start_run(run_name=run_name, tags=tags or {})
            logger.info(f"🚀 Started MLflow run: {run.info.run_id}")
            return run
            
        except Exception as e:
            logger.error(f"❌ Error starting run: {e}")
            return None
    
    def log_portfolio_metrics(self, 
                            portfolio_data: Dict[str, Any],
                            run_name: str = "portfolio_analysis"):
        """Log portfolio performance metrics"""
        if not self.available:
            logger.warning("MLflow unavailable - printing metrics instead")
            self._print_metrics(portfolio_data)
            return
        
        try:
            with self.start_run(run_name=run_name, 
                              tags={"component": "portfolio", "type": "analysis"}):
                
                # Log portfolio metrics
                for key, value in portfolio_data.items():
                    if isinstance(value, (int, float)):
                        mlflow.log_metric(key, value)
                    else:
                        mlflow.log_param(key, str(value))
                
                logger.info(f"✅ Logged portfolio metrics: {list(portfolio_data.keys())}")
                
        except Exception as e:
            logger.error(f"❌ Error logging portfolio metrics: {e}")
    
    def log_trading_signals(self, 
                           signals_data: Dict[str, Any],
                           run_name: str = "trading_signals"):
        """Log trading signal analysis"""
        if not self.available:
            self._print_metrics(signals_data)
            return
        
        try:
            with self.start_run(run_name=run_name,
                              tags={"component": "trading", "type": "signals"}):
                
                # Log signal metrics
                mlflow.log_param("signal_strategy", signals_data.get("strategy", "unknown"))
                mlflow.log_metric("total_signals", signals_data.get("total_signals", 0))
                mlflow.log_metric("buy_signals", signals_data.get("buy_signals", 0))
                mlflow.log_metric("sell_signals", signals_data.get("sell_signals", 0))
                mlflow.log_metric("signal_accuracy", signals_data.get("accuracy", 0.0))
                
                # Log additional metrics
                for key, value in signals_data.items():
                    if key not in ["strategy", "total_signals", "buy_signals", "sell_signals", "accuracy"]:
                        if isinstance(value, (int, float)):
                            mlflow.log_metric(key, value)
                        else:
                            mlflow.log_param(key, str(value))
                
                logger.info("✅ Logged trading signals to MLflow")
                
        except Exception as e:
            logger.error(f"❌ Error logging trading signals: {e}")
    
    def log_data_ingestion(self, 
                          ingestion_stats: Dict[str, Any],
                          run_name: str = "data_ingestion"):
        """Log data ingestion statistics"""
        if not self.available:
            self._print_metrics(ingestion_stats)
            return
        
        try:
            with self.start_run(run_name=run_name,
                              tags={"component": "data", "type": "ingestion"}):
                
                mlflow.log_param("data_source", ingestion_stats.get("source", "unknown"))
                mlflow.log_metric("rows_processed", ingestion_stats.get("rows_processed", 0))
                mlflow.log_metric("processing_time_seconds", ingestion_stats.get("processing_time", 0))
                mlflow.log_param("status", ingestion_stats.get("status", "unknown"))
                
                # Log additional stats
                for key, value in ingestion_stats.items():
                    if key not in ["source", "rows_processed", "processing_time", "status"]:
                        if isinstance(value, (int, float)):
                            mlflow.log_metric(key, value)
                        else:
                            mlflow.log_param(key, str(value))
                
                logger.info("✅ Logged data ingestion stats to MLflow")
                
        except Exception as e:
            logger.error(f"❌ Error logging ingestion stats: {e}")
    
    def _print_metrics(self, metrics: Dict[str, Any]):
        """Print metrics when MLflow is unavailable"""
        logger.info("📊 Metrics (MLflow unavailable):")
        for key, value in metrics.items():
            logger.info(f"   {key}: {value}")
    
    def get_experiment_runs(self, experiment_name: str = None) -> list:
        """Get all runs from an experiment"""
        if not self.available:
            return []
        
        try:
            exp_name = experiment_name or self.experiment_name
            experiment = mlflow.get_experiment_by_name(exp_name)
            if experiment:
                runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
                return runs.to_dict('records')
            return []
        except Exception as e:
            logger.error(f"❌ Error retrieving runs: {e}")
            return []

# Global MLflow client instance - initialized with error handling
try:
    logger.info("Initializing MLflow client...")
    mlflow_client = BentleyMLflowClient()
except Exception as e:
    logger.warning(f"⚠️ Failed to initialize global MLflow client: {e}")
    mlflow_client = None

# Convenience functions for easy import
def log_portfolio_metrics(portfolio_data: Dict[str, Any], run_name: str = None):
    """Convenience function to log portfolio metrics"""
    if mlflow_client is None:
        logger.warning("MLflow client unavailable - skipping metric logging")
        return None
    return mlflow_client.log_portfolio_metrics(portfolio_data, run_name or "portfolio_analysis")

def log_trading_signals(signals_data: Dict[str, Any], run_name: str = None):
    """Convenience function to log trading signals"""
    if mlflow_client is None:
        logger.warning("MLflow client unavailable - skipping signal logging")
        return None
    return mlflow_client.log_trading_signals(signals_data, run_name or "trading_signals")

def log_data_ingestion(ingestion_stats: Dict[str, Any], run_name: str = None):
    """Convenience function to log data ingestion stats"""
    if mlflow_client is None:
        logger.warning("MLflow client unavailable - skipping ingestion logging")
        return None
    return mlflow_client.log_data_ingestion(ingestion_stats, run_name or "data_ingestion")

def start_run(run_name: str = None, experiment_name: str = None, tags: Dict[str, str] = None):
    """Convenience function to start MLflow run"""
    if mlflow_client is None:
        logger.warning("MLflow client unavailable - skipping run creation")
        return None
    return mlflow_client.start_run(run_name, experiment_name, tags)

# Example usage functions for testing
def test_mlflow_connection():
    """Test MLflow connection and log sample data"""
    logger.info("🧪 Testing MLflow connection...")
    
    sample_portfolio = {
        "total_value": 125430.50,
        "daily_return": 2.34,
        "total_return": 12.8,
        "sharpe_ratio": 1.45,
        "max_drawdown": -8.2,
        "num_positions": 15
    }
    
    sample_signals = {
        "strategy": "RSI_MACD",
        "total_signals": 45,
        "buy_signals": 28,
        "sell_signals": 17,
        "accuracy": 0.73,
        "avg_signal_strength": 0.85
    }
    
    sample_ingestion = {
        "source": "yahoo_finance",
        "rows_processed": 1250,
        "processing_time": 12.5,
        "status": "success",
        "symbols_updated": 25
    }
    
    # Test all logging functions
    log_portfolio_metrics(sample_portfolio, "test_portfolio")
    log_trading_signals(sample_signals, "test_signals")
    log_data_ingestion(sample_ingestion, "test_ingestion")
    
    logger.info("✅ MLflow test completed")

if __name__ == "__main__":
    test_mlflow_connection()