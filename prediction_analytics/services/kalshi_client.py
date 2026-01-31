"""
Kalshi API Client
=================
Handles interaction with Kalshi prediction market API using official SDK
"""

from kalshi import Session
from typing import Dict, List, Optional
import streamlit as st


class KalshiClient:
    """Client for Kalshi API interactions using official SDK"""
    
    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        """Initialize Kalshi client with official SDK
        
        Args:
            email: Kalshi account email
            password: Kalshi account password
        """
        self.session = None
        self.email = email
        self.password = password
        
        if email and password:
            try:
                # Official Kalshi SDK uses email/password authentication
                # Endpoint: https://api.elections.kalshi.com
                self.session = Session(email=email, password=password, 
                                     endpoint='https://api.elections.kalshi.com/v1')
                print(f"✅ Kalshi SDK authenticated successfully")
            except Exception as e:
                print(f"❌ Kalshi authentication failed: {e}")
                self.session = None
    
    def get_active_markets(self) -> List[Dict]:
        """Fetch active prediction markets
        
        Returns:
            List of active market contracts
        """
        if not self.session:
            print("❌ Kalshi session not authenticated")
            return []
        
        try:
            markets = self.session.get_markets()
            print(f"✅ Fetched {len(markets)} active markets")
            return markets
        except Exception as e:
            print(f"❌ Error fetching markets: {e}")
            return []
    
    def get_market_details(self, market_id: str) -> Optional[Dict]:
        """Get detailed information for a specific market
        
        Args:
            market_id: The market contract ID
            
        Returns:
            Market details or None if not found
        """
        if not self.session:
            return None
        
        try:
            market = self.session.get_market(market_id)
            return market
        except Exception as e:
            print(f"❌ Error fetching market {market_id}: {e}")
            return None
    
    def get_contract_details(self, contract_id: str) -> Optional[Dict]:
        """Get details for a specific contract
        
        Args:
            contract_id: The contract ID
            
        Returns:
            Contract details or None if not found
        """
        if not self.session:
            return None
        
        try:
            contract = self.session.get_contract(contract_id)
            return contract
        except Exception as e:
            print(f"❌ Error fetching contract {contract_id}: {e}")
            return None
    
    def get_user_portfolio(self) -> List[Dict]:
        """Get user's portfolio positions (active holdings)
        
        Returns:
            List of user's active positions
        """
        if not self.session:
            print("❌ Kalshi session not authenticated")
            return []
        
        try:
            # Official SDK method: user_get_market_positions
            positions = self.session.user_get_market_positions()
            print(f"✅ Found {len(positions)} active positions")
            return positions
        except Exception as e:
            print(f"❌ Error fetching portfolio: {e}")
            return []
    
    def get_user_balance(self) -> Optional[Dict]:
        """Get user's account balance and cash available
        
        Endpoint: GET /balance
        
        Returns:
            Balance information with cash/holdings breakdown or None if error
        """
        if not self.session:
            print("❌ Kalshi session not authenticated")
            return None
        
        try:
            # Official SDK method: user_get_balance
            balance = self.session.user_get_balance()
            print(f"✅ Balance retrieved: {balance}")
            return balance
        except Exception as e:
            print(f"❌ Error fetching balance: {e}")
            return None
    
    def get_user_trades(self, limit: int = 100) -> List[Dict]:
        """Get user's trade history (fills)
        
        Endpoint: GET /fills
        
        Returns:
            List of executed trades/fills
        """
        if not self.session:
            print("❌ Kalshi session not authenticated")
            return []
        
        try:
            # Official SDK method: user_trades_get
            trades = self.session.user_trades_get(limit=limit)
            print(f"✅ Retrieved {len(trades)} trades from history")
            return trades if isinstance(trades, list) else trades.get('trades', [])
        except Exception as e:
            print(f"❌ Error fetching trade history: {e}")
            return []
    
    def get_account_history(self) -> List[Dict]:
        """Get user's full account transaction history
        
        Endpoint: GET /account-history
        
        Returns:
            List of all account transactions/activities
        """
        if not self.session:
            print("❌ Kalshi session not authenticated")
            return []
        
        try:
            # Official SDK method: user_get_account_history
            history = self.session.user_get_account_history()
            print(f"✅ Retrieved account history")
            return history if isinstance(history, list) else history.get('history', [])
        except Exception as e:
            print(f"❌ Error fetching account history: {e}")
            return []
