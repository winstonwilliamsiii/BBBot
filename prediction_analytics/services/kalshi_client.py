"""Kalshi API wrapper using RSA API key authentication."""
import os
import logging
import base64
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

import requests
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class KalshiClient:
    """
    Wrapper around Kalshi API using RSA API key authentication.
    Bypasses MFA/2FA by using API keys instead of email/password.
    Endpoint: https://trading-api.kalshi.com
    """
    
    def __init__(self, api_key_id: str = "", private_key_path: str = ""):
        """
        Initialize Kalshi client with RSA API key authentication.
        
        Args:
            api_key_id: Kalshi API Key ID (or KALSHI_API_KEY_ID env var)
            private_key_path: Path to RSA private key file (or KALSHI_PRIVATE_KEY_PATH env var)
        """
        self.api_key_id = api_key_id or os.getenv("KALSHI_API_KEY_ID", "")
        self.private_key_path = private_key_path or os.getenv("KALSHI_PRIVATE_KEY_PATH", "")
        self.base_url = "https://api.elections.kalshi.com"
        self.authenticated = False
        self.last_error = None
        self.private_key = None
        
        # Load private key on initialization
        if self.api_key_id and self.private_key_path:
            try:
                self._load_private_key()
                self.authenticated = True
                logger.info(f"✅ Kalshi API key loaded: {self.api_key_id[:10]}...")
            except Exception as e:
                self.authenticated = False
                self.last_error = str(e)
                logger.error(f"❌ Kalshi API key loading failed: {e}")
        else:
            self.last_error = "API Key ID and Private Key path required"
            logger.warning("⚠️ Kalshi credentials not provided")
    
    def _load_private_key(self):
        """Load RSA private key from file."""
        key_path = Path(self.private_key_path)
        if not key_path.exists():
            raise FileNotFoundError(f"Private key file not found: {self.private_key_path}")
        
        with open(key_path, "rb") as key_file:
            self.private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
    
    def _sign_request(self, method: str, path: str) -> Dict[str, str]:
        """
        Generate signed headers for Kalshi API request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (without query parameters)
            
        Returns:
            Dict with KALSHI-ACCESS-* headers
        """
        if not self.private_key:
            raise ValueError("Private key not loaded")
        
        # Generate timestamp in milliseconds
        timestamp_ms = int(time.time() * 1000)
        timestamp_str = str(timestamp_ms)
        
        # Strip query parameters from path before signing
        path_without_query = path.split('?')[0]
        
        # Create message to sign: timestamp + method + path
        msg_string = timestamp_str + method + path_without_query
        message = msg_string.encode('utf-8')
        
        # Sign with RSA-PSS
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Base64 encode signature
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        return {
            'KALSHI-ACCESS-KEY': self.api_key_id,
            'KALSHI-ACCESS-SIGNATURE': signature_b64,
            'KALSHI-ACCESS-TIMESTAMP': timestamp_str,
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, path: str, **kwargs) -> Optional[Dict]:
        """
        Make authenticated request to Kalshi API.
        
        Args:
            method: HTTP method
            path: API endpoint path
            **kwargs: Additional arguments for requests
            
        Returns:
            Response JSON or None on error
        """
        if not self.authenticated:
            logger.error("Not authenticated")
            return None
        
        try:
            headers = self._sign_request(method, path)
            url = self.base_url + path
            
            response = requests.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return None
    
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
            for key in ['data', 'items', 'results', 'markets', 'positions', 'trades', 'market_positions']:
                if key in response and isinstance(response[key], list):
                    return response[key]
            # If dict without recognized key, return as single-item list
            return [response]
        return []
    
    def get_user_portfolio(self) -> List[Dict]:
        """Get user's open market positions."""
        if not self.authenticated:
            logger.warning("Not authenticated")
            return []
        
        try:
            response = self._make_request('GET', '/trade-api/v2/portfolio/positions')
            logger.info(f"📊 Kalshi positions raw response type: {type(response)}")
            logger.info(f"📊 Kalshi positions raw response: {response}")
            
            normalized = self._normalize_list(response)
            
            if not normalized:
                logger.info("No positions found, checking fills...")
                fills_response = self._make_request('GET', '/trade-api/v2/portfolio/fills?limit=10')
                logger.info(f"📊 Recent fills: {fills_response}")
            
            return normalized
        except Exception as e:
            logger.error(f"❌ Failed to get portfolio: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def get_user_balance(self) -> Optional[Dict]:
        """Get user's account balance."""
        if not self.authenticated:
            return None
        
        try:
            balance = self._make_request('GET', '/trade-api/v2/portfolio/balance')
            return balance
        except Exception as e:
            logger.error(f"❌ Failed to get balance: {e}")
            return None
    
    def get_user_trades(self, limit: int = 100) -> List[Dict]:
        """Get user's trade history (fills)."""
        if not self.authenticated:
            return []
        
        try:
            response = self._make_request('GET', f'/trade-api/v2/portfolio/fills?limit={limit}')
            return self._normalize_list(response)
        except Exception as e:
            logger.error(f"❌ Failed to get trades: {e}")
            return []
    
    def get_user_profile(self) -> Optional[Dict]:
        """Get user's profile information."""
        if not self.authenticated:
            return None
        
        try:
            profile = self._make_request('GET', '/trade-api/v2/users/me')
            return profile
        except Exception as e:
            logger.error(f"❌ Failed to get profile: {e}")
            return None
    
    def get_account_history(self) -> List[Dict]:
        """Get user's account history."""
        if not self.authenticated:
            return []
        
        try:
            response = self._make_request('GET', '/trade-api/v2/portfolio/history')
            return self._normalize_list(response)
        except Exception as e:
            logger.error(f"❌ Failed to get account history: {e}")
            return []
    
    def get_active_markets(self, limit: int = 50) -> List[Dict]:
        """Get active prediction markets."""
        if not self.authenticated:
            return []
        
        try:
            response = self._make_request('GET', f'/trade-api/v2/markets?limit={limit}&status=open')
            return self._normalize_list(response)
        except Exception as e:
            logger.error(f"❌ Failed to get markets: {e}")
            return []
