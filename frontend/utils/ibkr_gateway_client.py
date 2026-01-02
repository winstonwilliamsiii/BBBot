"""
IBKR Gateway OAuth Client Module
Comprehensive OAuth handshake and session management for IBKR Gateway

Architecture:
┌──────────────────────────────┐
│  ibkr_gateway_client module  │
├──────────────────────────────┤
│ start_gateway()              │
│ check_auth_status()          │
│ wait_for_login()             │
│ ensure_session()             │
│ refresh_session()            │
│ api_request(path, method)    │
└──────────────────────────────┘

Features:
- Automatic gateway startup
- OAuth handshake management
- Session token refresh
- Auto-retry with exponential backoff
- Reusable API request wrapper
- Connection health monitoring
"""

import subprocess
import requests
import time
import logging
import json
from typing import Optional, Dict, Any, Literal
from pathlib import Path
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
import urllib3

# Disable SSL warnings for local gateway
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


@dataclass
class GatewayConfig:
    """IBKR Gateway configuration"""
    gateway_path: str
    base_url: str = "https://localhost:5000"
    username: Optional[str] = None
    password: Optional[str] = None
    verify_ssl: bool = False
    startup_timeout: int = 60
    login_timeout: int = 120
    retry_attempts: int = 3
    retry_delay: int = 2


