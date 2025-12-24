"""
Plaid API Client for Bentley Budget Bot
Handles transaction fetching and storage to MySQL database

Supports both environment variables and Airflow Variables/Connections
for credential management.
"""
import os
import requests
import mysql.connector
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import Airflow modules (optional)
try:
    from airflow.models import Variable
    from airflow.hooks.base import BaseHook
    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False
    logger.debug("Airflow not available, using environment variables only")


class PlaidClient:
    """Client for interacting with Plaid API for financial transactions"""
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        secret: Optional[str] = None,
        base_url: Optional[str] = None,
        use_airflow: bool = True
    ):
        """
        Initialize Plaid client with credentials from Airflow or environment

        Priority order for credentials:
        1. Parameters passed to __init__
        2. Airflow Variables/Connections (if use_airflow=True)
        3. Environment variables

        Args:
            client_id: Plaid client ID
            secret: Plaid secret
            base_url: Plaid API base URL
            use_airflow: Whether to try Airflow Variables first
        """
        # Try Airflow Variables first if available
        if use_airflow and AIRFLOW_AVAILABLE and not client_id:
            try:
                client_id = Variable.get("plaid_client_id", default_var=None)
                secret = Variable.get("plaid_secret", default_var=None)
                env = Variable.get("plaid_env", default_var="sandbox")
                logger.info("Loaded Plaid credentials from Airflow Variables")
            except Exception as e:
                logger.debug(f"Could not load from Airflow Variables: {e}")

        # Fall back to environment variables
        self.client_id = client_id or os.getenv("PLAID_CLIENT_ID")
        self.secret = secret or os.getenv("PLAID_SECRET")

        # Determine environment (sandbox, development, or production)
        env = os.getenv("PLAID_ENV", "sandbox")
        default_url = f"https://{env}.plaid.com"
        self.base_url = base_url or os.getenv("PLAID_BASE_URL", default_url)

        if not self.client_id or not self.secret:
            raise ValueError(
                "Plaid credentials not found. Set via:\n"
                "1. Airflow Variables: plaid_client_id, plaid_secret\n"
                "2. Environment: PLAID_CLIENT_ID, PLAID_SECRET\n"
                "3. Pass as parameters to PlaidClient()"
            )

        logger.info(f"Initialized PlaidClient with base_url: {self.base_url}")

    def _auth_payload(self) -> Dict[str, str]:
        """Generate authentication payload for Plaid API requests"""
        return {
            "client_id": self.client_id,
            "secret": self.secret
        }

    def fetch_transactions(
        self, 
        access_token: str, 
        start_date: str, 
        end_date: str,
        count: int = 500,
        offset: int = 0
    ) -> List[Dict]:
        """
        Fetch transactions from Plaid API
        
        Args:
            access_token: Plaid access token for the account
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            count: Number of transactions to fetch (max 500)
            offset: Pagination offset
            
        Returns:
            List of transaction dictionaries
        """
        url = f"{self.base_url}/transactions/get"
        payload = {
            **self._auth_payload(),
            "access_token": access_token,
            "start_date": start_date,
            "end_date": end_date,
            "options": {
                "count": min(count, 500),
                "offset": offset
            }
        }
        
        try:
            logger.info(f"Fetching transactions from {start_date} to {end_date}")
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            transactions = data.get("transactions", [])
            logger.info(f"Fetched {len(transactions)} transactions")
            return transactions
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch transactions from Plaid: {e}")
            raise

    def store_transactions(
        self,
        transactions: List[Dict],
        conn_params: Optional[Dict] = None,
        use_airflow: bool = True
    ) -> int:
        """
        Store transactions in MySQL database

        Args:
            transactions: List of transaction dictionaries from Plaid
            conn_params: MySQL connection parameters
            use_airflow: Whether to try Airflow Connection first

        Returns:
            Number of transactions stored
        """
        # Try Airflow MySQL Connection first
        if conn_params is None and use_airflow and AIRFLOW_AVAILABLE:
            try:
                # Get MySQL connection from Airflow Connections
                mysql_conn = BaseHook.get_connection("mysql_default")
                conn_params = {
                    "host": mysql_conn.host or "localhost",
                    "port": mysql_conn.port or 3307,
                    "user": mysql_conn.login or "root",
                    "password": mysql_conn.password or "root",
                    "database": mysql_conn.schema or "mansa_bot"
                }
                logger.info("Using MySQL connection from Airflow Connections")
            except Exception as e:
                logger.debug(f"Could not load from Airflow Connection: {e}")

        # Fall back to environment variables if still None
        if conn_params is None:
            conn_params = {
                "host": os.getenv("MYSQL_HOST", "localhost"),
                "port": int(os.getenv("MYSQL_PORT", 3307)),
                "user": os.getenv("MYSQL_USER", "root"),
                "password": os.getenv("MYSQL_PASSWORD", "root"),
                "database": os.getenv("MYSQL_DATABASE", "mansa_bot")
            }

        conn = None
        cursor = None
        stored_count = 0
        
        try:
            conn = mysql.connector.connect(**conn_params)
            cursor = conn.cursor()
            
            for tx in transactions:
                try:
                    # Insert or update transaction (handle duplicates)
                    cursor.execute(
                        """
                        INSERT INTO transactions 
                        (transaction_id, amount, date, name, merchant_name, category, pending)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        amount = VALUES(amount),
                        name = VALUES(name),
                        merchant_name = VALUES(merchant_name),
                        category = VALUES(category),
                        pending = VALUES(pending)
                        """,
                        (
                            tx.get("transaction_id"),
                            tx.get("amount"),
                            tx.get("date"),
                            tx.get("name"),
                            tx.get("merchant_name"),
                            ",".join(tx.get("category", [])),
                            tx.get("pending", False)
                        )
                    )
                    stored_count += 1
                except mysql.connector.Error as e:
                    logger.warning(f"Failed to store transaction {tx.get('transaction_id')}: {e}")
                    continue
            
            conn.commit()
            logger.info(f"Successfully stored {stored_count} transactions")
            return stored_count
            
        except mysql.connector.Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


