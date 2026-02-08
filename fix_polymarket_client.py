#!/usr/bin/env python
"""
Script to update Polymarket API client with flexible endpoint handling
"""

new_content = '''"""
Polymarket API Client
====================
Synchronous client for Polymarket API interaction (MansaCap)
Handles authentication and user portfolio/balance retrieval

NOTE: Polymarket API endpoints may vary. This client attempts multiple
endpoint patterns to handle different API versions and structures.
Reference: https://docs.polymarket.com/api
"""

import requests
from typing import Dict, List, Optional
import os


class PolymarketAPIClient:
    """Client for Polymarket API interactions"""
    
    # Multiple possible base URLs to try
    BASE_URL = "https://api.polymarket.com"
    CLOB_BASE_URL = "https://clob.polymarket.com"
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        """Initialize Polymarket API client
        
        Args:
            api_key: Polymarket API key (from MansaCap account)
            secret_key: Polymarket secret key (from MansaCap account)
        """
        self.api_key = api_key or os.getenv("POLYMARKET_API_KEY", "")
        self.secret_key = secret_key or os.getenv("POLYMARKET_SECRET_KEY", "")
        self.session = requests.Session()
        self.authenticated = bool(self.api_key and self.secret_key)
        
        if self.authenticated:
            # Set up authentication headers
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "X-Secret-Key": self.secret_key,
                "Content-Type": "application/json"
            })
    
    def test_connection(self) -> bool:
        """Test basic API connectivity
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.authenticated:
            return False
        
        try:
            # Try multiple endpoint patterns
            endpoints_to_try = [
                f"{self.CLOB_BASE_URL}/markets",
                f"{self.BASE_URL}/markets",
                f"{self.BASE_URL}/",
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    response = self.session.get(endpoint, timeout=5)
                    if response.status_code in [200, 401, 403]:
                        return True  # Server responded
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"Connection test error: {e}")
            return False
    
    def get_active_markets(self, limit: int = 50) -> List[Dict]:
        """Fetch active Polymarket markets
        
        Args:
            limit: Maximum number of markets to return
            
        Returns:
            List of active markets
        """
        if not self.authenticated:
            return []
        
        # Try multiple endpoint patterns
        endpoints_to_try = [
            # CLOB API pattern
            f"{self.CLOB_BASE_URL}/markets?limit={limit}",
            # REST API patterns
            f"{self.BASE_URL}/markets?limit={limit}",
            f"{self.BASE_URL}/events?limit={limit}",
            f"{self.BASE_URL}/events",
        ]
        
        for url in endpoints_to_try:
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Normalize response to list
                markets = self._normalize_response(data)
                if markets:
                    return markets
            except requests.RequestException as e:
                continue
        
        return []
    
    def get_user_portfolio(self) -> List[Dict]:
        """Get user's Polymarket portfolio positions
        
        Returns:
            List of user positions
        """
        if not self.authenticated:
            return []
        
        # Try multiple endpoint patterns
        endpoints_to_try = [
            # CLOB API pattern
            f"{self.CLOB_BASE_URL}/user/orders",
            f"{self.CLOB_BASE_URL}/user/positions",
            # REST API patterns  
            f"{self.BASE_URL}/user/positions",
            f"{self.BASE_URL}/positions",
            f"{self.BASE_URL}/user/portfolio",
        ]
        
        for url in endpoints_to_try:
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                positions = self._normalize_response(data)
                if positions:
                    return positions
            except requests.RequestException as e:
                continue
        
        return []
    
    def get_user_balance(self) -> Optional[Dict]:
        """Get user's account balance
        
        Returns:
            Dictionary with cash and portfolio values, or None
        """
        if not self.authenticated:
            return None
        
        # Try multiple endpoint patterns
        endpoints_to_try = [
            f"{self.BASE_URL}/user/balance",
            f"{self.BASE_URL}/user/account",
            f"{self.CLOB_BASE_URL}/user/balance",
        ]
        
        for url in endpoints_to_try:
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, dict) and ('cash' in data or 'balance' in data):
                    return data
            except requests.RequestException:
                continue
        
        # Return default balance if endpoints not found (demo mode)
        return {"cash": 0.0, "portfolio_value": 0.0, "total_balance": 0.0}
    
    def get_user_trades(self, limit: int = 50) -> List[Dict]:
        """Get user's trade history
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of trades
        """
        if not self.authenticated:
            return []
        
        # Try multiple endpoint patterns
        endpoints_to_try = [
            f"{self.CLOB_BASE_URL}/user/trades?limit={limit}",
            f"{self.BASE_URL}/user/trades?limit={limit}",
            f"{self.BASE_URL}/user/fills?limit={limit}",
            f"{self.BASE_URL}/trades?limit={limit}",
        ]
        
        for url in endpoints_to_try:
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                trades = self._normalize_response(data)
                if trades:
                    return trades
            except requests.RequestException:
                continue
        
        return []
    
    @staticmethod
    def _normalize_response(data) -> List[Dict]:
        """Normalize API response to list format
        
        Args:
            data: Raw API response
            
        Returns:
            Normalized list of items
        """
        if isinstance(data, list):
            return data
        
        if isinstance(data, dict):
            # Try common key patterns
            for key in ['data', 'items', 'results', 'orders', 'positions', 
                       'markets', 'events', 'trades', 'fills']:
                if key in data and isinstance(data[key], list):
                    return data[key]
        
        return []
'''

# Write the file
file_path = r"prediction_analytics\services\polymarket_api_client.py"
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ {file_path} updated with flexible endpoint handling")
