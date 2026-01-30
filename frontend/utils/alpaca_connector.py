"""
Compatibility shim for Alpaca connector.
This module re-exports the connector from frontend.components to preserve legacy imports.
"""

from frontend.components.alpaca_connector import AlpacaConnector, AlpacaAccount, AlpacaPosition

__all__ = ["AlpacaConnector", "AlpacaAccount", "AlpacaPosition"]
