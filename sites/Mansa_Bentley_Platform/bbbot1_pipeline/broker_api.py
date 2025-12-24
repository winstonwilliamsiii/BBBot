"""
Broker API Integration Module
Unified interface for trading across multiple brokers:
- Webull (equities, ETFs)
- Interactive Brokers (forex, futures, commodities)
- Binance (crypto)
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================
# WEBULL API - Equities & ETFs
# ============================================

class WebullClient:
    """
    Webull API client for equities and ETFs
    Docs: https://github.com/tedchou12/webull
    """
    
    def __init__(self):
        self.username = os.getenv("WEBULL_USERNAME")
        self.password = os.getenv("WEBULL_PASSWORD")
        self.device_id = os.getenv("WEBULL_DEVICE_ID")
        self.client = None
        
    def connect(self):
        """Initialize Webull connection"""
        try:
            from webull import webull
            self.client = webull()
            self.client.login(self.username, self.password, device_name=self.device_id)
            logger.info("✅ Webull connected successfully")
            return True
        except ImportError:
            logger.error("❌ webull package not installed. Run: pip install webull")
            return False
        except Exception as e:
            logger.error(f"❌ Webull connection failed: {e}")
            return False
    
    def place_order(self, symbol: str, side: str, quantity: float, order_type: str = "MKT") -> Dict[str, Any]:
        """
        Place order on Webull
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL', 'SPY')
            side: 'BUY' or 'SELL'
            quantity: Number of shares (must be integer for equities)
            order_type: 'MKT' (market) or 'LMT' (limit)
        
        Returns:
            Order confirmation dict with order_id and status
        """
        if not self.client:
            self.connect()
        
        try:
            # Webull requires integer quantity for equities
            quantity = int(quantity)
            
            if side.upper() == "BUY":
                result = self.client.place_order(
                    stock=symbol,
                    action="BUY",
                    orderType=order_type,
                    quant=quantity,
                    enforce="DAY"
                )
            elif side.upper() == "SELL":
                result = self.client.place_order(
                    stock=symbol,
                    action="SELL",
                    orderType=order_type,
                    quant=quantity,
                    enforce="DAY"
                )
            else:
                raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")
            
            logger.info(f"✅ Webull {side} order placed: {symbol} x{quantity}")
            return {
                "broker": "webull",
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "order_type": order_type,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Webull order failed: {e}")
            return {"error": str(e), "broker": "webull"}
    
    def get_positions(self):
        """Get current Webull positions"""
        if not self.client:
            self.connect()
        
        try:
            positions = self.client.get_positions()
            logger.info(f"✅ Retrieved {len(positions)} Webull positions")
            return positions
        except Exception as e:
            logger.error(f"❌ Failed to get Webull positions: {e}")
            return []


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
        self.port = int(os.getenv("IBKR_PORT", "7497"))  # 7497 for TWS paper, 7496 for live
        self.client_id = int(os.getenv("IBKR_CLIENT_ID", "1"))
        self.app = None
        
    def connect(self):
        """Initialize IBKR connection"""
        try:
            from ibapi.client import EClient
            from ibapi.wrapper import EWrapper
            from ibapi.contract import Contract
            
            class IBApp(EWrapper, EClient):
                def __init__(self):
                    EClient.__init__(self, self)
            
            self.app = IBApp()
            self.app.connect(self.host, self.port, self.client_id)
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


# ============================================
# BINANCE API - Cryptocurrency
# ============================================

class BinanceClient:
    """
    Binance API client for cryptocurrency trading
    Docs: https://python-binance.readthedocs.io/
    """
    
    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")
        self.testnet = os.getenv("BINANCE_TESTNET", "true").lower() == "true"
        self.client = None
        
    def connect(self):
        """Initialize Binance connection"""
        try:
            from binance.client import Client
            
            if self.testnet:
                # Use testnet for testing
                self.client = Client(
                    self.api_key, 
                    self.api_secret,
                    testnet=True
                )
                logger.info("✅ Binance TESTNET connected successfully")
            else:
                self.client = Client(self.api_key, self.api_secret)
                logger.info("✅ Binance LIVE connected successfully")
            
            return True
        
        except ImportError:
            logger.error("❌ python-binance package not installed. Run: pip install python-binance")
            return False
        except Exception as e:
            logger.error(f"❌ Binance connection failed: {e}")
            return False
    
    def place_order(self, symbol: str, side: str, quantity: float, order_type: str = "MARKET") -> Dict[str, Any]:
        """
        Place order on Binance
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT', 'ETHUSDT')
            side: 'BUY' or 'SELL'
            quantity: Crypto quantity (check symbol lot size)
            order_type: 'MARKET' or 'LIMIT'
        
        Returns:
            Order confirmation dict with order_id and status
        """
        if not self.client:
            self.connect()
        
        try:
            # Place market order
            if side.upper() == "BUY":
                result = self.client.order_market_buy(
                    symbol=symbol,
                    quantity=quantity
                )
            elif side.upper() == "SELL":
                result = self.client.order_market_sell(
                    symbol=symbol,
                    quantity=quantity
                )
            else:
                raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")
            
            logger.info(f"✅ Binance {side} order placed: {symbol} x{quantity}")
            return {
                "broker": "binance",
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "order_type": order_type,
                "order_id": result.get("orderId"),
                "status": result.get("status"),
                "fills": result.get("fills", []),
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Binance order failed: {e}")
            return {"error": str(e), "broker": "binance"}
    
    def get_positions(self):
        """Get current Binance account balances"""
        if not self.client:
            self.connect()
        
        try:
            account = self.client.get_account()
            balances = [
                b for b in account['balances'] 
                if float(b['free']) > 0 or float(b['locked']) > 0
            ]
            logger.info(f"✅ Retrieved {len(balances)} Binance balances")
            return balances
        except Exception as e:
            logger.error(f"❌ Failed to get Binance balances: {e}")
            return []


# ============================================
# UNIFIED TRADING INTERFACE
# ============================================

def execute_trade(broker: str, symbol: str, side: str, quantity: float, **kwargs) -> Dict[str, Any]:
    """
    Unified trade execution across all brokers
    
    Args:
        broker: 'webull', 'ibkr', or 'binance'
        symbol: Ticker/contract symbol
        side: 'BUY' or 'SELL'
        quantity: Amount to trade
        **kwargs: Additional broker-specific parameters
    
    Returns:
        Order confirmation dict
    
    Example:
        # Equities on Webull
        execute_trade('webull', 'AAPL', 'BUY', 100)
        
        # Futures on IBKR
        execute_trade('ibkr', 'ES', 'BUY', 1, sec_type='FUT', exchange='CME')
        
        # Crypto on Binance
        execute_trade('binance', 'BTCUSDT', 'BUY', 0.01)
    """
    broker = broker.lower()
    
    if broker == "webull":
        client = WebullClient()
        return client.place_order(symbol, side, quantity, **kwargs)
    
    elif broker == "ibkr":
        client = IBKRClient()
        return client.place_order(symbol, side, quantity, **kwargs)
    
    elif broker == "binance":
        client = BinanceClient()
        return client.place_order(symbol, side, quantity, **kwargs)
    
    else:
        error_msg = f"Unknown broker: {broker}. Supported: webull, ibkr, binance"
        logger.error(f"❌ {error_msg}")
        return {"error": error_msg}


def get_all_positions() -> Dict[str, list]:
    """
    Get positions from all brokers
    
    Returns:
        Dict with broker names as keys and position lists as values
    """
    positions = {}
    
    # Webull positions
    try:
        webull_client = WebullClient()
        positions['webull'] = webull_client.get_positions()
    except Exception as e:
        logger.error(f"Failed to get Webull positions: {e}")
        positions['webull'] = []
    
    # IBKR positions
    try:
        ibkr_client = IBKRClient()
        positions['ibkr'] = ibkr_client.get_positions()
    except Exception as e:
        logger.error(f"Failed to get IBKR positions: {e}")
        positions['ibkr'] = []
    
    # Binance positions
    try:
        binance_client = BinanceClient()
        positions['binance'] = binance_client.get_positions()
    except Exception as e:
        logger.error(f"Failed to get Binance positions: {e}")
        positions['binance'] = []
    
    return positions


# ============================================
# TESTING & VALIDATION
# ============================================

if __name__ == "__main__":
    """Test broker connections and API calls"""
    print("=" * 70)
    print("🧪 Testing Broker API Integrations")
    print("=" * 70)
    
    # Test Webull
    print("\n1️⃣  Testing Webull (Equities/ETFs)...")
    webull_test = execute_trade("webull", "AAPL", "BUY", 1)
    print(f"Result: {webull_test}")
    
    # Test IBKR
    print("\n2️⃣  Testing IBKR (Forex/Futures/Commodities)...")
    ibkr_test = execute_trade("ibkr", "ES", "BUY", 1, sec_type="FUT", exchange="CME")
    print(f"Result: {ibkr_test}")
    
    # Test Binance
    print("\n3️⃣  Testing Binance (Crypto)...")
    binance_test = execute_trade("binance", "BTCUSDT", "BUY", 0.001)
    print(f"Result: {binance_test}")
    
    # Get all positions
    print("\n4️⃣  Getting all positions...")
    all_positions = get_all_positions()
    for broker, positions in all_positions.items():
        print(f"{broker.upper()}: {len(positions)} positions")
    
    print("\n" + "=" * 70)
    print("✅ Broker API testing complete")
    print("=" * 70)
