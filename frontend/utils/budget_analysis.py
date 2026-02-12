"""
Budget Analysis Module for Plaid Integration
============================================
Handles transaction categorization, cash flow calculations, and budget analysis.

Features:
- Fetch user transactions from MySQL
- Calculate income, expenses, and net cash flow
- Compare budget vs actual spending
- Generate spending insights and alerts
- Category-based analysis
- Monthly/yearly aggregations

Database: Railway MySQL (cloud) or local MySQL (development)
"""

import mysql.connector
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import os
from functools import lru_cache
import streamlit as st
from dotenv import load_dotenv

# Force reload environment variables
load_dotenv(override=True)


def get_secret(key: str, default: str = None) -> str:
    """
    Get a secret value from Streamlit secrets (cloud) or environment variables (local).
    Streamlit Cloud uses st.secrets, local development uses .env files.
    """
    # Try Streamlit secrets first (for Streamlit Cloud)
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            value = str(st.secrets[key])
            # DEBUG: Log where the value came from
            if key.endswith('PORT'):
                st.sidebar.warning(f"🔍 {key} from secrets: {value}")
            return value
    except Exception as e:
        if key.endswith('PORT'):
            st.sidebar.warning(f"🔍 {key} NOT in secrets, trying env")
    
    # Fall back to environment variables (for local development)
    env_value = os.getenv(key, default)
    if key.endswith('PORT'):
        st.sidebar.warning(f"🔍 {key} from env/default: {env_value}")
    return env_value


