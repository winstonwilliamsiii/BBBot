"""
Frontend package for BentleyBudgetBot Investment Analysis.

Usage:
    from frontend import appwrite_client, get_transactions, get_watchlist
    from frontend import is_appwrite_connected, test_appwrite_connection
"""

from importlib import import_module

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

_OPTIONAL_EXPORTS = {"database", "account", "client"}


def __getattr__(name: str):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    try:
        initializer = import_module(".frontend_package_initializer", __name__)
        value = getattr(initializer, name)
    except (ImportError, AttributeError):
        if name not in _OPTIONAL_EXPORTS:
            raise
        value = None

    globals()[name] = value
    return value
