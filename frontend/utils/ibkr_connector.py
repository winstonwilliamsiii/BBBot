"""
Compatibility shim for IBKR connector.
This module re-exports the connector from frontend.components to preserve legacy imports.
"""

from frontend.components.ibkr_connector import IBKRConnector, IBKRPosition

__all__ = ["IBKRConnector", "IBKRPosition"]
