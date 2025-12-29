"""
Frontend package for BentleyBudgetBot Investment Analysis.

Usage:
    from frontend import appwrite_client, get_transactions, get_watchlist
    from frontend import is_appwrite_connected, test_appwrite_connection
"""

# Core exports
from .frontend_package_initializer import (
    # Version info
    get_version,
    VERSION,
    PACKAGE_NAME,
    
    # Appwrite client and status
    appwrite_client,
    is_appwrite_connected,
    test_appwrite_connection,
    APPWRITE_SDK_AVAILABLE,
    
    # Service functions
    get_transactions,
    create_transaction,
    get_watchlist,
    add_to_watchlist,
    get_user_profile,
    get_bot_metrics,
    
    # Function IDs for reference
    FUNCTION_IDS,
)

# Optional SDK exports (may be None if SDK not installed)
try:
    from .frontend_package_initializer import database, account, client
except ImportError:
    database = None
    account = None
    client = None

__all__ = [
    "get_version",
    "VERSION",
    "PACKAGE_NAME",
    "appwrite_client",
    "is_appwrite_connected",
    "test_appwrite_connection",
    "APPWRITE_SDK_AVAILABLE",
    "get_transactions",
    "create_transaction",
    "get_watchlist",
    "add_to_watchlist",
    "get_user_profile",
    "get_bot_metrics",
    "FUNCTION_IDS",
    "database",
    "account",
    "client",
]