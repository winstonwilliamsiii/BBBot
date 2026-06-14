"""
Broker API Integration Module
Unified interface for the supported direct broker integrations.

Supported here:
- Interactive Brokers (forex, futures, commodities)

Route Alpaca, MT5, and prop-firm execution through the FastAPI broker router.
"""

import logging
import os
import socket
from datetime import datetime
from typing import Any, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================
# INTERACTIVE BROKERS API - Forex, Futures, Commodities
# ============================================

class IBKRClient:
    """
    Interactive Brokers API client for forex, futures, and commodities
    Docs: https://interactivebrokers.github.io/tws-api/
    """
    
    def __init__(self):
        self.host = os.getenv("IBKR_HOST", "127.0.0.1")
        self.port = self._resolve_port()  # 7497 for TWS paper, 7496 for live
        self.client_id = int(os.getenv("IBKR_CLIENT_ID", "1"))
        self.app = None

    def _is_port_open(self, port: int, timeout: float = 0.8) -> bool:
        """Return True when the configured IBKR API socket is accepting connections."""
        try:
            with socket.create_connection((self.host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def _resolve_port(self) -> int:
        """Use IBKR_PORT when provided, otherwise auto-detect paper/live TWS socket."""
        env_port = os.getenv("IBKR_PORT")
        if env_port:
            return int(env_port)

        # Prefer paper by default, then fallback to live if that is the active port.
        if self._is_port_open(7497):
            return 7497
        if self._is_port_open(7496):
            return 7496

        # Keep legacy default when neither port is reachable during initialization.
        return 7497
        
    def connect(self):
        """Initialize IBKR connection"""
        try:
            from ibapi.client import EClient
            from ibapi.wrapper import EWrapper
            
            class IBApp(EWrapper, EClient):
                def __init__(self):
                    EClient.__init__(self, self)

                def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
                    logger.error(
                        f"IBKR API error reqId={reqId} code={errorCode} msg={errorString}"
                    )

                def nextValidId(self, orderId):
                    logger.info(f"IBKR API session ready. nextValidId={orderId}")
            
            self.app = IBApp()
            self.app.connect(self.host, self.port, self.client_id)

            if not self.app.isConnected():
                logger.error(
                    f"❌ IBKR API not connected to {self.host}:{self.port}. "
                    "Check TWS API settings, trusted IPs, and port."
                )
                self.app = None
                return False

            logger.info(f"✅ IBKR connected successfully to {self.host}:{self.port}")
            return True
        
        except ImportError:
            logger.error("❌ ibapi package not installed. Run: pip install ibapi")
            return False
        except Exception as e:
            logger.error(f"❌ IBKR connection failed: {e}")
            return False
    
    def place_order(self, symbol: str, side: str, quantity: float, 
                    sec_type: str = "FUT", exchange: str = "CME") -> Dict[str, Any]:
        """
        Place order on Interactive Brokers
        
        Args:
            symbol: Contract symbol (e.g., 'ES' for E-mini S&P, 'EUR.USD' for forex)
            side: 'BUY' or 'SELL'
            quantity: Contract quantity
            sec_type: 'FUT' (futures), 'CASH' (forex), 'CMDTY' (commodities)
            exchange: 'CME', 'GLOBEX', 'IDEALPRO' (for forex)
        
        Returns:
            Order confirmation dict
        """
        if not self.app:
            self.connect()
        
        try:
            from ibapi.contract import Contract
            from ibapi.order import Order
            
            # Create contract
            contract = Contract()
            contract.symbol = symbol
            contract.secType = sec_type
            contract.exchange = exchange
            contract.currency = "USD"
            
            # Create order
            order = Order()
            order.action = side.upper()
            order.totalQuantity = quantity
            order.orderType = "MKT"
            
            # Place order (requires order ID management)
            order_id = 1  # In production, use nextValidOrderId from EWrapper
            self.app.placeOrder(order_id, contract, order)
            
            logger.info(f"✅ IBKR {side} order placed: {symbol} x{quantity} ({sec_type})")
            return {
                "broker": "ibkr",
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "sec_type": sec_type,
                "exchange": exchange,
                "order_id": order_id,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ IBKR order failed: {e}")
            return {"error": str(e), "broker": "ibkr"}
    
    def get_positions(self):
        """Get current IBKR positions"""
        if not self.app:
            self.connect()
        
        try:
            self.app.reqPositions()
            logger.info("✅ IBKR position request sent")
            # Note: Positions returned asynchronously via EWrapper callbacks
            return []
        except Exception as e:
            logger.error(f"❌ Failed to get IBKR positions: {e}")
            return []


def _unsupported_broker_message(broker: str) -> dict[str, str]:
    return {
        "error": (
            f"Broker '{broker}' is no longer supported in bbbot1_pipeline.broker_api. "
            "Use backend.api.mansa_ai_router for Alpaca, MT5, and prop-firm execution."
        )
    }


# ============================================
# UNIFIED TRADING INTERFACE
# ============================================

def execute_trade(broker: str, symbol: str, side: str, quantity: float, **kwargs) -> Dict[str, Any]:
    """
    Unified trade execution across supported direct brokers.
    
    Args:
        broker: 'ibkr'
        symbol: Ticker/contract symbol
        side: 'BUY' or 'SELL'
        quantity: Amount to trade
        **kwargs: Additional broker-specific parameters
    
    Returns:
        Order confirmation dict
    
    Example:
        # Futures on IBKR
        execute_trade('ibkr', 'ES', 'BUY', 1, sec_type='FUT', exchange='CME')
        
    """
    broker = broker.lower()
    
    if broker == "ibkr":
        client = IBKRClient()
        return client.place_order(symbol, side, quantity, **kwargs)

    unsupported = _unsupported_broker_message(broker)
    logger.error(f"❌ {unsupported['error']}")
    return unsupported


def get_all_positions() -> Dict[str, list]:
    """
    Get positions from supported direct brokers.
    
    Returns:
        Dict with broker names as keys and position lists as values
    """
    positions = {}
    
    # IBKR positions
    try:
        ibkr_client = IBKRClient()
        positions['ibkr'] = ibkr_client.get_positions()
    except Exception as e:
        logger.error(f"Failed to get IBKR positions: {e}")
        positions['ibkr'] = []
    
    return positions


# ============================================
# TESTING & VALIDATION
# ============================================

if __name__ == "__main__":
    """Test broker connections and API calls"""
    print("=" * 70)
    print("🧪 Testing Broker API Integrations")
    print("=" * 70)
    
    # Test IBKR
    print("\n1️⃣  Testing IBKR (Forex/Futures/Commodities)...")
    ibkr_test = execute_trade("ibkr", "ES", "BUY", 1, sec_type="FUT", exchange="CME")
    print(f"Result: {ibkr_test}")
    
    # Get all positions
    print("\n2️⃣  Getting all positions...")
    all_positions = get_all_positions()
    for broker, positions in all_positions.items():
        print(f"{broker.upper()}: {len(positions)} positions")

    print("\n3️⃣  Unsupported brokers are routed through backend.api.mansa_ai_router")
    
    print("\n" + "=" * 70)
    print("✅ Broker API testing complete")
    print("=" * 70)
