"""
Environment Configuration Manager - Compatibility Wrapper
This file maintains backwards compatibility by importing from the new location.

The actual implementation is now in src/utils/config_env.py
"""

# Import everything from the new location
from src.utils.config_env import *

# For backwards compatibility, expose the main symbols
__all__ = ['EnvironmentConfig', 'reload_env', 'CRITICAL_VARS', 'IMPORTANT_VARS']
