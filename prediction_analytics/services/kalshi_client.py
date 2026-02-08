"""Kalshi API wrapper using official SDK with email/password authentication."""
import os
import logging
from typing import Dict, List, Any, Optional

from kalshi import Session

logger = logging.getLogger(__name__)


class KalshiClient:
    """
    Wrapper around official Kalshi SDK for easier access to prediction market data.
    Uses email/password authentication (official method as of 2024).
    Endpoint: https://api.elections.kalshi.com/v1
    """
    
    def __init__(self, email: str = "", password: str = ""):
        """
        Initialize Kalshi client with email/password authentication.
        
        Args:
            email: Kalshi account email (or KALSHI_EMAIL env var)
            password: Kalshi account password (or KALSHI_PASSWORD env var)
        """
        self.email = email or os.getenv("KALSHI_EMAIL", "")
        self.password = password or os.getenv("KALSHI_PASSWORD", "")
        self.authenticated = False
        self.last_error = None
        self.session = None
        
        # Authenticate on initialization
        if self.email and self.password:
            try:
                self.session = Session(
                    email=self.email,
                    password=self.password,
                    endpoint="https://api.elections.kalshi.com/v1"
                )
                self.authenticated = True
                logger.info(f"✅ Kalshi authenticated: {self.email}")
            except Exception as e:
                self.authenticated = False
                self.last_error = str(e)
                logger.error(f"❌ Kalshi auth failed: {e}")
                self.session = None
        else:
            self.last_error = "Email and password required"
            logger.warning("⚠️ Kalshi credentials not provided")
    
    @staticmethod
    def _normalize_list(response: Any) -> List[Dict]:
        """
        Normalize API response to list format.
        Handles different response structures (list, dict with data key, etc.)
        """
        if response is None:
            return []
        if isinstance(response, list):
            return response
        if isinstance(response, dict):
            # Try common keys for data arrays
            for key in ['data', 'items', 'results', 'markets', 'positions', 'trades']:
                if key in response and isinstance(response[key], list):
                    return response[key]
            # If dict without recognized key, return as single-item list
            return [response]
        return []
    
    def get_user_portfolio(self) -> List[Dict]:
        """Get user's open market positions."""
        if not self.authenticated or not self.session:
            logger.warning("Not authenticated or no session")
            return []
        
        try:
            # Get positions from the API
            raw_response = self.session.user_get_market_positions()
            logger.info(f"📊 Kalshi positions raw response type: {type(raw_response)}")
            logger.info(f"📊 Kalshi positions raw response: {raw_response}")
            
            # If response is empty or None, also try getting fills to see recent activity
            normalized = self._normalize_list(raw_response)
            
            if not normalized:
                logger.info("No positions found, checking recent fills...")
                fills = self.session.user_trades_get(limit=10)
                logger.info(f"📊 Recent fills: {fills}")
            
            return normalized
        except Exception as e:
            logger.error(f"❌ Failed to get portfolio: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def get_user_balance(self) -> Optional[Dict]:
        """Get user's account balance."""
        if not self.authenticated or not self.session:
            return None
        
        try:
            balance = self.session.user_get_balance()
            return balance
        except Exception as e:
            logger.error(f"❌ Failed to get balance: {e}")
            return None
    
    def get_user_trades(self, limit: int = 100) -> List[Dict]:
        """Get user's trade history (fills)."""
        if not self.authenticated or not self.session:
            return []
        
        try:
            trades = self.session.user_trades_get(limit=limit)
            return self._normalize_list(trades)
        except Exception as e:
            logger.error(f"❌ Failed to get trades: {e}")
            return []
    
    def get_user_profile(self) -> Optional[Dict]:
        """Get user's profile information."""
        if not self.authenticated or not self.session:
            return None
        
        try:
            profile = self.session.user_get_profile()
            return profile
        except Exception as e:
            logger.error(f"❌ Failed to get profile: {e}")
            return None
    
    def get_account_history(self) -> List[Dict]:
        """Get user's account history."""
        if not self.authenticated or not self.session:
            return []
        
        try:
            history = self.session.user_get_account_history()
            return self._normalize_list(history)
        except Exception as e:
            logger.error(f"❌ Failed to get account history: {e}")
            return []
    
    def get_active_markets(self, limit: int = 50) -> List[Dict]:
        """Get active prediction markets."""
        if not self.authenticated or not self.session:
            return []
        
        try:
            markets = self.session.get_markets(limit=limit)
            return self._normalize_list(markets)
        except Exception as e:
            logger.error(f"❌ Failed to get markets: {e}")
            return []
