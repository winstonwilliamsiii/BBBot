"""
MetaTrader 5 REST API Connector
Simple REST API connection to MT5 backend for trading operations

Capabilities:
- Login to MT5 account
- Get account information
- Fetch market data
- Place trades
- Manage positions
- Real-time webhook events
"""

import requests
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from datetime import datetime
import logging
import os
import time

logger = logging.getLogger(__name__)


def _sanitize_error_text(value: str) -> str:
    sanitized = value
    for token in ("password=", "user="):
        if token in sanitized:
            prefix, _, remainder = sanitized.partition(token)
            remainder = remainder.split("&", 1)[-1] if "&" in remainder else ""
            sanitized = prefix + token.rstrip("=") + "=<redacted>"
            if remainder:
                sanitized += "&" + remainder
    return sanitized


@dataclass
class MT5Account:
    """MT5 Account credentials and connection info"""
    user: str
    password: str
    host: str
    port: int = 443
    

@dataclass
class MT5Position:
    """Represents an open position in MT5"""
    ticket: int
    symbol: str
    type: str  # 'BUY' or 'SELL'
    volume: float
    open_price: float
    current_price: float
    profit: float
    open_time: datetime
    

class MT5Connector:
    """
    MetaTrader 5 REST API Client
    
    Usage:
        connector = MT5Connector(base_url="http://your-mt5-server.com")
        if connector.connect(user="123456", password="password", host="broker.com", port=443):
            account_info = connector.get_account_info()
            print(f"Balance: {account_info['balance']}")
    """
    
    def __init__(self, base_url: str):
        """
        Initialize MT5 connector
        
        Args:
            base_url: Base URL of your MT5 REST API server (e.g., "http://localhost:8000")
        """
        self.base_url = base_url.rstrip('/')
        self.connected = False
        self.session = requests.Session()
        self.account: Optional[MT5Account] = None
        self.last_connect_error: str = ""
        self.request_timeout = float(os.getenv("MT5_REQUEST_TIMEOUT", "10"))
        self.connect_retries = int(os.getenv("MT5_CONNECT_RETRIES", "3"))
        self.connect_retry_delay = float(
            os.getenv("MT5_CONNECT_RETRY_DELAY", "1.0")
        )

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Execute HTTP request with retry for transient network failures."""
        timeout = kwargs.pop('timeout', self.request_timeout)
        last_error = None

        for attempt in range(1, self.connect_retries + 1):
            try:
                return self.session.request(
                    method,
                    url,
                    timeout=timeout,
                    **kwargs,
                )
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ) as exc:
                last_error = exc
                if attempt >= self.connect_retries:
                    break

                sleep_seconds = self.connect_retry_delay * attempt
                logger.warning(
                    f"Transient MT5 network error (attempt "
                    f"{attempt}/{self.connect_retries}): {exc}. "
                    f"Retrying in {sleep_seconds:.1f}s"
                )
                time.sleep(sleep_seconds)

        raise last_error if last_error else RuntimeError("Unknown network error")

    def _request_with_fallback(self, method: str, paths: List[str], **kwargs) -> requests.Response:
        """Try multiple endpoint paths and return the first non-404 response."""
        last_response = None
        last_error = None

        for path in paths:
            url = f"{self.base_url}{path}"
            try:
                response = self._request(method, url, **kwargs)
                if response.status_code == 404:
                    last_response = response
                    continue
                return response
            except requests.exceptions.RequestException as exc:
                last_error = exc

        if last_response is not None:
            return last_response
        if last_error is not None:
            raise last_error
        raise RuntimeError("No endpoints provided")
        
    def connect(self, user: str, password: str, host: str, port: int = 443) -> bool:
        """
        Connect to MT5 account via REST API
        
        Args:
            user: MT5 account number
            password: MT5 account password
            host: Broker server hostname
            port: Connection port (default: 443)
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.last_connect_error = ""
            params = {
                'user': user,
                'password': password,
                'host': host,
                'port': port,
            }
            
            logger.info(f"Connecting to MT5 on {host}:{port}")
            # Prefer the JSON login endpoint so credentials stay out of URLs.
            response = self._request_with_fallback(
                'POST',
                ['/connect'],
                json=params,
                timeout=10,
            )
            if response.status_code == 404:
                response = self._request_with_fallback(
                    'GET',
                    ['/Connect'],
                    params=params,
                    timeout=10,
                )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success') or result.get('connected'):
                self.connected = True
                self.account = MT5Account(user=user, password=password, host=host, port=port)
                logger.info("Successfully connected to MT5")
                return True
            else:
                self.last_connect_error = str(result.get('error', 'Unknown error'))
                logger.error(f"MT5 connection failed: {self.last_connect_error}")
                return False
                
        except requests.exceptions.HTTPError as e:
            detail = ""
            try:
                payload = e.response.json() if e.response is not None else {}
                detail = str(payload.get('error') or payload)
            except Exception:
                detail = (e.response.text[:300] if e.response is not None else "")

            self.last_connect_error = _sanitize_error_text(detail or "HTTP error from MT5 bridge")
            status_code = e.response.status_code if e.response is not None else "unknown"
            logger.error(
                f"Connection error from MT5 bridge (status {status_code}): {self.last_connect_error}"
            )
            return False
        except requests.exceptions.RequestException as e:
            self.last_connect_error = f"Network error reaching MT5 bridge: {type(e).__name__}"
            logger.error(self.last_connect_error)
            return False
        except Exception as e:
            self.last_connect_error = f"Unexpected MT5 connection error: {type(e).__name__}"
            logger.error(self.last_connect_error)
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from MT5 account"""
        try:
            response = self._request_with_fallback('GET', ['/Disconnect'], timeout=5)
            if response.status_code == 404:
                response = self._request_with_fallback('POST', ['/disconnect'], timeout=5)
            response.raise_for_status()
            
            self.connected = False
            self.account = None
            logger.info("Disconnected from MT5")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return False
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get MT5 account information
        
        Returns:
            Dictionary with account details (balance, equity, margin, etc.)
        """
        if not self.connected:
            logger.error("Not connected to MT5. Call connect() first.")
            return None
            
        try:
            response = self._request_with_fallback('GET', ['/AccountInfo', '/account'], timeout=5)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def get_positions(self) -> Optional[List[MT5Position]]:
        """
        Get all open positions
        
        Returns:
            List of MT5Position objects
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return None
            
        try:
            response = self._request_with_fallback('GET', ['/Positions', '/positions'], timeout=5)
            response.raise_for_status()
            
            data = response.json()
            positions = []
            
            for pos in data.get('positions', []):
                positions.append(MT5Position(
                    ticket=pos.get('ticket'),
                    symbol=pos.get('symbol'),
                    type=pos.get('type'),
                    volume=pos.get('volume'),
                    open_price=pos.get('open_price'),
                    current_price=pos.get('current_price'),
                    profit=pos.get('profit'),
                    open_time=datetime.fromisoformat(pos.get('open_time', ''))
                ))
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return None
    
    def get_market_data(self, symbol: str, timeframe: str = "H1", count: int = 100) -> Optional[Dict]:
        """
        Get market data (OHLCV) for a symbol
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD", "BTCUSD")
            timeframe: Timeframe (M1, M5, M15, M30, H1, H4, D1, W1, MN1)
            count: Number of bars to fetch
            
        Returns:
            Dictionary with OHLCV data
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return None
            
        try:
            params = {
                'symbol': symbol,
                'timeframe': timeframe,
                'count': count
            }
            
            response = self._request_with_fallback(
                'GET',
                ['/MarketData', '/market-data'],
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return None
    
    def place_trade(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: str = ""
    ) -> Optional[Dict]:
        """
        Place a trade order
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            order_type: Order type ("BUY", "SELL", "BUY_LIMIT", "SELL_LIMIT", etc.)
            volume: Trade volume in lots
            price: Entry price (for pending orders)
            sl: Stop loss price
            tp: Take profit price
            comment: Order comment
            
        Returns:
            Dictionary with order result (ticket, status, etc.)
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return None
            
        try:
            data = {
                'symbol': symbol,
                'type': order_type,
                'volume': volume,
                'comment': comment,
            }
            
            if price is not None:
                data['price'] = price
            if sl is not None:
                data['sl'] = sl
            if tp is not None:
                data['tp'] = tp
            
            response = self._request_with_fallback('POST', ['/PlaceTrade'], json=data, timeout=10)
            if response.status_code == 404:
                bridge_payload = {
                    'symbol': symbol,
                    'action': order_type,
                    'volume': volume,
                    'comment': comment,
                }
                if price is not None:
                    bridge_payload['price'] = price
                if sl is not None:
                    bridge_payload['stop_loss'] = sl
                if tp is not None:
                    bridge_payload['take_profit'] = tp
                response = self._request_with_fallback('POST', ['/trade'], json=bridge_payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Trade placed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error placing trade: {e}")
            return None
    
    def close_position(self, ticket: int) -> bool:
        """
        Close an open position
        
        Args:
            ticket: Position ticket number
            
        Returns:
            True if closed successfully, False otherwise
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return False
            
        try:
            data = {'ticket': ticket}
            response = self._request_with_fallback('POST', ['/ClosePosition'], json=data, timeout=5)
            response.raise_for_status()
            
            result = response.json()
            success = result.get('success', False)
            
            if success:
                logger.info(f"Position {ticket} closed successfully")
            else:
                logger.error(f"Failed to close position {ticket}: {result.get('error')}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False
    
    def modify_position(
        self,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> bool:
        """
        Modify stop loss and/or take profit of an open position
        
        Args:
            ticket: Position ticket number
            sl: New stop loss price
            tp: New take profit price
            
        Returns:
            True if modified successfully, False otherwise
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return False
            
        try:
            data = {'ticket': ticket}
            if sl is not None:
                data['sl'] = sl
            if tp is not None:
                data['tp'] = tp

            response = self._request_with_fallback('POST', ['/ModifyPosition', '/modify'], json=data, timeout=5)
            response.raise_for_status()
            
            result = response.json()
            success = result.get('success', False)
            
            if success:
                logger.info(f"Position {ticket} modified successfully")
            else:
                logger.error(f"Failed to modify position {ticket}: {result.get('error')}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error modifying position: {e}")
            return False
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Get detailed symbol information
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with symbol details (bid, ask, spread, etc.)
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return None
            
        try:
            params = {'symbol': symbol}

            response = self._request_with_fallback('GET', ['/SymbolInfo', f'/symbol/{symbol}'], params=params, timeout=5)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None
    
    def setup_webhook(self, webhook_url: str, events: List[str]) -> bool:
        """
        Setup webhook for real-time events
        
        Args:
            webhook_url: URL to receive webhook notifications
            events: List of events to subscribe to (e.g., ['trade', 'position', 'account'])
            
        Returns:
            True if webhook setup successfully, False otherwise
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return False
            
        try:
            endpoint = f"{self.base_url}/SetupWebhook"
            data = {
                'webhook_url': webhook_url,
                'events': events
            }
            
            response = self._request(
                'POST',
                endpoint,
                json=data,
                timeout=5,
            )
            response.raise_for_status()
            
            result = response.json()
            success = result.get('success', False)
            
            if success:
                logger.info(f"Webhook setup successfully for events: {events}")
            else:
                logger.error(f"Failed to setup webhook: {result.get('error')}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error setting up webhook: {e}")
            return False
    
    def health_check(self) -> bool:
        """
        Check if MT5 REST API server is reachable
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = self._request_with_fallback('GET', ['/Health', '/health'], timeout=3)
            response.raise_for_status()
            
            result = response.json()
            status = str(result.get('status', '')).lower()
            mt5_initialized = result.get('mt5_initialized', True)
            return status in {'healthy', 'ok'} and mt5_initialized
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Convenience functions for quick usage
def quick_connect(base_url: str, user: str, password: str, host: str, port: int = 443) -> Optional[MT5Connector]:
    """
    Quick connect to MT5 - returns connected connector or None
    
    Example:
        mt5 = quick_connect(
            base_url="http://localhost:8000",
            user="123456",
            password="password",
            host="broker.com"
        )
        if mt5:
            print(mt5.get_account_info())
    """
    connector = MT5Connector(base_url)
    if connector.connect(user, password, host, port):
        return connector
    return None
