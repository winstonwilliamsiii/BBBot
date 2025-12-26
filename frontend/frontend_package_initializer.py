"""
Frontend package initializer for BentleyBudgetBot Investment Analysis.

This file ensures the `frontend` directory is treated as a Python package.
It centralizes common imports, configuration, and helper functions
for Streamlit pages and Appwrite API integration.
"""

import os
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv(override=True)

# Expose key modules for easy import
from . import components
from . import utils
from . import styles

# Optional: Appwrite client setup
try:
    from appwrite.client import Client
    from appwrite.services.databases import Databases
    from appwrite.services.account import Account



    # Example service bindings
    account = Account(client)
    database = Databases(client)

except ImportError:
    # Appwrite not installed or not needed in this context
    client = None
    account = None
    database = None

# Utility: global constants
PACKAGE_NAME = "frontend"
VERSION = "0.1.0"

def get_version() -> str:
    """Return the current frontend package version."""
    return VERSION

def is_appwrite_connected() -> bool:
    """Check if Appwrite client is initialized."""
    return client is not None