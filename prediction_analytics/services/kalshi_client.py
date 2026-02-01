"""
Kalshi API Client
=================
Handles interaction with Kalshi prediction market API using official SDK v3+
"""

from kalshi_python_sync import KalshiClient as KalshiSDK, KalshiAuth, Configuration
from typing import Dict, List, Optional
import streamlit as st


class KalshiClient:
    """Client for Kalshi API interactions using official SDK v3+"""
    
    def __init__(self, api_key: Optional[str] = None, private_key: Optional[str] = None):
        """Initialize Kalshi client with API key authentication
        
        Args:
            api_key: Kalshi API key ID (ACCESS_KEY)
            private_key: RSA private key in PEM format (PRIVATE_KEY) - can be with or without headers
        """
        self.client = None
        self.api_key = api_key
        self.authenticated = False
        self.last_error: Optional[str] = None
        
        if api_key and private_key:
            try:
                # Format private key as proper PEM if it's not already
                if not private_key.startswith('-----BEGIN'):
                    # Add PEM headers and format with newlines (64 chars per line)
                    key_body = private_key.strip()
                    formatted_key = "-----BEGIN RSA PRIVATE KEY-----\n"
                    # Split into 64-character lines
                    for i in range(0, len(key_body), 64):
                        formatted_key += key_body[i:i+64] + "\n"
                    formatted_key += "-----END RSA PRIVATE KEY-----"
                    private_key = formatted_key
                
                # Official Kalshi SDK v3+ uses API key authentication
                # API endpoint: https://api.elections.kalshi.com
                auth = KalshiAuth(key_id=api_key, private_key_pem=private_key)
                config = Configuration(host='https://api.elections.kalshi.com')
                self.client = KalshiSDK(auth=auth, configuration=config)
                self.authenticated = True
                self.last_error = None
                print("✅ Kalshi SDK v3+ authenticated successfully")
            except Exception as e:
                self.last_error = str(e)
                print(f"❌ Kalshi authentication failed: {e}")
                self.client = None
        else:
            self.last_error = "Missing Kalshi API key or private key"

    @staticmethod
    def _normalize_list(data: object, keys: List[str]) -> List[Dict]:
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in keys:
                value = data.get(key)
                if isinstance(value, list):
                    return value
        return []
    
    def get_active_markets(self) -> List[Dict]:
        """Fetch active prediction markets
        
        Returns:
            List of active market contracts
        """
        if not self.client:
            print("❌ Kalshi client not authenticated")
            return []
        
        try:
            response = self.client.market_api.get_markets()
            markets = response.markets if hasattr(response, 'markets') else []
            print(f"✅ Fetched {len(markets)} active markets")
            return [market.to_dict() if hasattr(market, 'to_dict') else market for market in markets]
        except Exception as e:
            print(f"❌ Error fetching markets: {e}")
            return []
    
    def get_market_details(self, market_ticker: str) -> Optional[Dict]:
        """Get detailed information for a specific market
        
        Args:
            market_ticker: The market ticker symbol
            
        Returns:
            Market details or None if not found
        """
        if not self.client:
            return None
        
        try:
            response = self.client.market_api.get_market(ticker=market_ticker)
            market = response.market if hasattr(response, 'market') else response
            return market.to_dict() if hasattr(market, 'to_dict') else market
        except Exception as e:
            print(f"❌ Error fetching market {market_ticker}: {e}")
            return None
    
    # Removed methods that don't exist in SDK v3:
    # - get_contract_details (use get_market_details instead)
    # - get_account_history (not available in current SDK)
    # - get_user_profile (not available in current SDK)
    
    def get_user_portfolio(self) -> List[Dict]:
        """Get user's portfolio positions (active holdings)
        
        Returns:
            List of user's active positions
        """
        if not self.client:
            print("❌ Kalshi client not authenticated")
            return []
        
        try:
            response = self.client.portfolio_api.get_positions()
            positions = response.market_positions if hasattr(response, 'market_positions') else []
            print(f"✅ Found {len(positions)} active positions")
            return [pos.to_dict() if hasattr(pos, 'to_dict') else pos for pos in positions]
        except Exception as e:
            print(f"❌ Error fetching portfolio: {e}")
            return []
    
    def get_user_balance(self) -> Optional[Dict]:
        """Get user's account balance and cash available
        
        Returns:
            Balance information with cash/holdings breakdown or None if error
        """
        if not self.client:
            print("❌ Kalshi client not authenticated")
            return None
        
        try:
            response = self.client.portfolio_api.get_balance()
            balance = response.balance if hasattr(response, 'balance') else response
            print(f"✅ Balance retrieved")
            return balance.to_dict() if hasattr(balance, 'to_dict') else balance
        except Exception as e:
            print(f"❌ Error fetching balance: {e}")
            return None
    
    def get_user_trades(self, limit: int = 100) -> List[Dict]:
        """Get user's trade history (fills)
        
        Returns:
            List of executed trades/fills
        """
        if not self.client:
            print("❌ Kalshi client not authenticated")
            return []
        
        try:
            response = self.client.portfolio_api.get_fills(limit=limit)
            fills = response.fills if hasattr(response, 'fills') else []
            print(f"✅ Retrieved {len(fills)} trades from history")
            return [fill.to_dict() if hasattr(fill, 'to_dict') else fill for fill in fills]
        except Exception as e:
            print(f"❌ Error fetching trade history: {e}")
            return []
    
# Removed methods that don't exist in SDK v3:
    # - get_contract_details (use get_market_details instead)
    # - get_account_history (not available in current SDK)
    # - get_user_profile (not available in current SDK)