class BudgetAnalyzer:
    """Main class for budget analysis operations."""
    
    def __init__(self):
        """Initialize database connection."""
        # Use separate budget database configuration
        # Check Streamlit secrets first, then fall back to env vars
        
        # Get host first to determine if Railway
        host = get_secret('BUDGET_MYSQL_HOST', get_secret('MYSQL_HOST', get_secret('DB_HOST', '127.0.0.1')))
        is_railway = any(x in host for x in ('railway', 'nozomi'))
        
        # Smart default port: Railway uses 54537, local uses 3307
        default_port = '54537' if is_railway else '3307'
        
        self.db_config = {
            'host': host,
            'port': int(get_secret('BUDGET_MYSQL_PORT', get_secret('MYSQL_PORT', get_secret('DB_PORT', default_port)))),
            'user': get_secret('BUDGET_MYSQL_USER', get_secret('MYSQL_USER', get_secret('DB_USER', 'root'))),
            'password': get_secret('BUDGET_MYSQL_PASSWORD', get_secret('MYSQL_PASSWORD', get_secret('DB_PASSWORD', ''))),
            'database': get_secret('BUDGET_MYSQL_DATABASE', get_secret('MYSQL_DATABASE', get_secret('DB_NAME', 'mansa_bot' if is_railway else 'mydb'))),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci'
        }
        
        # DEBUG: Show what port is being used
        st.sidebar.info(f"🔍 DEBUG: Connecting to {host}:{self.db_config['port']} ({'Railway' if is_railway else 'Local'})")
    
    def _get_connection(self):
        """Create database connection."""
        try:
            return mysql.connector.connect(**self.db_config)
        except mysql.connector.Error as err:
            st.error(f"❌ Database connection error: {err}")
            
            # Provide helpful troubleshooting
            with st.expander("🔧 Troubleshooting Database Connection"):
                st.markdown(f"""
                **Connection Details:**
                - Host: `{self.db_config['host']}`
                - Port: `{self.db_config['port']}`
                - Database: `{self.db_config['database']}`
                - User: `{self.db_config['user']}`
                
                **For Streamlit Cloud (Railway Production):**
                Add these secrets in Settings → Secrets:
                ```toml
                MYSQL_HOST = "nozomi.proxy.rlwy.net"
                MYSQL_PORT = "54537"
                MYSQL_USER = "root"
                MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
                MYSQL_DATABASE = "mansa_bot"
                ```
                
                **For Local Development:**
                
                1. ✅ **Check MySQL is running:**
                   ```powershell
                   netstat -an | Select-String "3306"
                   ```
                
                2. ✅ **Verify database exists:**
                   ```sql
                   mysql -u root -p
                   SHOW DATABASES;
                   CREATE DATABASE IF NOT EXISTS mydb;
                   ```
                
                3. ✅ **Run database schema:**
                   ```powershell
                   mysql -u root -p mydb < scripts/setup/budget_schema.sql
                   ```
                
                4. ✅ **Check .env configuration:**
                   ```
                   MYSQL_HOST=127.0.0.1
                   MYSQL_PORT=3306
                   MYSQL_USER=root
                   MYSQL_PASSWORD=root
                   MYSQL_DATABASE=mydb
                   ```
                
                5. ✅ **Restart MySQL service:**
                   ```powershell
                   # Windows
                   net stop MySQL80
                   net start MySQL80
                   
                   # Or restart via Services.msc
                   ```
                
                **Error Code Reference:**
                - `2003`: Cannot connect to server (check if MySQL is running)
                - `1045`: Access denied (check username/password)
                - `1049`: Unknown database (create database first)
                """)
            
            return None
    
    # ==========================================================================
    # Transaction Fetching
    # ==========================================================================
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def fetch_transactions(_self, user_id: int, start_date: str = None, 
                          end_date: str = None, category: str = None) -> pd.DataFrame:
        """
        Fetch transactions for a user with optional filters.
        
        Args:
            user_id: User ID to fetch transactions for
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            category: Filter by category (optional)
        
        Returns:
            DataFrame with transactions
        """
        conn = _self._get_connection()
        if not conn:
            return pd.DataFrame()
        
        try:
            query = """
                SELECT 
                    t.transaction_id,
                    t.date,
                    t.name,
                    t.merchant_name,
                    t.amount,
                    t.category,
                    t.pending,
                    tn.note,
                    tn.tags,
                    tn.is_recurring
                FROM transactions t
                LEFT JOIN transaction_notes tn 
                    ON t.transaction_id = tn.transaction_id 
                    AND t.user_id = tn.user_id
                WHERE t.user_id = %s
            """
            
            params = [user_id]
            
            if start_date:
                query += " AND t.date >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND t.date <= %s"
                params.append(end_date)
            
            if category:
                query += " AND t.category = %s"
                params.append(category)
            
            query += " ORDER BY t.date DESC"
            
            df = pd.read_sql(query, conn, params=params)
            
            # Convert date to datetime
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                
                # Add derived columns
                df['month'] = df['date'].dt.to_period('M')
                df['type'] = df['amount'].apply(lambda x: 'Income' if x > 0 else 'Expense')
                df['abs_amount'] = df['amount'].abs()
            
            return df
            
        except Exception as e:
            st.error(f"Error fetching transactions: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    # ==========================================================================
    # Cash Flow Calculations
    # ==========================================================================
    
    def calculate_cash_flow(self, user_id: int, month: str = None) -> Dict:
        """
        Calculate cash flow metrics for a user.
        
        Args:
            user_id: User ID
            month: Month in YYYY-MM format (defaults to current month)
        
        Returns:
            Dict with income, expenses, net_flow, and percentage changes
        """
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        # Current month
        start_date = f"{month}-01"
        end_of_month = (datetime.strptime(start_date, '%Y-%m-%d') + 
                       relativedelta(months=1) - timedelta(days=1))
        end_date = end_of_month.strftime('%Y-%m-%d')
        
        # Previous month for comparison
        prev_month = (datetime.strptime(start_date, '%Y-%m-%d') - 
                     relativedelta(months=1))
        prev_start = prev_month.strftime('%Y-%m-01')
        prev_end = (prev_month + relativedelta(months=1) - 
                   timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Fetch current month transactions
        df_current = self.fetch_transactions(user_id, start_date, end_date)
        
        # Fetch previous month transactions
        df_previous = self.fetch_transactions(user_id, prev_start, prev_end)
        
        # Calculate current month metrics
        income = df_current[df_current['amount'] > 0]['amount'].sum() if not df_current.empty else 0
        expenses = abs(df_current[df_current['amount'] < 0]['amount'].sum()) if not df_current.empty else 0
        net_flow = income - expenses
        
        # Calculate previous month metrics
        prev_income = df_previous[df_previous['amount'] > 0]['amount'].sum() if not df_previous.empty else 0
        prev_expenses = abs(df_previous[df_previous['amount'] < 0]['amount'].sum()) if not df_previous.empty else 0
        prev_net_flow = prev_income - prev_expenses
        
        # Calculate percentage changes
        income_change = ((income - prev_income) / prev_income * 100) if prev_income != 0 else 0
        expense_change = ((expenses - prev_expenses) / prev_expenses * 100) if prev_expenses != 0 else 0
        net_flow_change = ((net_flow - prev_net_flow) / prev_net_flow * 100) if prev_net_flow != 0 else 0
        
        return {
            'month': month,
            'income': round(income, 2),
            'expenses': round(expenses, 2),
            'net_flow': round(net_flow, 2),
            'income_change_pct': round(income_change, 1),
            'expense_change_pct': round(expense_change, 1),
            'net_flow_change_pct': round(net_flow_change, 1),
            'transaction_count': len(df_current),
            'avg_transaction': round(df_current['abs_amount'].mean(), 2) if not df_current.empty else 0
        }
    
    # ==========================================================================
    # Category Analysis
    # ==========================================================================
    
    def get_spending_by_category(self, user_id: int, month: str = None, 
                                 limit: int = None) -> pd.DataFrame:
        """
        Get spending breakdown by category.
        
        Args:
            user_id: User ID
            month: Month in YYYY-MM format (defaults to current month)
            limit: Limit number of categories returned (top N)
        
        Returns:
            DataFrame with category, amount, percentage, transaction_count
        """
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        start_date = f"{month}-01"
        end_of_month = (datetime.strptime(start_date, '%Y-%m-%d') + 
                       relativedelta(months=1) - timedelta(days=1))
        end_date = end_of_month.strftime('%Y-%m-%d')
        
        df = self.fetch_transactions(user_id, start_date, end_date)
        
        if df.empty:
            return pd.DataFrame()
        
        # Filter expenses only
        expenses = df[df['amount'] < 0].copy()
        
        # Group by category
        category_summary = expenses.groupby('category').agg({
            'amount': lambda x: abs(x.sum()),
            'transaction_id': 'count'
        }).reset_index()
        
        category_summary.columns = ['category', 'amount', 'transaction_count']
        
        # Calculate percentage
        total_expenses = category_summary['amount'].sum()
        category_summary['percentage'] = (category_summary['amount'] / total_expenses * 100).round(1)
        
        # Sort by amount descending
        category_summary = category_summary.sort_values('amount', ascending=False)
        
        if limit:
            category_summary = category_summary.head(limit)
        
        return category_summary
    
    # ==========================================================================
    # Budget Tracking
    # ==========================================================================
    
    def get_budget_status(self, user_id: int, month: str = None) -> pd.DataFrame:
        """
        Get budget vs actual spending comparison.
        
        Args:
            user_id: User ID
            month: Month in YYYY-MM format (defaults to current month)
        
        Returns:
            DataFrame with budget, actual, variance, status
        """
        conn = self._get_connection()
        if not conn:
            return pd.DataFrame()
        
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        month_start = f"{month}-01"
        
        try:
            query = """
                SELECT 
                    bt.category,
                    bt.budgeted,
                    bt.actual,
                    bt.variance,
                    bt.variance_pct,
                    bc.color_hex,
                    bc.icon,
                    CASE 
                        WHEN bt.actual <= bt.budgeted * 0.8 THEN 'Under Budget'
                        WHEN bt.actual <= bt.budgeted THEN 'On Track'
                        WHEN bt.actual <= bt.budgeted * 1.1 THEN 'Slightly Over'
                        ELSE 'Over Budget'
                    END AS status
                FROM budget_tracking bt
                LEFT JOIN budget_categories bc 
                    ON bt.user_id = bc.user_id 
                    AND bt.category = bc.category_name
                WHERE bt.user_id = %s 
                    AND bt.month = %s
                    AND bc.is_active = TRUE
                ORDER BY bt.actual DESC
            """
            
            df = pd.read_sql(query, conn, params=[user_id, month_start])
            return df
            
        except Exception as e:
            st.error(f"Error fetching budget status: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def update_budget_tracking(self, user_id: int, month: str = None):
        """
        Update budget tracking table with actual spending.
        
        Args:
            user_id: User ID
            month: Month in YYYY-MM format (defaults to current month)
        """
        conn = self._get_connection()
        if not conn:
            return
        
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        month_start = f"{month}-01"
        
        try:
            cursor = conn.cursor()
            cursor.callproc('update_budget_tracking', [user_id, month_start])
            conn.commit()
        except Exception as e:
            st.error(f"Error updating budget tracking: {e}")
        finally:
            conn.close()
    
    # ==========================================================================
    # Insights and Alerts
    # ==========================================================================
    
    def generate_insights(self, user_id: int, month: str = None) -> List[Dict]:
        """
        Generate spending insights and alerts.
        
        Args:
            user_id: User ID
            month: Month in YYYY-MM format
        
        Returns:
            List of insight dictionaries with type, message, severity
        """
        insights = []
        
        # Get cash flow
        cash_flow = self.calculate_cash_flow(user_id, month)
        
        # Get budget status
        budget_status = self.get_budget_status(user_id, month)
        
        # Insight 1: Net cash flow trend
        if cash_flow['net_flow'] < 0:
            insights.append({
                'type': 'warning',
                'icon': '⚠️',
                'message': f"Negative cash flow: ${abs(cash_flow['net_flow']):,.2f}",
                'severity': 'high'
            })
        elif cash_flow['net_flow_change_pct'] < -20:
            insights.append({
                'type': 'warning',
                'icon': '📉',
                'message': f"Cash flow decreased by {abs(cash_flow['net_flow_change_pct']):.1f}%",
                'severity': 'medium'
            })
        elif cash_flow['net_flow_change_pct'] > 20:
            insights.append({
                'type': 'success',
                'icon': '📈',
                'message': f"Cash flow improved by {cash_flow['net_flow_change_pct']:.1f}%",
                'severity': 'low'
            })
        
        # Insight 2: Budget overruns
        if not budget_status.empty:
            over_budget = budget_status[budget_status['status'] == 'Over Budget']
            if len(over_budget) > 0:
                for _, row in over_budget.iterrows():
                    insights.append({
                        'type': 'alert',
                        'icon': '🚨',
                        'message': f"{row['icon']} {row['category']}: ${row['actual']:,.2f} (${row['variance']:,.2f} over budget)",
                        'severity': 'high'
                    })
        
        # Insight 3: Spending increases
        if cash_flow['expense_change_pct'] > 15:
            insights.append({
                'type': 'info',
                'icon': '💸',
                'message': f"Spending increased by {cash_flow['expense_change_pct']:.1f}% this month",
                'severity': 'medium'
            })
        
        # Insight 4: Top category check
        top_categories = self.get_spending_by_category(user_id, month, limit=1)
        if not top_categories.empty:
            top_cat = top_categories.iloc[0]
            insights.append({
                'type': 'info',
                'icon': '📊',
                'message': f"Top spending: {top_cat['category']} (${top_cat['amount']:,.2f}, {top_cat['percentage']:.1f}%)",
                'severity': 'low'
            })
        
        return insights
    
    # ==========================================================================
    # Historical Trends
    # ==========================================================================
    
    def get_monthly_trends(self, user_id: int, months: int = 6) -> pd.DataFrame:
        """
        Get cash flow trends over multiple months.
        
        Args:
            user_id: User ID
            months: Number of months to retrieve (default 6)
        
        Returns:
            DataFrame with monthly income, expenses, net_flow
        """
        conn = self._get_connection()
        if not conn:
            return pd.DataFrame()
        
        try:
            query = """
                SELECT 
                    DATE_FORMAT(month, '%Y-%m') AS month,
                    total_income AS income,
                    total_expenses AS expenses,
                    net_cash_flow AS net_flow,
                    transaction_count
                FROM cash_flow_summary
                WHERE user_id = %s
                ORDER BY month DESC
                LIMIT %s
            """
            
            df = pd.read_sql(query, conn, params=[user_id, months])
            
            # Reverse to chronological order
            df = df.iloc[::-1].reset_index(drop=True)
            
            return df
            
        except Exception as e:
            st.error(f"Error fetching monthly trends: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    # ==========================================================================
    # Plaid Integration Helpers
    # ==========================================================================
    
    def check_plaid_connection(self, user_id: int) -> Dict:
        """
        Check if user has connected Plaid account.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with connection status and details
        """
        conn = self._get_connection()
        if not conn:
            return {'connected': False}
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Try plaid_items table first (new structure), then fall back to user_plaid_tokens (old structure)
            tables_to_try = [
                ('plaid_items', 'created_at'),  # new table
                ('user_plaid_tokens', 'last_sync')  # old table
            ]
            
            for table_name, timestamp_col in tables_to_try:
                try:
                    query = f"""
                        SELECT 
                            institution_name,
                            {timestamp_col} as last_sync,
                            COALESCE(is_active, 1) as is_active
                        FROM {table_name}
                        WHERE user_id = %s AND COALESCE(is_active, 1) = 1
                        ORDER BY {timestamp_col} DESC
                        LIMIT 1
                    """
                    cursor.execute(query, (user_id,))
                    result = cursor.fetchone()
                    
                    if result:
                        return {
                            'connected': True,
                            'institution': result['institution_name'],
                            'last_sync': result['last_sync'],
                            'is_active': result['is_active']
                        }
                except mysql.connector.Error:
                    # Table doesn't exist, try next one
                    continue
            
            return {'connected': False}
                
        except Exception as e:
            # More detailed error for debugging
            import traceback
            error_details = traceback.format_exc()
            st.error(f"Error checking Plaid connection: {e}")
            with st.expander("🔍 Debug Details"):
                st.code(error_details)
            return {'connected': False}
        finally:
            conn.close()


# ==========================================================================
# Utility Functions
# ==========================================================================

def format_currency(amount: float) -> str:
    """Format amount as currency."""
    return f"${amount:,.2f}"


def format_percentage(pct: float, include_sign: bool = True) -> str:
    """Format percentage with optional sign."""
    sign = '+' if pct > 0 and include_sign else ''
    return f"{sign}{pct:.1f}%"


def get_trend_emoji(value: float) -> str:
    """Get emoji based on trend direction."""
    if value > 5:
        return "📈"
    elif value < -5:
        return "📉"
    else:
        return "➡️"


def categorize_transaction(name: str, category: str = None) -> str:
    """
    Simple transaction categorization based on merchant name.
    This is a fallback if Plaid doesn't provide category.
    
    Args:
        name: Transaction name/merchant
        category: Plaid-provided category (if available)
    
    Returns:
        Category string
    """
    if category:
        return category
    
    name_lower = name.lower()
    
    # Simple keyword matching
    if any(word in name_lower for word in ['uber', 'lyft', 'gas', 'shell', 'chevron', 'exxon']):
        return 'Transportation'
    elif any(word in name_lower for word in ['restaurant', 'cafe', 'pizza', 'starbucks', 'mcdonald']):
        return 'Food and Drink'
    elif any(word in name_lower for word in ['walmart', 'target', 'amazon', 'grocery', 'safeway']):
        return 'Shopping'
    elif any(word in name_lower for word in ['netflix', 'spotify', 'hulu', 'disney']):
        return 'Entertainment'
    elif any(word in name_lower for word in ['rent', 'mortgage', 'utilities', 'electric', 'internet']):
        return 'Bills and Utilities'
    elif any(word in name_lower for word in ['paycheck', 'salary', 'deposit', 'transfer in']):
        return 'Income'
    else:
        return 'Other'
