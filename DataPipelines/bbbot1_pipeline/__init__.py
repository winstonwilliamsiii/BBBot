"""
BentleyBot Data Pipeline Package
Modular ingestion and derivation for market data
"""

import yaml
import os

__version__ = "1.0.0"
__author__ = "BentleyBot Team"

# Package-level imports for easy access with graceful fallbacks
try:
    from .db import get_mysql_connection, get_mysql_engine
    DB_AVAILABLE = True
except ImportError as e:
    DB_AVAILABLE = False
    get_mysql_connection = None
    get_mysql_engine = None

try:
    from .ingest_yfinance import fetch_yfinance_prices, run_yfinance_ingestion
    INGEST_AVAILABLE = True
except ImportError as e:
    INGEST_AVAILABLE = False
    fetch_yfinance_prices = None
    run_yfinance_ingestion = None

try:
    from .derive_ratios import calculate_pe_ratio, calculate_moving_averages
    DERIVE_AVAILABLE = True
except ImportError as e:
    DERIVE_AVAILABLE = False
    calculate_pe_ratio = None
    calculate_moving_averages = None


def load_tickers_config():
    """Load ticker configuration from YAML file.
    
    Returns:
        dict: Configuration dictionary with 'tickers', 'database', 'pipeline' keys
    """
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'tickers_config.yaml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        return {}


__all__ = [
    'get_mysql_connection',
    'get_mysql_engine',
    'fetch_yfinance_prices',
    'run_yfinance_ingestion',
    'calculate_pe_ratio',
    'calculate_moving_averages',
    'load_tickers_config',
    'DB_AVAILABLE',
    'INGEST_AVAILABLE',
    'DERIVE_AVAILABLE',
]
