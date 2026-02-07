"""
Polymarket API Client
====================
Synchronous client for Polymarket API interaction (MansaCap)
Handles authentication and user portfolio/balance retrieval
"""

import requests
from typing import Dict, List, Optional
import os


class PolymarketAPIClient:
    """Client for Polymarket API interactions"""
    
    BASE_URL = "https://api.polymarket.com"
    CLOB_BASE_URL = "https://clob.polymarket.com"
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        """Initialize Polymarket API client
        
        Args:
            api_key: Polymarket API key
            secret_key: Polymarket secret key
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.session = requests.Session()
        self.authenticated = False
        
        if api_key and secret_key:
            # Set up authentication headers
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}",
                "X-Secret-Key": secret_key,
                "Content-Type": "application/json"
            })
            self.authenticated = True
    
    def get_active_markets(self, limit: int = 50) -> List[Dict]:
        """Fetch active Polymarket markets
        
        Args:
            limit: Maximum number of markets to return
            
        Returns:
            List of active markets
        """
        if not self.authenticated:
            print("❌ Polymarket client not authenticated")
            return []
        
        try:
            url = f"{self.BASE_URL}/events?limit={limit}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Normalize response
            markets = []
            if isinstance(data, list):
                markets = data
            elif isinstance(data, dict) and "events" in data:
                markets = data.get("events", [])
            elif isinstance(data, dict) and "data" in data:
                markets = data.get("data", [])
            
            print(f"✅ Fetched {len(markets)} active Polymarket markets")
            return markets
        except requests.RequestException as e:
            print(f"❌ Error fetching Polymarket markets: {e}")
            return []
    
    def get_user_portfolio(self) -> List[Dict]:
        """Get user's Polymarket portfolio positions
        
        Returns:
            List of user positions
        """
        if not self.authenticated:
            print("❌ Polymarket client not authenticated")
            return []
        
        try:
            url = f"{self.BASE_URL}/user/positions"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Normalize response
            positions = []
            if isinstance(data, list):
                positions = data
            elif isinstance(data, dict) and "positions" in data:
                positions = data.get("positions", [])
            elif isinstance(data, dict) and "portfolio" in data:
                positions = data.get("portfolio", [])
            
            print(f"✅ Found {len(positions)} Polymarket positions")
            return positions
        except requests.RequestException as e:
            print(f"❌ Error fetching Polymarket positions: {e}")
            return []
    
    def get_user_balance(self) -> Optional[Dict]:
        """Get user's Polymarket account balance
        
        Returns:
            Balance information or None
        """
        if not self.authenticated:
            print("❌ Polymarket client not authenticated")
            return None
        
        try:
            url = f"{self.BASE_URL}/user/balance"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Handle response format
            if isinstance(data, dict):
                balance_info = data if "balance" in data or "cash" in data else data
                print(f"✅ Balance retrieved: {balance_info}")
                return balance_info
            
            return None
        except requests.RequestException as e:
            print(f"❌ Error fetching Polymarket balance: {e}")
            return None
    
    def get_user_trades(self, limit: int = 50) -> List[Dict]:
        """Get user's Polymarket trade history
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of trades
        """
        if not self.authenticated:
            print("❌ Polymarket client not authenticated")
            return []
        
        try:
            url = f"{self.BASE_URL}/user/trades?limit={limit}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Normalize response
            trades = []
            if isinstance(data, list):
                trades = data
            elif isinstance(data, dict) and "trades" in data:
                trades = data.get("trades", [])
            elif isinstance(data, dict) and "data" in data:
                trades = data.get("data", [])
            
            print(f"✅ Retrieved {len(trades)} Polymarket trades")
            return trades
        except requests.RequestException as e:
            print(f"❌ Error fetching Polymarket trades: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test API connection
        
        Returns:
            True if connection successful
        """
        try:
            url = f"{self.BASE_URL}/events?limit=1"
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
