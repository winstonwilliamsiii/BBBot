"""
Bank of America CashPro API Integration
========================================
Alternative bank connection using BofA CashPro APIs for transaction data.

Features:
- Current day transaction inquiry
- Account balance retrieval
- Transaction history
- OAuth 2.0 authentication

API Documentation: https://developer.bankofamerica.com/cashpro/apis
"""

import os
import requests
import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime, date
from dotenv import load_dotenv
import mysql.connector

load_dotenv()


def get_secret(key: str, default: str = None) -> str:
    """Get secret from Streamlit secrets or environment variables"""
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


class BofACashProClient:
    """Bank of America CashPro API Client"""
    
    def __init__(self):
        """Initialize CashPro client with credentials"""
        self.client_id = get_secret('BOFA_CLIENT_ID', '')
        self.client_secret = get_secret('BOFA_CLIENT_SECRET', '')
        self.api_key = get_secret('BOFA_API_KEY', '')
        self.environment = get_secret('BOFA_ENV', 'sandbox')  # sandbox or production
        
        # API Base URLs
        self.base_urls = {
            'sandbox': 'https://api-it.bankofamerica.com',
            'production': 'https://api.bankofamerica.com'
        }
        self.base_url = self.base_urls.get(self.environment, self.base_urls['sandbox'])
        
        # OAuth token storage
        self.access_token = None
        self.token_expires_at = None
    
    def _get_headers(self) -> Dict:
        """Get API request headers"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        return headers
    
    def authenticate(self) -> bool:
        """
        Authenticate with BofA CashPro OAuth 2.0
        
        Returns:
            bool: True if authentication successful
        """
        try:
            url = f"{self.base_url}/oauth/token"
            
            payload = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'cashpro.reporting'
            }
            
            response = requests.post(url, data=payload, headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            })
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                expires_in = data.get('expires_in', 3600)  # Default 1 hour
                self.token_expires_at = datetime.now().timestamp() + expires_in
                return True
            else:
                st.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            st.error(f"Authentication error: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated and token is valid"""
        if not self.access_token:
            return False
        
        if self.token_expires_at and datetime.now().timestamp() >= self.token_expires_at:
            return False
        
        return True
    
    def get_current_day_transactions(
        self,
        account_number: str,
        transaction_date: Optional[str] = None
    ) -> Dict:
        """
        Get current day transaction history from CashPro
        
        Args:
            account_number: Bank account number
            transaction_date: Date in YYYY-MM-DD format (defaults to today)
        
        Returns:
            Dict with transaction data or error
        """
        # Ensure authenticated
        if not self.is_authenticated():
            if not self.authenticate():
                return {'error': 'Authentication failed'}
        
        # Default to today if no date provided
        if not transaction_date:
            transaction_date = date.today().strftime('%Y-%m-%d')
        
        try:
            url = f"{self.base_url}/cashpro/reporting/v1/transaction-inquiries/current-day"
            
            payload = {
                'accountNumber': account_number,
                'transactionDate': transaction_date,
                'pageSize': 100,  # Max results per page
                'pageNumber': 1
            }
            
            response = requests.post(url, json=payload, headers=self._get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'error': f'API Error {response.status_code}',
                    'message': response.text
                }
                
        except Exception as e:
            return {'error': str(e)}
    
    def get_account_balance(self, account_number: str) -> Dict:
        """
        Get account balance
        
        Args:
            account_number: Bank account number
        
        Returns:
            Dict with balance data
        """
        if not self.is_authenticated():
            if not self.authenticate():
                return {'error': 'Authentication failed'}
        
        try:
            url = f"{self.base_url}/cashpro/reporting/v1/account-balances"
            
            payload = {
                'accountNumber': account_number
            }
            
            response = requests.post(url, json=payload, headers=self._get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'error': f'API Error {response.status_code}',
                    'message': response.text
                }
                
        except Exception as e:
            return {'error': str(e)}


def save_bofa_connection(user_id: int, account_number: str, account_name: str) -> bool:
    """
    Save BofA CashPro connection to database
    
    Args:
        user_id: User ID
        account_number: BofA account number
        account_name: Account nickname
    
    Returns:
        bool: Success status
    """
    try:
        from frontend.utils.budget_analysis import BudgetAnalyzer
        
        analyzer = BudgetAnalyzer()
        conn = analyzer._get_connection()
        
        if conn:
            cursor = conn.cursor()
            
            # Save to plaid_items table (reusing structure for BofA)
            sql = """
                INSERT INTO plaid_items (item_id, user_id, access_token, institution_name, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE 
                    institution_name = VALUES(institution_name),
                    updated_at = NOW()
            """
            
            # Use account number as item_id for BofA
            cursor.execute(sql, (
                f"bofa_{account_number}",
                user_id,
                account_number,  # Store account number as access token
                account_name
            ))
            conn.commit()
            
            cursor.close()
            conn.close()
            return True
            
    except Exception as e:
        st.error(f"Failed to save BofA connection: {e}")
        return False


