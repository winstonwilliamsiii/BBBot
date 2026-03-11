"""
Streamlit Secrets Helper
Provides unified access to secrets from Streamlit Cloud or environment variables
"""

import os
import streamlit as st
from typing import Optional


def _clean_secret_value(value: Optional[str]) -> Optional[str]:
    """Normalize env/secret values by trimming whitespace and wrapping quotes."""
    if value is None:
        return None
    cleaned = str(value).strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in ("'", '"'):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def _lookup_secret_value(container, key: str) -> Optional[str]:
    """Lookup key in a secrets mapping with case-insensitive fallback."""
    if container is None:
        return None

    # Fast path exact match
    try:
        if key in container:
            return str(container[key])
    except Exception:
        pass

    # Case-insensitive fallback for differently cased keys in secrets
    try:
        for existing_key in container.keys():
            if str(existing_key).lower() == key.lower():
                return str(container[existing_key])
    except Exception:
        pass

    return None


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
            if section:
                section_obj = None
                if section in st.secrets:
                    section_obj = st.secrets[section]
                else:
                    # Case-insensitive section lookup
                    for existing_section in st.secrets.keys():
                        if str(existing_section).lower() == section.lower():
                            section_obj = st.secrets[existing_section]
                            break

                section_value = _lookup_secret_value(section_obj, key)
                if section_value is not None:
                    return section_value
            
            # Try root level
            root_value = _lookup_secret_value(st.secrets, key)
            if root_value is not None:
                return root_value
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

    # Auto-map database names for Railway production environment
    # mansa_bot and railway both point to bbbot1 on production
    if is_railway and database in ('mansa_bot', 'railway'):
        database = 'bbbot1'

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
    api_key = (
        get_secret('ALPACA_API_KEY')
        or get_secret('APCA_API_KEY_ID')
        or get_secret('ALPACA_KEY_ID')
        or get_secret('alpaca_api_key')
        or get_secret('apca_api_key_id')
        or get_secret('alpaca_key_id')
        or get_secret('ALPACA_API_KEY', section='alpaca')
        or get_secret('APCA_API_KEY_ID', section='alpaca')
        or get_secret('alpaca_api_key', section='alpaca')
        or get_secret('apca_api_key_id', section='alpaca')
        or get_secret('api_key', section='alpaca')
        or get_secret('key_id', section='alpaca')
    )
    secret_key = (
        get_secret('ALPACA_SECRET_KEY')
        or get_secret('APCA_API_SECRET_KEY')
        or get_secret('ALPACA_API_SECRET')
        or get_secret('alpaca_secret_key')
        or get_secret('apca_api_secret_key')
        or get_secret('alpaca_api_secret')
        or get_secret('ALPACA_SECRET_KEY', section='alpaca')
        or get_secret('APCA_API_SECRET_KEY', section='alpaca')
        or get_secret('ALPACA_SECRET', section='alpaca')
        or get_secret('alpaca_secret_key', section='alpaca')
        or get_secret('apca_api_secret_key', section='alpaca')
        or get_secret('alpaca_secret', section='alpaca')
        or get_secret('secret_key', section='alpaca')
        or get_secret('secret', section='alpaca')
    )
    api_key = _clean_secret_value(api_key)
    secret_key = _clean_secret_value(secret_key)
    paper = get_secret('ALPACA_PAPER', default=None)
    if paper is None:
        env = get_secret('ALPACA_ENVIRONMENT', default='paper')
        if str(env).lower() not in ('paper', 'live'):
            base_url = get_secret('ALPACA_BASE_URL', default='') or ''
            env = 'paper' if 'paper-api.alpaca.markets' in str(base_url).lower() else 'live'
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
    env = os.getenv('PLAID_ENV') or os.getenv('PLAID_ENVIRONMENT')
    if not env:
        env = get_secret('PLAID_ENV', section='plaid', default=None)
    if not env:
        env = get_secret('PLAID_ENVIRONMENT', section='plaid', default='sandbox')
    env = str(env).strip().lower()

    is_production = env == 'production'

    if is_production:
        client_id = (
            os.getenv('PLAID_CLIENT_ID_PRODUCTION')
            or os.getenv('PLAID_PRODUCTION_CLIENT_ID')
            or os.getenv('PLAID_CLIENT_ID')
            or
            get_secret('PLAID_CLIENT_ID_PRODUCTION', section='plaid', default=None)
            or get_secret('PLAID_PRODUCTION_CLIENT_ID', section='plaid', default=None)
            or get_secret('PLAID_CLIENT_ID', section='plaid')
        )
        secret = (
            os.getenv('PLAID_SECRET_PRODUCTION')
            or os.getenv('PLAID_PRODUCTION_SECRET')
            or os.getenv('PLAID_SECRET')
            or
            get_secret('PLAID_SECRET_PRODUCTION', section='plaid', default=None)
            or get_secret('PLAID_PRODUCTION_SECRET', section='plaid', default=None)
            or get_secret('PLAID_SECRET', section='plaid')
        )
    else:
        client_id = (
            os.getenv('PLAID_CLIENT_ID')
            or get_secret('PLAID_CLIENT_ID', section='plaid')
        )
        secret = (
            os.getenv('PLAID_SECRET')
            or get_secret('PLAID_SECRET', section='plaid')
        )
    
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
