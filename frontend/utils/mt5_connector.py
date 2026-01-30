"""
Compatibility shim for MT5 connector.
This module re-exports the connector from frontend.components to preserve legacy imports.
"""

from frontend.components.mt5_connector import MT5Connector, MT5Account, MT5Position

__all__ = ["MT5Connector", "MT5Account", "MT5Position"]