def plaid_ingest(**context):
    """
    Airflow task function to ingest Plaid transactions

    Credentials priority:
    1. Airflow Variables (recommended for production)
    2. Airflow Connections (for MySQL)
    3. Environment variables (for local development)

    Required Airflow Variables:
    - plaid_client_id: Plaid client ID
    - plaid_secret: Plaid secret
    - plaid_access_token: Plaid access token
    - plaid_env: sandbox|development|production (optional)
    - plaid_start_date: Start date YYYY-MM-DD (optional)
    - plaid_end_date: End date YYYY-MM-DD (optional)

    Required Airflow Connection:
    - mysql_default: MySQL connection for storing transactions

    Usage in DAG:
        from plaid_client import plaid_ingest

        PythonOperator(
            task_id='fetch_plaid_transactions',
            python_callable=plaid_ingest
        )
    """
    try:
        # Get access token from Airflow Variable or environment
        access_token = None
        if AIRFLOW_AVAILABLE:
            try:
                access_token = Variable.get("plaid_access_token")
                logger.info("Using access token from Airflow Variable")
            except Exception as e:
                logger.debug(f"Could not get access token from Airflow: {e}")

        if not access_token:
            access_token = os.getenv("PLAID_ACCESS_TOKEN")
            if not access_token:
                raise ValueError(
                    "Plaid access token not found. Set via:\n"
                    "1. Airflow Variable: plaid_access_token\n"
                    "2. Environment: PLAID_ACCESS_TOKEN"
                )

        # Initialize client (will try Airflow Variables first)
        client = PlaidClient(use_airflow=True)

        # Get date range from Airflow Variables or environment
        start_date = "2025-11-01"
        end_date = "2025-11-23"
        if AIRFLOW_AVAILABLE:
            try:
                start_date = Variable.get("plaid_start_date", start_date)
                end_date = Variable.get("plaid_end_date", end_date)
            except Exception:
                pass

        start_date = os.getenv("PLAID_START_DATE", start_date)
        end_date = os.getenv("PLAID_END_DATE", end_date)

        logger.info(f"Fetching Plaid transactions: {start_date} to {end_date}")

        # Fetch transactions
        transactions = client.fetch_transactions(
            access_token, start_date, end_date
        )

        # Store in database (will try Airflow Connection first)
        stored_count = client.store_transactions(
            transactions, use_airflow=True
        )

        result = {
            "transactions_fetched": len(transactions),
            "transactions_stored": stored_count
        }
        logger.info(f"Plaid ingest complete: {result}")
        return result

    except Exception as e:
        logger.error(f"Plaid ingest failed: {e}")
        raise