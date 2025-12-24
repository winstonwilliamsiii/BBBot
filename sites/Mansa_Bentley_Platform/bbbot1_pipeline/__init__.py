"""
BentleyBot Data Pipeline Package
Modular ingestion and derivation for market data
"""

import yaml
import os

__version__ = "1.0.0"
__author__ = "BentleyBot Team"

# Package-level imports for easy access
from .db import get_mysql_connection, get_mysql_engine
from .ingest_yfinance import fetch_yfinance_prices, run_yfinance_ingestion
from .derive_ratios import calculate_pe_ratio, calculate_moving_averages


def load_tickers_config():
    """Load ticker configuration from YAML file.
    
    Returns:
        dict: Configuration dictionary with 'tickers', 'database', 'pipeline' keys
    """
    config_path = os.path.join(os.path.dirname(__file__), 'tickers_config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


__all__ = [
    'get_mysql_connection',
    'get_mysql_engine',
    'fetch_yfinance_prices',
    'run_yfinance_ingestion',
    'calculate_pe_ratio',
    'calculate_moving_averages',
    'load_tickers_config',
]