def sync_bofa_transactions(user_id: int, account_number: str, days_back: int = 30) -> int:
    """
    Sync transactions from BofA CashPro to database
    
    Args:
        user_id: User ID
        account_number: BofA account number
        days_back: Number of days to sync (default 30)
    
    Returns:
        int: Number of transactions synced
    """
    client = BofACashProClient()
    
    if not client.authenticate():
        st.error("Failed to authenticate with BofA CashPro")
        return 0
    
    synced_count = 0
    
    try:
        from frontend.utils.budget_analysis import BudgetAnalyzer
        analyzer = BudgetAnalyzer()
        conn = analyzer._get_connection()
        
        if not conn:
            return 0
        
        cursor = conn.cursor()
        
        # Fetch transactions for each day
        from datetime import timedelta
        
        for i in range(days_back):
            transaction_date = (date.today() - timedelta(days=i)).strftime('%Y-%m-%d')
            
            result = client.get_current_day_transactions(account_number, transaction_date)
            
            if 'error' in result:
                st.warning(f"Error fetching {transaction_date}: {result['error']}")
                continue
            
            transactions = result.get('transactions', [])
            
            for txn in transactions:
                try:
                    # Insert transaction
                    sql = """
                        INSERT INTO transactions (
                            user_id, account_id, amount, date, name, 
                            merchant_name, category, pending, transaction_id, 
                            created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        ON DUPLICATE KEY UPDATE 
                            amount = VALUES(amount),
                            name = VALUES(name),
                            merchant_name = VALUES(merchant_name),
                            category = VALUES(category),
                            pending = VALUES(pending)
                    """
                    
                    cursor.execute(sql, (
                        user_id,
                        account_number,
                        float(txn.get('amount', 0)),
                        txn.get('transactionDate', transaction_date),
                        txn.get('description', 'Unknown'),
                        txn.get('merchantName', ''),
                        txn.get('category', 'Uncategorized'),
                        False,  # BofA transactions are settled
                        txn.get('transactionId', f"bofa_{txn.get('referenceNumber')}")
                    ))
                    
                    synced_count += 1
                    
                except Exception as e:
                    st.warning(f"Failed to save transaction: {e}")
                    continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return synced_count
        
    except Exception as e:
        st.error(f"Sync error: {e}")
        return 0


def render_bofa_connection_form(user_id: int):
    """
    Render BofA CashPro connection form
    
    Args:
        user_id: User ID
    """
    st.markdown("### 🏦 Bank of America CashPro")
    st.info("💡 Connect your BofA business account via CashPro API")
    
    with st.form("bofa_connection_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            account_number = st.text_input(
                "Account Number",
                placeholder="Enter your BofA account number",
                help="Your Bank of America business account number"
            )
        
        with col2:
            account_name = st.text_input(
                "Account Nickname",
                placeholder="e.g., Business Checking",
                help="A friendly name for this account"
            )
        
        days_to_sync = st.slider(
            "Days of history to sync",
            min_value=1,
            max_value=90,
            value=30,
            help="How many days back to fetch transactions"
        )
        
        submitted = st.form_submit_button(
            "🔗 Connect BofA Account",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if not account_number or not account_name:
                st.error("⚠️ Please fill in all fields")
            else:
                with st.spinner("Connecting to Bank of America..."):
                    # Test authentication
                    client = BofACashProClient()
                    if client.authenticate():
                        # Save connection
                        if save_bofa_connection(user_id, account_number, account_name):
                            st.success("✅ Connection saved!")
                            
                            # Sync transactions
                            with st.spinner(f"Syncing {days_to_sync} days of transactions..."):
                                count = sync_bofa_transactions(user_id, account_number, days_to_sync)
                                st.success(f"✅ Synced {count} transactions!")
                                st.balloons()
                                st.rerun()
                        else:
                            st.error("Failed to save connection")
                    else:
                        st.error("Failed to authenticate with BofA CashPro")
    
    # Help section
    with st.expander("❓ Setup Instructions"):
        st.markdown("""
        **Prerequisites:**
        
        1. **BofA CashPro Account** - Your business must have CashPro enabled
        2. **API Credentials** - Request from your BofA relationship manager
        3. **Configuration** - Add to Streamlit secrets:
        
        ```toml
        BOFA_CLIENT_ID = "your_client_id"
        BOFA_CLIENT_SECRET = "your_client_secret"
        BOFA_API_KEY = "your_api_key"
        BOFA_ENV = "sandbox"  # or "production"
        ```
        
        **Sandbox Testing:**
        - Environment: `sandbox`
        - Test Account: Use any account number
        - API returns sample transaction data
        
        **Production:**
        - Environment: `production`
        - Requires live CashPro account
        - Real transaction data
        
        **API Documentation:**
        https://developer.bankofamerica.com/cashpro/apis
        """)
