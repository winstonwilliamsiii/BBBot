"""
APIClient for Bentley Bot Vercel Backend
Manages connections to the serverless API with environment-aware routing
"""

import os
import requests
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """Manages connections to Bentley Bot Vercel API"""
    
    def __init__(self):
        """Initialize API client with environment-aware configuration"""
        env = os.getenv("DEPLOYMENT_ENV", "local")
        self.deployment_env = env
        
        # Set base URL based on deployment environment
        if env == "production":
            self.base_url = "https://bbbot305.streamlit.app/api"
        elif env == "staging":
            # For staging, use environment variable if available
            self.base_url = os.getenv("STAGING_API_URL", "http://localhost:3000/api")
        else:
            # Local development
            self.base_url = "http://localhost:8501/api"
        
        # API authentication
        self.api_key = os.getenv("API_GATEWAY_KEY", "")
        self.timeout = int(os.getenv("API_TIMEOUT", "10"))
        
        logger.info(f"APIClient initialized for {env} environment")
        logger.debug(f"Base URL: {self.base_url}")
    
    def _headers(self) -> Dict[str, str]:
        """Build request headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "BentleyBudgetBot/1.0",
        }
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        return headers
    
    def _request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Execute HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            headers = self._headers()
            
            if method.upper() == "GET":
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=self.timeout,
                    **kwargs
                )
            elif method.upper() == "POST":
                response = requests.post(
                    url, 
                    headers=headers, 
                    timeout=self.timeout,
                    **kwargs
                )
            elif method.upper() == "PUT":
                response = requests.put(
                    url, 
                    headers=headers, 
                    timeout=self.timeout,
                    **kwargs
                )
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            # Check for errors
            response.raise_for_status()
            
            # Parse response
            try:
                return response.json()
            except ValueError:
                return {"status": response.status_code, "body": response.text}
        
        except requests.exceptions.Timeout:
            logger.error(f"API request timeout: {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error to API: {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code}: {url}")
            return None
        except Exception as e:
            logger.error(f"Unexpected API error: {str(e)}")
            return None
    
    def health_check(self) -> bool:
        """Verify API is operational"""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                headers=self._headers(),
                timeout=self.timeout
            )
            return response.status_code == 200 and "healthy" in response.text.lower()
        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            return False
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get backend operational status"""
        return self._request("GET", "/status")
    
    def get_migration_status(self) -> Optional[Dict[str, Any]]:
        """Get database migration status"""
        return self._request("GET", "/status/migration")
    
    def get_health(self) -> Optional[Dict[str, Any]]:
        """Get detailed health information"""
        return self._request("GET", "/health")
    
    def check_connectivity(self) -> Dict[str, bool]:
        """Comprehensive connectivity check"""
        return {
            "api_health": self.health_check(),
            "api_status": self.get_status() is not None,
            "migrations": self.get_migration_status() is not None,
        }


def get_api_client() -> APIClient:
    """Factory function for API client (singleton pattern)"""
    if not hasattr(get_api_client, '_instance'):
        get_api_client._instance = APIClient()
    return get_api_client._instance
