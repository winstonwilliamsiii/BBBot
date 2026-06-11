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

        # Set base URL based on deployment environment.
        # Local development should talk directly to the FastAPI backend,
        # not the Streamlit web server.
        if env == "production":
            self.base_url = os.getenv(
                "BACKEND_API_URL",
                "https://bbbot305.streamlit.app/api",
            )
        elif env == "staging":
            self.base_url = os.getenv(
                "STAGING_API_URL",
                os.getenv("BACKEND_API_URL", "http://localhost:3000/api"),
            )
        else:
            self.base_url = os.getenv(
                "CONTROL_CENTER_API_URL",
                os.getenv("FASTAPI_BASE_URL", "http://localhost:5001"),
            )

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
                    **kwargs,
                )
            elif method.upper() == "POST":
                response = requests.post(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    **kwargs,
                )
            elif method.upper() == "PUT":
                response = requests.put(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    **kwargs,
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
        for path in ("/health", "/healthz"):
            try:
                response = requests.get(
                    f"{self.base_url}{path}",
                    headers=self._headers(),
                    timeout=self.timeout,
                )
                if response.status_code == 200:
                    return True
            except Exception as e:
                logger.warning(f"Health check failed for {path}: {str(e)}")
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

    def get_hydra_status(self) -> Optional[Dict[str, Any]]:
        """Get Hydra bot status."""
        return self._request("GET", "/hydra/status")

    def get_hydra_health(self) -> Optional[Dict[str, Any]]:
        """Get Hydra dependency and broker health."""
        return self._request("GET", "/hydra/health")

    def bootstrap_hydra(self) -> Optional[Dict[str, Any]]:
        """Bootstrap Hydra demo state."""
        return self._request("POST", "/hydra/bootstrap")

    def analyze_hydra(
        self,
        ticker: str,
        news_headlines: Optional[list[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Analyze a ticker using Hydra's factor stack."""
        return self._request(
            "POST",
            "/hydra/analyze",
            json={
                "ticker": ticker,
                "news_headlines": news_headlines or [],
            },
        )

    def trade_hydra(
        self,
        broker: str,
        ticker: str,
        action: str,
        qty: float,
        dry_run: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Submit or simulate a Hydra trade decision."""
        return self._request(
            "POST",
            "/hydra/trade",
            json={
                "broker": broker,
                "ticker": ticker,
                "action": action,
                "qty": qty,
                "dry_run": dry_run,
            },
        )

    def get_hydra_airbyte_config(self) -> Optional[Dict[str, Any]]:
        """Get Hydra's Airbyte source configuration payload."""
        return self._request("GET", "/hydra/airbyte-config")

    def get_triton_status(self) -> Optional[Dict[str, Any]]:
        """Get Triton bot status."""
        return self._request("GET", "/triton/status")

    def get_triton_health(self) -> Optional[Dict[str, Any]]:
        """Get Triton dependency and broker health."""
        return self._request("GET", "/triton/health")

    def bootstrap_triton(self) -> Optional[Dict[str, Any]]:
        """Bootstrap Triton demo analysis state."""
        return self._request("POST", "/triton/bootstrap")

    def analyze_triton(
        self,
        ticker: str,
        news_headlines: Optional[list[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Analyze a transportation ticker using Triton's forecast stack."""
        return self._request(
            "POST",
            "/triton/analyze",
            json={
                "ticker": ticker,
                "news_headlines": news_headlines or [],
            },
        )

    def trade_triton(
        self,
        broker: str,
        ticker: str,
        action: str,
        qty: float,
        dry_run: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Submit or simulate a Triton trade decision."""
        return self._request(
            "POST",
            "/triton/trade",
            json={
                "broker": broker,
                "ticker": ticker,
                "action": action,
                "qty": qty,
                "dry_run": dry_run,
            },
        )

    def get_rhea_status(self) -> Optional[Dict[str, Any]]:
        """Get Rhea bot status."""
        return self._request("GET", "/rhea/status")

    def get_rhea_health(self) -> Optional[Dict[str, Any]]:
        """Get Rhea dependency and broker health."""
        return self._request("GET", "/rhea/health")

    def bootstrap_rhea(self) -> Optional[Dict[str, Any]]:
        """Bootstrap Rhea demo analysis state."""
        return self._request("POST", "/rhea/bootstrap")

    def analyze_rhea(
        self,
        ticker: str,
        news_headlines: Optional[list[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Analyze an ADI-sector ticker using Rhea's signal stack."""
        return self._request(
            "POST",
            "/rhea/analyze",
            json={
                "ticker": ticker,
                "news_headlines": news_headlines or [],
            },
        )

    def trade_rhea(
        self,
        broker: str,
        ticker: str,
        action: str,
        qty: float,
        dry_run: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Submit or simulate a Rhea trade decision."""
        return self._request(
            "POST",
            "/rhea/trade",
            json={
                "broker": broker,
                "ticker": ticker,
                "action": action,
                "qty": qty,
                "dry_run": dry_run,
            },
        )

    def get_rhea_airbyte_config(self) -> Optional[Dict[str, Any]]:
        """Get Rhea's Airbyte source configuration payload."""
        return self._request("GET", "/rhea/airbyte-config")


def get_api_client() -> APIClient:
    """Factory function for API client (singleton pattern)"""
    if not hasattr(get_api_client, "_instance"):
        get_api_client._instance = APIClient()
    return get_api_client._instance
