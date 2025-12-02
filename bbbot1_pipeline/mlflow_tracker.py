"""
MLFlow Logging Module for BentleyBot
Logs experiments, metrics, parameters, and artifacts to MLFlow
"""

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd


class BentleyBotMLFlowTracker:
    """MLFlow tracking for BentleyBot financial analysis"""
    
    def __init__(self, tracking_uri: str = None, experiment_name: str = "bentley_bot_analysis"):
        """
        Initialize MLFlow tracker
        
        Args:
            tracking_uri: MLFlow tracking server URI (default: local file storage)
            experiment_name: Name of the MLFlow experiment
        """
        # Set tracking URI (use MySQL if provided, otherwise local file storage)
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        else:
            # Default to local file storage in mlflow_logs directory
            mlflow_dir = os.path.join(os.path.dirname(__file__), '../data/mlflow')
            os.makedirs(mlflow_dir, exist_ok=True)
            mlflow.set_tracking_uri(f"file://{os.path.abspath(mlflow_dir)}")
        
        # Set or create experiment
        mlflow.set_experiment(experiment_name)
        self.client = MlflowClient()
        self.experiment_name = experiment_name
        
    def log_fundamental_ratios(
        self, 
        ticker: str, 
        report_date: str, 
        ratios: Dict[str, float], 
        source: str = "AlphaVantage+YFinance"
    ):
        """
        Log fundamental ratio analysis into MLFlow
        
        Args:
            ticker: Stock ticker symbol
            report_date: Date of the financial report
            ratios: Dictionary of calculated ratios (e.g., PE, PB, ROE)
            source: Data source identifier
        """
        run_name = f"{ticker}_{report_date}_ratios"
        
        with mlflow.start_run(run_name=run_name):
            # Log parameters
            mlflow.log_param("ticker", ticker)
            mlflow.log_param("report_date", report_date)
            mlflow.log_param("source", source)
            mlflow.log_param("analysis_timestamp", datetime.now().isoformat())
            
            # Log metrics (ratios)
            for key, value in ratios.items():
                if value is not None:
                    try:
                        mlflow.log_metric(key, float(value))
                    except (ValueError, TypeError):
                        print(f"⚠️ Could not log metric {key}={value} (not numeric)")
            
            # Save raw ratios as JSON artifact
            artifact_path = f"ratios_{ticker}_{report_date}.json"
            with open(artifact_path, "w") as f:
                json.dump(ratios, f, indent=2, default=str)
            
            mlflow.log_artifact(artifact_path)
            
            # Clean up local artifact file
            if os.path.exists(artifact_path):
                os.remove(artifact_path)
    
    def log_portfolio_performance(
        self,
        portfolio_name: str,
        metrics: Dict[str, float],
        holdings: Optional[pd.DataFrame] = None
    ):
        """
        Log portfolio performance metrics
        
        Args:
            portfolio_name: Name of the portfolio
            metrics: Performance metrics (total_value, returns, etc.)
            holdings: DataFrame of portfolio holdings (optional)
        """
        run_name = f"portfolio_{portfolio_name}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        with mlflow.start_run(run_name=run_name):
            # Log parameters
            mlflow.log_param("portfolio_name", portfolio_name)
            mlflow.log_param("timestamp", datetime.now().isoformat())
            
            if holdings is not None:
                mlflow.log_param("num_holdings", len(holdings))
            
            # Log metrics
            for key, value in metrics.items():
                if value is not None:
                    try:
                        mlflow.log_metric(key, float(value))
                    except (ValueError, TypeError):
                        print(f"⚠️ Could not log metric {key}={value}")
            
            # Log holdings as artifact if provided
            if holdings is not None:
                holdings_path = f"holdings_{portfolio_name}.csv"
                holdings.to_csv(holdings_path, index=False)
                mlflow.log_artifact(holdings_path)
                
                if os.path.exists(holdings_path):
                    os.remove(holdings_path)
    
    def log_data_ingestion(
        self,
        source: str,
        tickers: list,
        rows_fetched: int,
        success: bool,
        response_time: float
    ):
        """
        Log data ingestion operations
        
        Args:
            source: Data source (yfinance, Alpha Vantage, etc.)
            tickers: List of tickers fetched
            rows_fetched: Number of data rows retrieved
            success: Whether the operation succeeded
            response_time: API response time in seconds
        """
        run_name = f"ingestion_{source}_{datetime.now().strftime('%H%M%S')}"
        
        with mlflow.start_run(run_name=run_name):
            # Log parameters
            mlflow.log_param("source", source)
            mlflow.log_param("num_tickers", len(tickers))
            mlflow.log_param("tickers", str(tickers) if len(tickers) <= 10 else f"{len(tickers)} tickers")
            mlflow.log_param("timestamp", datetime.now().isoformat())
            mlflow.log_param("success", success)
            
            # Log metrics
            mlflow.log_metric("rows_fetched", rows_fetched)
            mlflow.log_metric("response_time_seconds", response_time)
            mlflow.log_metric("success_flag", 1 if success else 0)
    
    def get_recent_runs(self, max_results: int = 10) -> list:
        """
        Get recent MLFlow runs for the current experiment
        
        Args:
            max_results: Maximum number of runs to return
            
        Returns:
            List of MLFlow run objects
        """
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                return []
            
            runs = self.client.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=["start_time DESC"],
                max_results=max_results
            )
            
            return runs
        except Exception as e:
            print(f"⚠️ Error fetching MLFlow runs: {e}")
            return []
    
    def get_ratio_analysis_runs(self, ticker: Optional[str] = None, max_results: int = 20) -> list:
        """
        Get runs containing ratio analysis data
        
        Args:
            ticker: Optional ticker filter
            max_results: Maximum number of runs to return
            
        Returns:
            List of MLFlow run objects with ratio data
        """
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                return []
            
            # Build filter query
            filter_string = ""
            if ticker:
                filter_string = f"params.ticker = '{ticker}'"
            
            runs = self.client.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=filter_string,
                order_by=["params.report_date DESC"],
                max_results=max_results
            )
            
            # Filter for runs with ratio metrics
            ratio_runs = [run for run in runs if any('ratio' in key.lower() or 'pe' in key.lower() 
                                                      for key in run.data.metrics.keys())]
            
            return ratio_runs
        except Exception as e:
            print(f"⚠️ Error fetching ratio analysis runs: {e}")
            return []


