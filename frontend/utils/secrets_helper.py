"""
Streamlit Secrets Helper
Provides unified access to secrets from Streamlit Cloud or environment variables
"""

import os
import streamlit as st
from typing import Optional


def get_secret(key: str, default: Optional[str] = None, section: Optional[str] = None) -> str:
    """
    Get a secret value with priority:
    1. Streamlit Cloud secrets (production)
    2. Environment variables (local development)
    3. Default value (fallback)
    
    Args:
        key: Secret key name (e.g., 'ALPACA_API_KEY')
        default: Default value if not found
        section: Optional TOML section (e.g., 'mysql', 'alpaca')
    
    Returns:
        Secret value as string
    
    Example:
        # Get from root level or env
        api_key = get_secret('ALPACA_API_KEY')
        
        # Get from specific TOML section
        db_host = get_secret('MYSQL_HOST', section='mysql')
    """
    # Try Streamlit secrets first (for Streamlit Cloud)
    try:
        if hasattr(st, 'secrets'):
            # Try section-specific first
            if section and section in st.secrets:
                if key in st.secrets[section]:
                    return str(st.secrets[section][key])
            
            # Try root level
            if key in st.secrets:
                return str(st.secrets[key])
    except Exception:
        pass
    
    # Fall back to environment variables (for local development)
    env_value = os.getenv(key, default)
    return env_value if env_value is not None else default


def get_mysql_config(database: str = None) -> dict:
    """
    Get MySQL connection configuration from secrets or environment.
    Automatically maps databases for Railway production environment.
    
    Args:
        database: Optional specific database name. If not provided, uses MYSQL_DATABASE env var.
    
    Returns:
        dict: MySQL configuration with host, port, user, password, database
    """
    # Get database from parameter, env var, or default
    if database is None:
        database = get_secret('MYSQL_DATABASE', default=get_secret('DB_NAME', default='mansa_bot'))

    # For production Railway, map default database names to actual databases
    host = get_secret('MYSQL_HOST', default=get_secret('DB_HOST', default='127.0.0.1'))
    is_railway = any(x in host for x in ('railway', 'nozomi'))

    # ---
    # 🚦 AUTO-MAPPING: On Railway, mansa_bot/railway → bbbot1 for trading signals
    # This ensures the app always uses the correct DB for ML trading signals
    if is_railway and database in ('mansa_bot', 'railway'):
        database = 'bbbot1'
    # ---

    return {
        'host': host,
        'port': int(get_secret('MYSQL_PORT', default=get_secret('DB_PORT', default='54537' if is_railway else '3306'))),
        'user': get_secret('MYSQL_USER', default=get_secret('DB_USER', default='root')),
        'password': get_secret('MYSQL_PASSWORD', default=get_secret('DB_PASSWORD', default='root')),
        'database': database,
    }


def get_mysql_url(database: str = None) -> str:
    """
    Get SQLAlchemy-compatible MySQL connection URL.
    
    Args:
        database (str, optional): Database name to use. If None, uses default from config.
    
    Returns:
        str: Connection URL like mysql+pymysql://user:pass@host:port/database
    """
    config = get_mysql_config(database=database)
    return (
        f"mysql+pymysql://{config['user']}:{config['password']}"
        f"@{config['host']}:{config['port']}/{config['database']}"
    )


def get_alpaca_config() -> dict:
    """
    Get Alpaca trading API configuration.
    
    Returns:
        dict: Alpaca configuration with api_key, secret_key, paper
        
    Raises:
        ValueError: If credentials are not configured
    """
    api_key = get_secret('ALPACA_API_KEY')
    secret_key = get_secret('ALPACA_SECRET_KEY')
    paper = get_secret('ALPACA_PAPER', default=None)
    if paper is None:
        env = get_secret('ALPACA_ENVIRONMENT', default='paper')
        paper = 'true' if str(env).lower() == 'paper' else 'false'
    
    if not api_key or api_key == 'your-alpaca-api-key-here':
        raise ValueError(
            "❌ Alpaca credentials not configured.\n"
            "For Streamlit Cloud: Add to Settings → Secrets\n"
            "For local: Add to .env file\n"
            "See STREAMLIT_CLOUD_SECRETS_TEMPLATE.toml"
        )
    
    if not secret_key or secret_key == 'your-alpaca-secret-key-here':
        raise ValueError(
            "❌ Alpaca secret key not configured.\n"
            "For Streamlit Cloud: Add to Settings → Secrets\n"
            "For local: Add to .env file"
        )
    
    return {
        'api_key': api_key,
        'secret_key': secret_key,
        'paper': paper.lower() in ('true', '1', 'yes'),
    }


def get_plaid_config() -> dict:
    """
    Get Plaid bank linking API configuration.
    
    Returns:
        dict: Plaid configuration with client_id, secret, env
        
    Raises:
        ValueError: If credentials are not configured
    """
    client_id = get_secret('PLAID_CLIENT_ID', section='plaid')
    secret = get_secret('PLAID_SECRET', section='plaid')
    env = get_secret('PLAID_ENV', section='plaid', default=None)
    if not env:
        env = get_secret('PLAID_ENVIRONMENT', section='plaid', default='sandbox')
    
    if not client_id or client_id == 'your-plaid-client-id':
        raise ValueError(
            "❌ Plaid client_id not configured.\n"
            "For Streamlit Cloud: Add to Settings → Secrets\n"
            "For local: Add to .env file\n"
            "See STREAMLIT_CLOUD_SECRETS_TEMPLATE.toml"
        )
    
    if not secret or secret == 'your-plaid-sandbox-secret':
        raise ValueError(
            "❌ Plaid secret not configured.\n"
            "For Streamlit Cloud: Add to Settings → Secrets\n"
            "For local: Add to .env file"
        )
    
    return {
        'client_id': client_id,
        'secret': secret,
        'env': env,
        'items_collection_id': get_secret('PLAID_ITEMS_COLLECTION_ID', section='plaid', default='plaid_items'),
    }


def check_credentials_status() -> dict:
    """
    Check which credential sets are properly configured.
    
    Returns:
        dict: Status of each credential set (mysql, alpaca, plaid)
    """
    status = {}
    
    # Check MySQL
    try:
        config = get_mysql_config()
        status['mysql'] = {
            'configured': True,
            'database': config['database'],
            'host': config['host'],
        }
    except Exception as e:
        status['mysql'] = {
            'configured': False,
            'error': str(e),
        }
    
    # Check Alpaca
    try:
        get_alpaca_config()
        status['alpaca'] = {'configured': True}
    except Exception as e:
        status['alpaca'] = {
            'configured': False,
            'error': str(e),
        }
    
    # Check Plaid
    try:
        get_plaid_config()
        status['plaid'] = {'configured': True}
    except Exception as e:
        status['plaid'] = {
            'configured': False,
            'error': str(e),
        }
    
    return status
