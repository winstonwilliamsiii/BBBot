"""
Alpaca Markets API Connector
Complete integration for stocks, options, and crypto trading

Features:
- Account management
- Real-time market data
- Stock/crypto trading
- Position management
- Order management
- Paper trading support
"""

import requests
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AlpacaAccount:
    """Alpaca account credentials"""
    api_key: str
    secret_key: str
    paper: bool = True  # Paper trading by default


@dataclass
class AlpacaPosition:
    """Represents a position"""
    symbol: str
    qty: float
    side: str
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    current_price: float
    avg_entry_price: float


class AlpacaConnector:
    """
    Alpaca Markets API Client
    
    Usage:
        alpaca = AlpacaConnector(api_key="YOUR_KEY", secret_key="YOUR_SECRET", paper=True)
        account = alpaca.get_account()
        print(f"Buying Power: ${account['buying_power']}")
    """
    
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        """
        Initialize Alpaca connector
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Use paper trading (True) or live trading (False)
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        
        # Set base URL based on paper/live
        if paper:
            self.base_url = "https://paper-api.alpaca.markets"
            self.data_url = "https://data.alpaca.markets"
        else:
            self.base_url = "https://api.alpaca.markets"
            self.data_url = "https://data.alpaca.markets"
        
        self.session = requests.Session()
        self.session.headers.update({
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': secret_key
        })
        
        logger.info(f"Alpaca connector initialized ({'PAPER' if paper else 'LIVE'} trading)")
    
    def get_account(self) -> Optional[Dict[str, Any]]:
        """
        Get account information
        
        Returns:
            Dictionary with account details (buying_power, cash, portfolio_value, etc.)
        """
        try:
            response = self.session.get(f"{self.base_url}/v2/account", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def get_positions(self) -> Optional[List[AlpacaPosition]]:
        """
        Get all open positions
        
        Returns:
            List of AlpacaPosition objects
        """
        try:
            response = self.session.get(f"{self.base_url}/v2/positions", timeout=5)
            response.raise_for_status()
            
            data = response.json()
            positions = []
            
            for pos in data:
                positions.append(AlpacaPosition(
                    symbol=pos['symbol'],
                    qty=float(pos['qty']),
                    side=pos['side'],
                    market_value=float(pos['market_value']),
                    cost_basis=float(pos['cost_basis']),
                    unrealized_pl=float(pos['unrealized_pl']),
                    unrealized_plpc=float(pos['unrealized_plpc']),
                    current_price=float(pos['current_price']),
                    avg_entry_price=float(pos['avg_entry_price'])
                ))
            
            return positions
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return None
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get specific position"""
        try:
            response = self.session.get(f"{self.base_url}/v2/positions/{symbol}", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting position for {symbol}: {e}")
            return None
    
    def close_position(self, symbol: str) -> bool:
        """Close a position"""
        try:
            response = self.session.delete(f"{self.base_url}/v2/positions/{symbol}", timeout=5)
            response.raise_for_status()
            logger.info(f"Position {symbol} closed successfully")
            return True
        except Exception as e:
            logger.error(f"Error closing position {symbol}: {e}")
            return False
    
    def close_all_positions(self) -> bool:
        """Close all positions"""
        try:
            response = self.session.delete(f"{self.base_url}/v2/positions", timeout=5)
            response.raise_for_status()
            logger.info("All positions closed")
            return True
        except Exception as e:
            logger.error(f"Error closing all positions: {e}")
            return False
    
    def place_order(
        self,
        symbol: str,
        qty: Optional[float] = None,
        notional: Optional[float] = None,
        side: str = "buy",
        order_type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        extended_hours: bool = False
    ) -> Optional[Dict]:
        """
        Place an order
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            qty: Number of shares (use qty OR notional, not both)
            notional: Dollar amount to trade (fractional shares)
            side: "buy" or "sell"
            order_type: "market", "limit", "stop", "stop_limit"
            time_in_force: "day", "gtc", "ioc", "fok"
            limit_price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            extended_hours: Allow extended hours trading
            
        Returns:
            Dictionary with order details
        """
        try:
            data = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'time_in_force': time_in_force,
                'extended_hours': extended_hours
            }
            
            if qty is not None:
                data['qty'] = qty
            elif notional is not None:
                data['notional'] = notional
            else:
                raise ValueError("Must specify either qty or notional")
            
            if limit_price is not None:
                data['limit_price'] = limit_price
            if stop_price is not None:
                data['stop_price'] = stop_price
            
            response = self.session.post(f"{self.base_url}/v2/orders", json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Order placed: {symbol} {side} {qty or notional}")
            return result
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def get_orders(self, status: str = "open") -> Optional[List[Dict]]:
        """
        Get orders
        
        Args:
            status: "open", "closed", "all"
            
        Returns:
            List of order dictionaries
        """
        try:
            params = {'status': status, 'limit': 500}
            response = self.session.get(f"{self.base_url}/v2/orders", params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            response = self.session.delete(f"{self.base_url}/v2/orders/{order_id}", timeout=5)
            response.raise_for_status()
            logger.info(f"Order {order_id} cancelled")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    def cancel_all_orders(self) -> bool:
        """Cancel all open orders"""
        try:
            response = self.session.delete(f"{self.base_url}/v2/orders", timeout=5)
            response.raise_for_status()
            logger.info("All orders cancelled")
            return True
        except Exception as e:
            logger.error(f"Error cancelling all orders: {e}")
            return False
    
    def get_bars(
        self,
        symbol: str,
        timeframe: str = "1Day",
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100
    ) -> Optional[Dict]:
        """
        Get historical bars (OHLCV data)
        
        Args:
            symbol: Stock symbol
            timeframe: "1Min", "5Min", "15Min", "1Hour", "1Day"
            start: Start date (ISO format)
            end: End date (ISO format)
            limit: Number of bars
            
        Returns:
            Dictionary with bar data
        """
        try:
            params = {
                'timeframe': timeframe,
                'limit': limit
            }
            if start:
                params['start'] = start
            if end:
                params['end'] = end
            
            response = self.session.get(
                f"{self.data_url}/v2/stocks/{symbol}/bars",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting bars for {symbol}: {e}")
            return None
    
    def get_latest_quote(self, symbol: str) -> Optional[Dict]:
        """Get latest quote (bid/ask)"""
        try:
            response = self.session.get(
                f"{self.data_url}/v2/stocks/{symbol}/quotes/latest",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return None
    
    def get_latest_trade(self, symbol: str) -> Optional[Dict]:
        """Get latest trade"""
        try:
            response = self.session.get(
                f"{self.data_url}/v2/stocks/{symbol}/trades/latest",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting trade for {symbol}: {e}")
            return None
    
    def get_portfolio_history(
        self,
        period: str = "1M",
        timeframe: str = "1D"
    ) -> Optional[Dict]:
        """
        Get portfolio history
        
        Args:
            period: "1D", "1W", "1M", "3M", "1Y", "all"
            timeframe: "1Min", "5Min", "15Min", "1H", "1D"
            
        Returns:
            Dictionary with portfolio history
        """
        try:
            params = {'period': period, 'timeframe': timeframe}
            response = self.session.get(
                f"{self.base_url}/v2/account/portfolio/history",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting portfolio history: {e}")
            return None
    
    def get_clock(self) -> Optional[Dict]:
        """Get market clock (open/closed status)"""
        try:
            response = self.session.get(f"{self.base_url}/v2/clock", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting clock: {e}")
            return None
    
    def get_calendar(self, start: Optional[str] = None, end: Optional[str] = None) -> Optional[List[Dict]]:
        """Get market calendar"""
        try:
            params = {}
            if start:
                params['start'] = start
            if end:
                params['end'] = end
            
            response = self.session.get(f"{self.base_url}/v2/calendar", params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting calendar: {e}")
            return None
    
    def get_asset(self, symbol: str) -> Optional[Dict]:
        """Get asset information"""
        try:
            response = self.session.get(f"{self.base_url}/v2/assets/{symbol}", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting asset {symbol}: {e}")
            return None


def quick_connect_alpaca(api_key: str, secret_key: str, paper: bool = True) -> Optional[AlpacaConnector]:
    """Quick connect helper for Alpaca"""
    try:
        connector = AlpacaConnector(api_key, secret_key, paper)
        # Test connection
        account = connector.get_account()
        if account:
            logger.info(f"Alpaca connected: ${account.get('portfolio_value', 0):,.2f} portfolio value")
            return connector
        return None
    except Exception as e:
        logger.error(f"Quick connect failed: {e}")
        return None