# Global tracker instance (lazy initialization)
_tracker_instance = None


def get_tracker(tracking_uri: str = None, experiment_name: str = "bentley_bot_analysis") -> BentleyBotMLFlowTracker:
    """Get or create the global MLFlow tracker instance"""
    global _tracker_instance
    
    if _tracker_instance is None:
        _tracker_instance = BentleyBotMLFlowTracker(tracking_uri, experiment_name)
    
    return _tracker_instance


# Convenience functions for quick logging
def log_ratios(ticker: str, report_date: str, ratios: Dict[str, float], source: str = "AlphaVantage+YFinance"):
    """Quick function to log fundamental ratios"""
    tracker = get_tracker()
    tracker.log_fundamental_ratios(ticker, report_date, ratios, source)


def log_portfolio(portfolio_name: str, metrics: Dict[str, float], holdings: Optional[pd.DataFrame] = None):
    """Quick function to log portfolio metrics"""
    tracker = get_tracker()
    tracker.log_portfolio_performance(portfolio_name, metrics, holdings)


def log_ingestion(source: str, tickers: list, rows_fetched: int, success: bool, response_time: float):
    """Quick function to log data ingestion"""
    tracker = get_tracker()
    tracker.log_data_ingestion(source, tickers, rows_fetched, success, response_time)


if __name__ == "__main__":
    # Test the MLFlow tracker
    print("🧪 Testing BentleyBot MLFlow Tracker...")
    
    # Initialize tracker
    tracker = get_tracker()
    print(f"✅ Tracker initialized with experiment: {tracker.experiment_name}")
    
    # Test logging ratios
    test_ratios = {
        "pe_ratio": 25.3,
        "pb_ratio": 3.2,
        "roe": 0.18,
        "debt_to_equity": 0.45
    }
    
    log_ratios("IONQ", "2024-12-01", test_ratios, "Test")
    print("✅ Logged test ratios for IONQ")
    
    # Test logging portfolio
    test_metrics = {
        "total_value": 125430.50,
        "daily_return": 0.012,
        "num_assets": 8
    }
    
    log_portfolio("test_portfolio", test_metrics)
    print("✅ Logged test portfolio metrics")
    
    # Get recent runs
    recent_runs = tracker.get_recent_runs(max_results=5)
    print(f"\n📊 Found {len(recent_runs)} recent runs:")
    for run in recent_runs:
        print(f"  - {run.info.run_name} at {run.info.start_time}")
    
    print("\n✅ MLFlow tracker test complete!")
