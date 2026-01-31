"""
Kalshi API Client
=================
Handles interaction with Kalshi prediction market API
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime


class KalshiClient:
    """Client for Kalshi API interactions"""
    
    BASE_URL = "https://api.kalshi.com"
    
    def __init__(self, api_key: Optional[str] = None, private_key: Optional[str] = None):
        """Initialize Kalshi client
        
        Args:
            api_key: Optional API key for authenticated requests
            private_key: Optional private key for signing requests
        """
        self.api_key = api_key
        self.private_key = private_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def get_active_markets(self) -> List[Dict]:
        """Fetch active prediction markets
        
        Returns:
            List of active market contracts
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/markets")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching markets: {e}")
            return []
    
    def get_market_details(self, market_id: str) -> Optional[Dict]:
        """Get detailed information for a specific market
        
        Args:
            market_id: The market contract ID
            
        Returns:
            Market details or None if not found
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/markets/{market_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching market {market_id}: {e}")
            return None
    
    def get_contract_details(self, contract_id: str) -> Optional[Dict]:
        """Get details for a specific contract
        
        Args:
            contract_id: The contract ID
            
        Returns:
            Contract details or None if not found
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/contracts/{contract_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching contract {contract_id}: {e}")
            return None
    
    def get_user_portfolio(self) -> List[Dict]:
        """Get user's portfolio positions (requires authenticated API key)
        
        Returns:
            List of user's active positions
        """
        if not self.api_key:
            print("API key required for portfolio access")
            return []
        
        try:
            # Kalshi API endpoint for portfolio/positions
            response = self.session.get(f"{self.BASE_URL}/portfolio/positions")
            print(f"Kalshi API Status: {response.status_code}")
            print(f"Kalshi API Response: {response.text[:500]}")
            response.raise_for_status()
            data = response.json()
            print(f"Parsed data: {data}")
            return data.get('positions', data.get('portfolio', []))
        except requests.RequestException as e:
            print(f"Error fetching portfolio: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
            return []
    
    def get_user_balance(self) -> Optional[Dict]:
        """Get user's account balance (requires authenticated API key)
        
        Returns:
            Balance information or None if error
        """
        if not self.api_key:
            print("API key required for balance access")
            return None
        
        try:
            response = self.session.get(f"{self.BASE_URL}/portfolio/balance")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching balance: {e}")
            return None