class IBKRGatewayClient:
    """
    IBKR Gateway OAuth Client
    
    Handles complete OAuth flow including:
    - Gateway startup
    - Authentication status monitoring
    - Session token management
    - API request handling with auto-retry
    
    Usage:
        client = IBKRGatewayClient(config)
        client.start_gateway()
        client.wait_for_login()
        response = client.api_request("/iserver/accounts")
    """
    
    def __init__(self, config: GatewayConfig):
        """
        Initialize IBKR Gateway Client
        
        Args:
            config: Gateway configuration object
        """
        self.config = config
        self.gateway_process = None
        self.session = requests.Session()
        self.session.verify = config.verify_ssl
        self.authenticated = False
        self.last_auth_check = None
        self.session_token = None
        
        logger.info(f"IBKR Gateway Client initialized: {config.base_url}")
    
    def start_gateway(self) -> bool:
        """
        Start IBKR Gateway application
        
        Returns:
            True if gateway started successfully or already running
            
        Example:
            client.start_gateway()
        """
        try:
            # Check if gateway is already running
            if self.check_auth_status():
                logger.info("Gateway already running and accessible")
                return True
            
            # Verify gateway path exists
            gateway_path = Path(self.config.gateway_path)
            if not gateway_path.exists():
                logger.error(f"Gateway executable not found: {gateway_path}")
                return False
            
            # Start gateway process
            logger.info(f"Starting IBKR Gateway: {gateway_path}")
            
            if os.name == 'nt':  # Windows
                self.gateway_process = subprocess.Popen(
                    [str(gateway_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:  # Unix/Mac
                self.gateway_process = subprocess.Popen(
                    [str(gateway_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # Wait for gateway to initialize
            logger.info("Waiting for gateway to initialize...")
            start_time = time.time()
            
            while time.time() - start_time < self.config.startup_timeout:
                try:
                    response = self.session.get(
                        f"{self.config.base_url}/v1/api/portal/iserver/auth/status",
                        timeout=2
                    )
                    if response.status_code == 200:
                        logger.info("✅ Gateway started successfully")
                        return True
                except Exception:
                    pass
                
                time.sleep(2)
            
            logger.error("Gateway startup timeout")
            return False
            
        except Exception as e:
            logger.error(f"Error starting gateway: {e}")
            return False
    
    def check_auth_status(self) -> bool:
        """
        Check current authentication status
        
        Returns:
            True if authenticated, False otherwise
            
        Example:
            if client.check_auth_status():
                print("Authenticated!")
        """
        try:
            response = self.session.get(
                f"{self.config.base_url}/v1/api/iserver/auth/status",
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            self.authenticated = data.get('authenticated', False)
            self.last_auth_check = datetime.now()
            
            if self.authenticated:
                logger.info("✅ Authenticated with IBKR Gateway")
                # Check for session token
                if 'sessionToken' in data:
                    self.session_token = data['sessionToken']
            else:
                logger.warning("⚠️ Not authenticated - login required")
            
            return self.authenticated
            
        except Exception as e:
            logger.error(f"Auth status check failed: {e}")
            self.authenticated = False
            return False
    
    def wait_for_login(self, timeout: Optional[int] = None) -> bool:
        """
        Wait for user to complete login via gateway UI
        
        Args:
            timeout: Maximum wait time in seconds (default: config.login_timeout)
            
        Returns:
            True if login successful
            
        Example:
            print("Please log in via Gateway UI...")
            if client.wait_for_login():
                print("Login successful!")
        """
        if timeout is None:
            timeout = self.config.login_timeout
        
        logger.info(f"⏳ Waiting for login (timeout: {timeout}s)...")
        logger.info("📝 Please complete login in IBKR Gateway window")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.check_auth_status():
                logger.info("✅ Login successful!")
                return True
            
            time.sleep(3)
        
        logger.error("❌ Login timeout - user did not complete login")
        return False
    
    def ensure_session(self) -> bool:
        """
        Ensure valid session exists (check + refresh if needed)
        
        Returns:
            True if session is valid or successfully refreshed
            
        Example:
            if client.ensure_session():
                # Safe to make API calls
                data = client.api_request("/iserver/accounts")
        """
        # Check if we need to verify auth status
        if self.last_auth_check is None or \
           datetime.now() - self.last_auth_check > timedelta(minutes=5):
            
            if not self.check_auth_status():
                logger.warning("Session expired - attempting refresh")
                return self.refresh_session()
        
        return self.authenticated
    
    def refresh_session(self) -> bool:
        """
        Refresh the authentication session
        
        Returns:
            True if session refreshed successfully
            
        Example:
            if not client.refresh_session():
                print("Session refresh failed - re-login required")
        """
        try:
            logger.info("🔄 Refreshing session...")
            
            response = self.session.post(
                f"{self.config.base_url}/v1/api/iserver/reauthenticate",
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Check if reauthentication succeeded
            if data.get('message') == 'triggered':
                logger.info("Session refresh triggered")
                time.sleep(2)
                return self.check_auth_status()
            
            logger.info("✅ Session refreshed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Session refresh failed: {e}")
            self.authenticated = False
            return False
    
    def api_request(
        self,
        path: str,
        method: Literal["GET", "POST", "PUT", "DELETE"] = "GET",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        auto_retry: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Make API request with auto-retry and session management
        
        Args:
            path: API endpoint path (e.g., "/iserver/accounts")
            method: HTTP method (GET, POST, PUT, DELETE)
            data: Request body data (for POST/PUT)
            params: Query parameters
            auto_retry: Enable automatic retry on failure
            
        Returns:
            Response data as dictionary, or None on error
            
        Example:
            # Get accounts
            accounts = client.api_request("/iserver/accounts")
            
            # Place order
            order_data = {"acctId": "...", "conid": 123, ...}
            result = client.api_request(
                "/iserver/account/DU123/orders",
                method="POST",
                data={"orders": [order_data]}
            )
        """
        # Ensure session is valid
        if not self.ensure_session():
            logger.error("No valid session - cannot make API request")
            return None
        
        url = f"{self.config.base_url}/v1/api{path}"
        attempts = self.config.retry_attempts if auto_retry else 1
        
        for attempt in range(1, attempts + 1):
            try:
                logger.debug(f"API Request [{attempt}/{attempts}]: {method} {path}")
                
                # Make request based on method
                if method == "GET":
                    response = self.session.get(url, params=params, timeout=10)
                elif method == "POST":
                    response = self.session.post(url, json=data, params=params, timeout=10)
                elif method == "PUT":
                    response = self.session.put(url, json=data, params=params, timeout=10)
                elif method == "DELETE":
                    response = self.session.delete(url, params=params, timeout=10)
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    return None
                
                response.raise_for_status()
                
                # Parse response
                try:
                    result = response.json()
                    logger.debug(f"✅ API request successful: {path}")
                    return result
                except json.JSONDecodeError:
                    # Some endpoints return empty response
                    logger.debug(f"✅ API request successful (no JSON): {path}")
                    return {}
                
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                
                # Handle authentication errors
                if status_code == 401:
                    logger.warning("401 Unauthorized - refreshing session...")
                    if self.refresh_session():
                        continue  # Retry with refreshed session
                    else:
                        logger.error("Session refresh failed")
                        return None
                
                # Handle rate limiting
                elif status_code == 429:
                    wait_time = self.config.retry_delay * attempt
                    logger.warning(f"Rate limited - waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                else:
                    logger.error(f"HTTP {status_code} error: {e}")
                    if attempt < attempts:
                        time.sleep(self.config.retry_delay)
                        continue
                    return None
            
            except Exception as e:
                logger.error(f"API request error: {e}")
                if attempt < attempts:
                    time.sleep(self.config.retry_delay)
                    continue
                return None
        
        logger.error(f"API request failed after {attempts} attempts")
        return None
    
    def tickle(self) -> bool:
        """
        Send tickle request to keep session alive
        
        IBKR requires periodic tickle requests to maintain session.
        Should be called every 60-90 seconds.
        
        Returns:
            True if tickle successful
            
        Example:
            # Keep session alive in background thread
            while True:
                client.tickle()
                time.sleep(60)
        """
        try:
            response = self.session.post(
                f"{self.config.base_url}/v1/api/tickle",
                timeout=5
            )
            response.raise_for_status()
            logger.debug("Session tickle successful")
            return True
        except Exception as e:
            logger.error(f"Tickle failed: {e}")
            return False
    
    def logout(self) -> bool:
        """
        Logout and invalidate session
        
        Returns:
            True if logout successful
        """
        try:
            response = self.session.post(
                f"{self.config.base_url}/v1/api/logout",
                timeout=5
            )
            response.raise_for_status()
            
            self.authenticated = False
            self.session_token = None
            logger.info("✅ Logged out successfully")
            return True
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    def stop_gateway(self):
        """Stop the gateway process if started by this client"""
        if self.gateway_process:
            try:
                self.gateway_process.terminate()
                self.gateway_process.wait(timeout=10)
                logger.info("Gateway process stopped")
            except Exception as e:
                logger.error(f"Error stopping gateway: {e}")
                try:
                    self.gateway_process.kill()
                except Exception:
                    pass


# ============================================================================
# Helper Functions
# ============================================================================

def create_client_from_env() -> IBKRGatewayClient:
    """
    Create IBKR Gateway Client from environment variables
    
    Required env vars:
        - IBKR_GATEWAY_PATH: Path to gateway executable
        - IBKR_GATEWAY_URL: Gateway URL (default: https://localhost:5000)
    
    Returns:
        Configured IBKRGatewayClient instance
        
    Example:
        client = create_client_from_env()
        client.start_gateway()
    """
    config = GatewayConfig(
        gateway_path=os.getenv("IBKR_GATEWAY_PATH", ""),
        base_url=os.getenv("IBKR_GATEWAY_URL", "https://localhost:5000"),
        username=os.getenv("IBKR_USERNAME"),
        password=os.getenv("IBKR_PASSWORD")
    )
    
    return IBKRGatewayClient(config)


def quick_start(gateway_path: str, wait_for_login: bool = True) -> Optional[IBKRGatewayClient]:
    """
    Quick start helper - Start gateway and wait for authentication
    
    Args:
        gateway_path: Path to IBKR Gateway executable
        wait_for_login: Wait for user to complete login
        
    Returns:
        Authenticated IBKRGatewayClient, or None on failure
        
    Example:
        client = quick_start("/path/to/clientportal.gw/bin/run.sh")
        if client:
            accounts = client.api_request("/iserver/accounts")
    """
    config = GatewayConfig(gateway_path=gateway_path)
    client = IBKRGatewayClient(config)
    
    # Start gateway
    if not client.start_gateway():
        logger.error("Failed to start gateway")
        return None
    
    # Wait for login if requested
    if wait_for_login:
        if not client.wait_for_login():
            logger.error("Login timeout or failed")
            return None
    
    return client


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example 1: Quick start
    print("Example 1: Quick Start")
    print("-" * 50)
    
    gateway_path = os.getenv("IBKR_GATEWAY_PATH", "")
    if gateway_path:
        client = quick_start(gateway_path)
        if client:
            # Get accounts
            accounts = client.api_request("/iserver/accounts")
            print(f"Accounts: {accounts}")
            
            # Keep session alive
            client.tickle()
    
    # Example 2: Manual control
    print("\nExample 2: Manual Control")
    print("-" * 50)
    
    config = GatewayConfig(
        gateway_path=gateway_path,
        base_url="https://localhost:5000"
    )
    
    client = IBKRGatewayClient(config)
    
    # Start gateway
    if client.start_gateway():
        print("✅ Gateway started")
        
        # Check auth status
        if client.check_auth_status():
            print("✅ Already authenticated")
        else:
            print("⏳ Waiting for login...")
            if client.wait_for_login():
                print("✅ Login successful")
        
        # Make API calls
        if client.ensure_session():
            # Get accounts
            accounts = client.api_request("/iserver/accounts")
            print(f"Accounts: {accounts}")
            
            # Get portfolio positions
            if accounts:
                account_id = accounts[0]
                positions = client.api_request(f"/portfolio/{account_id}/positions/0")
                print(f"Positions: {positions}")
        
        # Cleanup
        client.logout()
        client.stop_gateway()
