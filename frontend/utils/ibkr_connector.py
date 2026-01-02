"""
Interactive Brokers (IBKR) Gateway Connector
REST API integration for comprehensive trading

Features:
- Connect to IBKR Gateway/Client Portal
- Account management
- Portfolio positions
- Market data
- Order placement
- FOREX, Futures, Stocks, Options support
"""

import requests
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class IBKRPosition:
    """IBKR position data"""
    conid: int
    symbol: str
    position: float
    market_value: float
    avg_cost: float
    unrealized_pnl: float
    realized_pnl: float
    account_id: str


class IBKRConnector:
    """
    Interactive Brokers Gateway/Client Portal API Connector
    
    Usage:
        # Make sure IBKR Gateway is running on localhost:5000
        ibkr = IBKRConnector(base_url="https://localhost:5000")
        if ibkr.is_authenticated():
            account = ibkr.get_accounts()
            print(f"Connected to account: {account}")
    """
    
    def __init__(self, base_url: str = "https://localhost:5000", verify_ssl: bool = False):
        """
        Initialize IBKR connector
        
        Args:
            base_url: IBKR Gateway URL (default: https://localhost:5000)
            verify_ssl: Verify SSL certificates (usually False for local Gateway)
        """
        self.base_url = base_url.rstrip('/')
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.verify = verify_ssl
        
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        logger.info(f"IBKR connector initialized: {base_url}")
    
    def is_authenticated(self) -> bool:
        """Check if authenticated with IBKR"""
        try:
            response = self.session.get(
                f"{self.base_url}/v1/api/iserver/auth/status",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            authenticated = data.get('authenticated', False)
            
            if authenticated:
                logger.info("IBKR authentication successful")
            else:
                logger.warning("IBKR not authenticated - check Gateway connection")
            
            return authenticated
        except Exception as e:
            logger.error(f"Authentication check failed: {e}")
            return False
    
    def reauthenticate(self) -> bool:
        """Trigger reauthentication"""
        try:
            response = self.session.post(
                f"{self.base_url}/v1/api/iserver/reauthenticate",
                timeout=10
            )
            response.raise_for_status()
            logger.info("Reauthentication successful")
            return True
        except Exception as e:
            logger.error(f"Reauthentication failed: {e}")
            return False
    
    def get_accounts(self) -> Optional[List[str]]:
        """Get list of account IDs"""
        try:
            response = self.session.get(
                f"{self.base_url}/v1/api/portfolio/accounts",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            return None
    
    def get_account_summary(self, account_id: str) -> Optional[Dict]:
        """Get account summary"""
        try:
            response = self.session.get(
                f"{self.base_url}/v1/api/portfolio/{account_id}/summary",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return None
    
    def get_positions(self, account_id: Optional[str] = None) -> Optional[List[IBKRPosition]]:
        """
        Get portfolio positions
        
        Args:
            account_id: Specific account ID (if None, uses first account)
            
        Returns:
            List of IBKRPosition objects
        """
        try:
            # Get account ID if not provided
            if not account_id:
                accounts = self.get_accounts()
                if not accounts or len(accounts) == 0:
                    logger.error("No accounts found")
                    return None
                account_id = accounts[0]
            
            # Get positions
            response = self.session.get(
                f"{self.base_url}/v1/api/portfolio/{account_id}/positions/0",
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            positions = []
            
            for pos in data:
                positions.append(IBKRPosition(
                    conid=pos.get('conid', 0),
                    symbol=pos.get('contractDesc', ''),
                    position=float(pos.get('position', 0)),
                    market_value=float(pos.get('mktValue', 0)),
                    avg_cost=float(pos.get('avgCost', 0)),
                    unrealized_pnl=float(pos.get('unrealizedPnl', 0)),
                    realized_pnl=float(pos.get('realizedPnl', 0)),
                    account_id=account_id
                ))
            
            return positions
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return None
    
    def search_contract(self, symbol: str) -> Optional[List[Dict]]:
        """
        Search for contracts by symbol
        
        Args:
            symbol: Symbol to search (e.g., "EUR", "GC", "AAPL")
            
        Returns:
            List of matching contracts
        """
        try:
            response = self.session.get(
                f"{self.base_url}/v1/api/iserver/secdef/search",
                params={'symbol': symbol},
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error searching contract {symbol}: {e}")
            return None
    
    def get_contract_details(self, conid: int) -> Optional[Dict]:
        """Get contract details by contract ID"""
        try:
            response = self.session.get(
                f"{self.base_url}/v1/api/iserver/contract/{conid}/info",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting contract details for {conid}: {e}")
            return None
    
    def get_market_data(
        self,
        conids: List[int],
        fields: Optional[List[int]] = None
    ) -> Optional[Dict]:
        """
        Get real-time market data
        
        Args:
            conids: List of contract IDs
            fields: Market data fields (default: [31, 84, 85, 86, 88])
                    31=Last Price, 84=Bid, 85=Ask, 86=Volume, 88=Change
        
        Returns:
            Dictionary with market data
        """
        try:
            if fields is None:
                fields = [31, 84, 85, 86, 88]
            
            params = {
                'conids': ','.join(map(str, conids)),
                'fields': ','.join(map(str, fields))
            }
            
            response = self.session.get(
                f"{self.base_url}/v1/api/iserver/marketdata/snapshot",
                params=params,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return None
    
    def get_historical_data(
        self,
        conid: int,
        period: str = "1d",
        bar: str = "5min"
    ) -> Optional[Dict]:
        """
        Get historical market data
        
        Args:
            conid: Contract ID
            period: Time period ("1d", "1w", "1m", "1y")
            bar: Bar size ("1min", "5min", "1h", "1d")
            
        Returns:
            Dictionary with historical bars
        """
        try:
            params = {
                'conid': conid,
                'period': period,
                'bar': bar
            }
            
            response = self.session.get(
                f"{self.base_url}/v1/api/iserver/marketdata/history",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return None
    
    def place_order(
        self,
        account_id: str,
        conid: int,
        order_type: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        tif: str = "DAY"
    ) -> Optional[Dict]:
        """
        Place an order
        
        Args:
            account_id: Account ID
            conid: Contract ID
            order_type: "MKT", "LMT", "STP", "STP_LIMIT"
            side: "BUY" or "SELL"
            quantity: Order quantity
            price: Limit/stop price (for limit/stop orders)
            tif: Time in force ("DAY", "GTC", "IOC")
            
        Returns:
            Order confirmation dictionary
        """
        try:
            order = {
                'acctId': account_id,
                'conid': conid,
                'orderType': order_type,
                'side': side,
                'quantity': quantity,
                'tif': tif
            }
            
            if price is not None:
                order['price'] = price
            
            # Place order
            response = self.session.post(
                f"{self.base_url}/v1/api/iserver/account/{account_id}/orders",
                json={'orders': [order]},
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Order placed: {side} {quantity} contracts")
            
            # Handle order confirmation (may require second confirmation)
            if isinstance(result, list) and len(result) > 0:
                order_result = result[0]
                if 'id' in order_result:
                    # Confirm the order
                    confirm_response = self.session.post(
                        f"{self.base_url}/v1/api/iserver/reply/{order_result['id']}",
                        json={'confirmed': True},
                        timeout=5
                    )
                    confirm_response.raise_for_status()
                    return confirm_response.json()
            
            return result
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def modify_order(
        self,
        account_id: str,
        order_id: str,
        quantity: Optional[float] = None,
        price: Optional[float] = None
    ) -> Optional[Dict]:
        """Modify an existing order"""
        try:
            data = {}
            if quantity is not None:
                data['quantity'] = quantity
            if price is not None:
                data['price'] = price
            
            response = self.session.post(
                f"{self.base_url}/v1/api/iserver/account/{account_id}/order/{order_id}",
                json=data,
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"Order {order_id} modified")
            return response.json()
        except Exception as e:
            logger.error(f"Error modifying order: {e}")
            return None
    
    def cancel_order(self, account_id: str, order_id: str) -> bool:
        """Cancel an order"""
        try:
            response = self.session.delete(
                f"{self.base_url}/v1/api/iserver/account/{account_id}/order/{order_id}",
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"Order {order_id} cancelled")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    def get_live_orders(self) -> Optional[List[Dict]]:
        """Get all live orders"""
        try:
            response = self.session.get(
                f"{self.base_url}/v1/api/iserver/account/orders",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting live orders: {e}")
            return None
    
    def get_trades(self) -> Optional[List[Dict]]:
        """Get recent trades"""
        try:
            response = self.session.get(
                f"{self.base_url}/v1/api/iserver/account/trades",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting trades: {e}")
            return None
    
    def logout(self) -> bool:
        """Logout from IBKR Gateway"""
        try:
            response = self.session.post(
                f"{self.base_url}/v1/api/logout",
                timeout=5
            )
            response.raise_for_status()
            logger.info("Logged out from IBKR")
            return True
        except Exception as e:
            logger.error(f"Error logging out: {e}")
            return False


def quick_connect_ibkr(base_url: str = "https://localhost:5000") -> Optional[IBKRConnector]:
    """Quick connect helper for IBKR"""
    try:
        connector = IBKRConnector(base_url)
        if connector.is_authenticated():
            accounts = connector.get_accounts()
            logger.info(f"IBKR connected: {len(accounts) if accounts else 0} accounts")
            return connector
        else:
            logger.warning("IBKR Gateway not authenticated. Make sure Gateway is running.")
            return None
    except Exception as e:
        logger.error(f"Quick connect failed: {e}")
        return None
