"""
Webull Trading API Client
Integrates Webull OpenAPI SDK with BentleyBot
"""

import os
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

from webull.core.client import ApiClient
from webull.trade.trade_client import TradeClient

# Load environment variables
load_dotenv()


class WebullClient:
    """
    Custom Webull API wrapper for BentleyBot
    Handles authentication, account management, and trading operations
    """

    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        region_id: str = "us",
        use_production: bool = False
    ):
        """
        Initialize Webull API client
        
        Args:
            app_key: Webull API app key (defaults to env WEBULL_APP_KEY)
            app_secret: Webull API secret (defaults to env WEBULL_APP_SECRET)
            region_id: Region identifier (default: 'us')
            use_production: Use production endpoint (default: False for test)
        """
        self.app_key = app_key or os.getenv("WEBULL_APP_KEY")
        self.app_secret = app_secret or os.getenv("WEBULL_APP_SECRET")
        self.region_id = region_id
        self.use_production = use_production
        
        if not self.app_key or not self.app_secret:
            raise ValueError(
                "Webull API credentials not found. "
                "Set WEBULL_APP_KEY and WEBULL_APP_SECRET in .env file"
            )
        
        # Initialize API client
        self.api_client = ApiClient(self.app_key, self.app_secret, self.region_id)
        
        # Set endpoint
        endpoint = (
            "api.webull.com" if use_production 
            else "us-openapi-alb.uat.webullbroker.com"
        )
        self.api_client.add_endpoint(self.region_id, endpoint)
        
        # Initialize trade client
        self.trade_client = TradeClient(self.api_client)
        
        # Cache for account data
        self._accounts_cache: Optional[List[Dict]] = None
        self._default_account_id: Optional[str] = None

    # =====================================================
    # ACCOUNT MANAGEMENT
    # =====================================================

    def get_accounts(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of all trading accounts
        
        Args:
            refresh: Force refresh from API (default: False)
            
        Returns:
            List of account dictionaries
        """
        if self._accounts_cache is None or refresh:
            response = self.trade_client.account_v2.get_account_list()
            if response.status_code == 200:
                self._accounts_cache = response.json()
            else:
                raise Exception(f"Failed to fetch accounts: {response.text}")
        
        return self._accounts_cache or []

    def get_default_account_id(self) -> str:
        """
        Get the default account ID (first account)
        
        Returns:
            Account ID string
        """
        if self._default_account_id is None:
            accounts = self.get_accounts()
            if not accounts:
                raise Exception("No Webull accounts found")
            self._default_account_id = accounts[0].get('account_id')
        
        return self._default_account_id

    def get_account_balance(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get account balance information
        
        Args:
            account_id: Specific account ID (defaults to first account)
            
        Returns:
            Balance dictionary with buying_power, cash, etc.
        """
        account_id = account_id or self.get_default_account_id()
        response = self.trade_client.account_v2.get_account_balance(account_id)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch balance: {response.text}")

    def get_account_positions(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get current positions/holdings
        
        Args:
            account_id: Specific account ID (defaults to first account)
            
        Returns:
            List of position dictionaries
        """
        account_id = account_id or self.get_default_account_id()
        response = self.trade_client.account_v2.get_account_position(account_id)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch positions: {response.text}")

    # =====================================================
    # ORDER MANAGEMENT - EQUITY ORDERS
    # =====================================================

    def place_equity_order(
        self,
        symbol: str,
        quantity: int,
        side: str,
        order_type: str = "MARKET",
        limit_price: Optional[float] = None,
        account_id: Optional[str] = None,
        time_in_force: str = "DAY"
    ) -> Dict[str, Any]:
        """
        Place a simple equity order
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
            quantity: Number of shares
            side: 'BUY' or 'SELL'
            order_type: 'MARKET' or 'LIMIT' (default: MARKET)
            limit_price: Limit price (required if order_type is LIMIT)
            account_id: Specific account ID (defaults to first account)
            time_in_force: 'DAY' or 'GTC' (default: DAY)
            
        Returns:
            Order placement response
        """
        account_id = account_id or self.get_default_account_id()
        
        if order_type == "LIMIT" and limit_price is None:
            raise ValueError("limit_price required for LIMIT orders")
        
        client_order_id = uuid.uuid4().hex
        
        order_data = [{
            "combo_type": "NORMAL",
            "client_order_id": client_order_id,
            "symbol": symbol.upper(),
            "instrument_type": "EQUITY",
            "market": "US",
            "order_type": order_type,
            "quantity": str(quantity),
            "support_trading_session": "CORE",
            "side": side.upper(),
            "time_in_force": time_in_force,
            "entrust_type": "QTY"
        }]
        
        if order_type == "LIMIT":
            order_data[0]["limit_price"] = str(limit_price)
        
        response = self.trade_client.order_v2.place_order(account_id, order_data)
        
        if response.status_code == 200:
            return {
                "success": True,
                "client_order_id": client_order_id,
                "response": response.json()
            }
        else:
            raise Exception(f"Order placement failed: {response.text}")

    def preview_equity_order(
        self,
        symbol: str,
        quantity: int,
        side: str,
        order_type: str = "MARKET",
        limit_price: Optional[float] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Preview an equity order before placing it
        
        Args:
            Same as place_equity_order
            
        Returns:
            Order preview with estimated costs/proceeds
        """
        account_id = account_id or self.get_default_account_id()
        
        if order_type == "LIMIT" and limit_price is None:
            raise ValueError("limit_price required for LIMIT orders")
        
        order_data = [{
            "combo_type": "NORMAL",
            "client_order_id": uuid.uuid4().hex,
            "symbol": symbol.upper(),
            "instrument_type": "EQUITY",
            "market": "US",
            "order_type": order_type,
            "quantity": str(quantity),
            "support_trading_session": "CORE",
            "side": side.upper(),
            "time_in_force": "DAY",
            "entrust_type": "QTY"
        }]
        
        if order_type == "LIMIT":
            order_data[0]["limit_price"] = str(limit_price)
        
        response = self.trade_client.order_v2.preview_order(account_id, order_data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Order preview failed: {response.text}")

    def cancel_order(
        self,
        client_order_id: str,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel an existing order
        
        Args:
            client_order_id: The client order ID to cancel
            account_id: Specific account ID (defaults to first account)
            
        Returns:
            Cancellation response
        """
        account_id = account_id or self.get_default_account_id()
        response = self.trade_client.order_v2.cancel_order(account_id, client_order_id)
        
        if response.status_code == 200:
            return {"success": True, "response": response.json()}
        else:
            raise Exception(f"Order cancellation failed: {response.text}")

    def get_open_orders(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open orders
        
        Args:
            account_id: Specific account ID (defaults to first account)
            
        Returns:
            List of open orders
        """
        account_id = account_id or self.get_default_account_id()
        response = self.trade_client.order_v2.get_order_open(account_id=account_id)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch open orders: {response.text}")

    def get_order_detail(
        self,
        client_order_id: str,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get details of a specific order
        
        Args:
            client_order_id: The client order ID
            account_id: Specific account ID (defaults to first account)
            
        Returns:
            Order details
        """
        account_id = account_id or self.get_default_account_id()
        response = self.trade_client.order_v2.get_order_detail(account_id, client_order_id)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch order detail: {response.text}")

    # =====================================================
    # OPTIONS TRADING
    # =====================================================

    def place_option_order(
        self,
        symbol: str,
        strike_price: float,
        option_expire_date: str,
        option_type: str,
        quantity: int,
        side: str,
        order_type: str = "LIMIT",
        limit_price: Optional[float] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Place an options order
        
        Args:
            symbol: Underlying stock symbol
            strike_price: Strike price
            option_expire_date: Expiration date (format: 'YYYY-MM-DD')
            option_type: 'CALL' or 'PUT'
            quantity: Number of contracts
            side: 'BUY' or 'SELL'
            order_type: 'LIMIT' or 'MARKET' (default: LIMIT)
            limit_price: Limit price per contract
            account_id: Specific account ID
            
        Returns:
            Order placement response
        """
        account_id = account_id or self.get_default_account_id()
        
        if order_type == "LIMIT" and limit_price is None:
            raise ValueError("limit_price required for LIMIT orders")
        
        client_order_id = uuid.uuid4().hex
        
        order_data = [{
            "client_order_id": client_order_id,
            "combo_type": "NORMAL",
            "order_type": order_type,
            "quantity": str(quantity),
            "option_strategy": "SINGLE",
            "side": side.upper(),
            "time_in_force": "DAY",
            "entrust_type": "QTY",
            "legs": [{
                "side": side.upper(),
                "quantity": str(quantity),
                "symbol": symbol.upper(),
                "strike_price": str(strike_price),
                "option_expire_date": option_expire_date,
                "instrument_type": "OPTION",
                "option_type": option_type.upper(),
                "market": "US"
            }]
        }]
        
        if order_type == "LIMIT":
            order_data[0]["limit_price"] = str(limit_price)
        
        response = self.trade_client.order_v2.place_option(account_id, order_data)
        
        if response.status_code == 200:
            return {
                "success": True,
                "client_order_id": client_order_id,
                "response": response.json()
            }
        else:
            raise Exception(f"Option order placement failed: {response.text}")

    # =====================================================
    # UTILITY METHODS
    # =====================================================

    def get_portfolio_summary(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive portfolio summary
        
        Args:
            account_id: Specific account ID (defaults to first account)
            
        Returns:
            Dictionary with balance, positions, and summary metrics
        """
        account_id = account_id or self.get_default_account_id()
        
        balance = self.get_account_balance(account_id)
        positions = self.get_account_positions(account_id)
        
        # Calculate portfolio metrics
        total_value = balance.get('net_liquidation_value', 0)
        total_positions = len(positions) if positions else 0
        
        return {
            "account_id": account_id,
            "total_value": total_value,
            "cash_balance": balance.get('cash_balance', 0),
            "buying_power": balance.get('buying_power', 0),
            "total_positions": total_positions,
            "positions": positions,
            "balance_details": balance,
            "timestamp": datetime.now().isoformat()
        }

    def format_position_for_display(self, position: Dict[str, Any]) -> str:
        """
        Format a position for human-readable display
        
        Args:
            position: Position dictionary from API
            
        Returns:
            Formatted string
        """
        symbol = position.get('symbol', 'N/A')
        quantity = position.get('quantity', 0)
        market_value = position.get('market_value', 0)
        cost_basis = position.get('cost_basis', 0)
        unrealized_pnl = position.get('unrealized_profit_loss', 0)
        pnl_percent = (unrealized_pnl / cost_basis * 100) if cost_basis else 0
        
        return (
            f"{symbol}: {quantity} shares | "
            f"Value: ${market_value:,.2f} | "
            f"P&L: ${unrealized_pnl:,.2f} ({pnl_percent:+.2f}%)"
        )


# =====================================================
# CONVENIENCE FUNCTION
# =====================================================

def create_webull_client(use_production: bool = False) -> WebullClient:
    """
    Factory function to create configured Webull client
    
    Args:
        use_production: Use production endpoint (default: False)
        
    Returns:
        Configured WebullClient instance
    """
    return WebullClient(use_production=use_production)
