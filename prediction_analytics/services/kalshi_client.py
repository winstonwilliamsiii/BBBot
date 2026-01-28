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
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Kalshi client
        
        Args:
            api_key: Optional API key for authenticated requests
        """
        self.api_key = api_key
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
