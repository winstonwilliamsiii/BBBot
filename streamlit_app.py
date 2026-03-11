import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables FIRST before any other imports with override enabled
# This ensures fresh values on every Streamlit reload
load_dotenv(override=True)

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except Exception:
    yf = None
    YFINANCE_AVAILABLE = False
from datetime import date, timedelta
import re

from frontend.utils.styling import (
    apply_custom_styling,
    create_custom_card,
    create_metric_card,
    add_footer,
)
from frontend.styles.colors import COLOR_SCHEME
from frontend.utils.yahoo import fetch_portfolio_list, fetch_portfolio_tickers
from frontend.utils.bot_fund_mapping import get_bot_catalog_rows

# Optional MySQL helper (for dev health checks)
try:
    from frontend.utils.secrets_helper import get_mysql_config
    MYSQL_HELPER_AVAILABLE = True
except ImportError:
    MYSQL_HELPER_AVAILABLE = False

# Import cache-busting reload function
try:
    from config_env import reload_env
    ENV_RELOAD_AVAILABLE = True
except ImportError:
    ENV_RELOAD_AVAILABLE = False

# RBAC and Budget Analysis imports
try:
    from frontend.utils.rbac import RBACManager, Permission, show_login_form, show_user_info
    from frontend.components.budget_dashboard import show_budget_summary
    RBAC_AVAILABLE = True
except ImportError:
    RBAC_AVAILABLE = False

# Chatbot imports
try:
    from frontend.components.bentley_chatbot import render_chatbot_interface, get_chatbot_context_data
    CHATBOT_AVAILABLE = True
except ImportError:
    CHATBOT_AVAILABLE = False

# Economic Calendar Widget import
try:
    from frontend.components.economic_calendar_widget import get_calendar_widget
    ECONOMIC_CALENDAR_AVAILABLE = True
except ImportError as e:
    ECONOMIC_CALENDAR_AVAILABLE = False

# Appwrite services imports
try:
    from services.transactions import create_transaction, get_transactions
    from services.watchlist import add_to_watchlist, get_watchlist
    APPWRITE_SERVICES_AVAILABLE = True
except ImportError:
    APPWRITE_SERVICES_AVAILABLE = False

# DCF Analysis Widget import
try:
    from frontend.components.dcf_widget import render_dcf_widget, render_dcf_mini_widget
    DCF_WIDGET_AVAILABLE = True
except ImportError:
    DCF_WIDGET_AVAILABLE = False


@st.cache_data
def get_yfinance_data(tickers, start_date, end_date):
    """Grab Yahoo Finance data (close prices) and return a long dataframe.

    This is defensive: yfinance returns different column shapes depending on
    whether a single ticker or multiple tickers are requested. We normalize
    the result to a DataFrame of close prices with tickers as columns.
    """
    if not tickers:
        return pd.DataFrame()

    try:
        if not YFINANCE_AVAILABLE:
            st.error("The 'yfinance' package is not installed. Please install it (`pip install yfinance`) to fetch live data.")
            return pd.DataFrame()

        # yfinance (and Yahoo) can be flaky with a large list of tickers.
        # To be robust, download in batches and concatenate results.
        def _chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        # choose a conservative batch size; this can be tuned
        batch_size = 8
        if isinstance(tickers, (list, tuple)) and len(tickers) > batch_size:
            frames = []
            for chunk in _chunks(list(tickers), batch_size):
                try:
                    part = yf.download(chunk, start=start_date, end=end_date, threads=True, progress=False)
                except Exception as e:
                    st.warning(f"yfinance chunk download failed for {chunk}: {e}")
                    continue
                if part is not None and not part.empty:
                    frames.append(part)
            if not frames:
                raw_df = pd.DataFrame()
            else:
                # align frames by index/columns carefully by concatenating along columns
                raw_df = pd.concat(frames, axis=1)
        else:
            raw_df = yf.download(tickers, start=start_date, end=end_date, threads=True, progress=False)
    except Exception as e:
        # Return empty dataframe on network / yfinance errors; caller can warn.
        st.error(f"Failed to download data from yfinance: {e}")
        return pd.DataFrame()

    if raw_df is None or raw_df.empty:
        return pd.DataFrame()

    # Try to extract Close prices robustly.
    close_prices = None
    try:
        # Common case: raw_df has top-level 'Close'
        close_prices = raw_df['Close']
    except Exception:
        # If columns are MultiIndex like (Ticker, OHLCV) or (OHLCV, Ticker)
        # attempt to locate columns whose name or tuple contains 'Close'
        if isinstance(raw_df.columns, pd.MultiIndex):
            # Find tuples where any level equals 'Close'
            close_cols = [col for col in raw_df.columns if 'Close' in col]
            if close_cols:
                close_prices = raw_df.loc[:, close_cols]
                # If close_cols are tuples like (ticker, 'Close') or ('Close', ticker)
                # normalize column names to ticker symbols when possible
                new_cols = []
                for c in close_cols:
                    if isinstance(c, tuple):
                        # prefer element that looks like a ticker (short, uppercase)
                        ticker_guess = None
                        for element in c:
                            if isinstance(element, str) and element.isupper() and len(element) <= 6:
                                ticker_guess = element
                                break
                        new_cols.append(ticker_guess or str(c))
                    else:
                        new_cols.append(str(c))
                close_prices.columns = new_cols
        else:
            # Try to find any columns with 'Close' in their name (e.g., 'Adj Close')
            filtered = raw_df.filter(regex='Close')
            if not filtered.empty:
                close_prices = filtered

    if close_prices is None or close_prices.empty:
        return pd.DataFrame()

    # If Series (single ticker), convert to DataFrame
    if isinstance(close_prices, pd.Series):
        col_name = None
        if isinstance(tickers, (list, tuple)) and len(tickers) == 1:
            col_name = tickers[0]
        else:
            col_name = close_prices.name or 'Price'
        close_prices = close_prices.to_frame(name=col_name)

    # At this point close_prices should be a DataFrame with Date index
    df_long = close_prices.reset_index().melt(id_vars='Date', var_name='Ticker', value_name='Price')
    df_long['Date'] = pd.to_datetime(df_long['Date'])
    return df_long


def _get_mysql_config_fallback():
    if MYSQL_HELPER_AVAILABLE:
        return get_mysql_config(database=os.getenv("MYSQL_DATABASE", os.getenv("DB_NAME", "bentley_bot_dev")))
    return {
        "host": os.getenv("MYSQL_HOST", os.getenv("DB_HOST", "127.0.0.1")),
        "port": int(os.getenv("MYSQL_PORT", os.getenv("DB_PORT", "3306"))),
        "user": os.getenv("MYSQL_USER", os.getenv("DB_USER", "root")),
        "password": os.getenv("MYSQL_PASSWORD", os.getenv("DB_PASSWORD", "")),
        "database": os.getenv("MYSQL_DATABASE", os.getenv("DB_NAME", "bentley_bot_dev")),
    }


def test_mysql_connection():
    """Quick MySQL connection test for dev UI."""
    try:
        import mysql.connector
    except Exception as e:
        return {"ok": False, "error": f"mysql-connector-python not installed: {e}"}

    config = _get_mysql_config_fallback()
    try:
        conn = mysql.connector.connect(**config)
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        conn.close()
        return {"ok": True, "config": config}
    except Exception as e:
        return {"ok": False, "error": str(e), "config": config}


def ensure_dev_schema():
    """Auto-create dev schema (optional) on startup."""
    if os.getenv("ENVIRONMENT", "development").lower() != "development":
        return
    if os.getenv("AUTO_CREATE_DEV_SCHEMA", "").lower() not in ("1", "true", "yes", "on"):
        return

    try:
        import mysql.connector
    except Exception:
        return

    config = _get_mysql_config_fallback()
    db_name = config.get("database") or "bentley_bot_dev"

    # Try connecting with database; if it fails, skip schema creation
    try:
        conn = mysql.connector.connect(**config)
    except Exception as e:
        # MySQL connection failed - skip schema creation (optional feature)
        print(f"⚠️  MySQL not available for dev schema creation: {e}")
        return

    # Connection successful - proceed with schema creation
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(100),
                    role VARCHAR(20) DEFAULT 'VIEWER',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    is_active BOOLEAN DEFAULT TRUE
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    account_id VARCHAR(100),
                    amount DECIMAL(10, 2) NOT NULL,
                    category VARCHAR(50),
                    date DATE NOT NULL,
                    description TEXT,
                    merchant_name VARCHAR(100),
                    plaid_transaction_id VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS plaid_items (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    plaid_item_id VARCHAR(100) UNIQUE NOT NULL,
                    access_token VARCHAR(255) NOT NULL,
                    institution_id VARCHAR(100),
                    institution_name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_synced TIMESTAMP NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_prices_yf (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                ticker VARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                open DECIMAL(10, 2),
                high DECIMAL(10, 2),
                low DECIMAL(10, 2),
                close DECIMAL(10, 2),
                volume BIGINT,
                adj_close DECIMAL(10, 2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY ticker_date (ticker, date)
                )
                """
            )
            cursor.execute(
                """
                INSERT IGNORE INTO users (username, password_hash, email, role)
                VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqQqZ5wQ5u', 'admin@localhost', 'ADMIN')
                """
            )
        conn.commit()
    except Exception as e:
        print(f"⚠️  Error creating dev schema: {e}")
    finally:
        conn.close()


def calculate_portfolio_metrics(portfolio_df):
    """Calculate portfolio metrics from uploaded CSV data."""
    if portfolio_df is None or portfolio_df.empty:
        return None, None, None, None
    
    try:
        # Get current prices for all symbols in portfolio
        symbols = portfolio_df['Symbol'].unique().tolist()
        
        if YFINANCE_AVAILABLE:
            # Fetch current prices
            current_data = {}
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                    current_data[symbol] = current_price
                except:
                    current_data[symbol] = 0
            
            # Calculate metrics
            total_value = 0
            for _, row in portfolio_df.iterrows():
                symbol = row['Symbol']
                quantity = row.get('Quantity', 0)
                current_price = current_data.get(symbol, 0)
                total_value += quantity * current_price
            
            num_assets = len(symbols)
            
            # Simple sector allocation (you can enhance this)
            num_sectors = min(5, max(1, num_assets // 2))
            
            # Calculate percentage change (if purchase price provided)
            total_cost = 0
            if 'Purchase_Price' in portfolio_df.columns:
                for _, row in portfolio_df.iterrows():
                    quantity = row.get('Quantity', 0)
                    purchase_price = row.get('Purchase_Price', 0)
                    total_cost += quantity * purchase_price
                
                if total_cost > 0:
                    change_pct = ((total_value - total_cost) / total_cost) * 100
                else:
                    change_pct = 0
            else:
                change_pct = 0
            
            return total_value, num_assets, num_sectors, change_pct
        else:
            # If yfinance not available, use placeholder values
            return None, len(symbols), min(5, max(1, len(symbols) // 2)), 0
            
    except Exception as e:
        st.sidebar.error(f"Error calculating portfolio metrics: {str(e)}")
        return None, None, None, None


def main():
    # Set page config first (Streamlit requires this before other writes)
    st.set_page_config(
        page_title="BBBot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Reload environment variables for cache-busting (ensures fresh values on every run)
    if ENV_RELOAD_AVAILABLE:
        reload_env()  # Override to break cache

    # Optional dev schema auto-create
    ensure_dev_schema()

    # Apply custom styling (CSS)
    apply_custom_styling()
    
    # Initialize RBAC session state
    if RBAC_AVAILABLE:
        RBACManager.init_session_state()
    
    # Initialize Plaid session state keys to prevent AttributeError
    if 'plaid_public_token' not in st.session_state:
        st.session_state.plaid_public_token = None
    if 'plaid_public_token_pending' not in st.session_state:
        st.session_state.plaid_public_token_pending = None
    if 'plaid_institution_name' not in st.session_state:
        st.session_state.plaid_institution_name = None
    if 'plaid_institution' not in st.session_state:
        st.session_state.plaid_institution = None
    if 'show_manual_form' not in st.session_state:
        st.session_state.show_manual_form = True

    # Additional sidebar-specific CSS with Mansa Capital styling
    st.markdown(f"""
    <style>
    /* Sidebar with Mansa Capital branding */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {COLOR_SCHEME['background']} 0%, {COLOR_SCHEME['secondary']} 100%) !important;
        border-right: 1px solid rgba(20, 184, 166, 0.2) !important;
    }}
    
    [data-testid="stSidebar"] * {{
        color: {COLOR_SCHEME['text']} !important;
    }}
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label {{
        color: {COLOR_SCHEME['text']} !important;
        font-weight: 500 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # Hide admin-only pages 6–8 from sidebar for non-ADMIN users
    if RBAC_AVAILABLE:
        RBACManager.init_session_state()
        if not RBACManager.has_permission(Permission.VIEW_TRADING_BOT):
            st.markdown(
                """
                <style>
                [data-testid="stSidebarNav"] li:nth-child(6),
                [data-testid="stSidebarNav"] li:nth-child(7),
                [data-testid="stSidebarNav"] li:nth-child(8) {
                    display: none !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

    # Main title with Mansa Capital branding
    st.markdown(f"""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 style='color: {COLOR_SCHEME['text']}; margin-bottom: 0.5rem; font-size: 3rem;'>
            <span style='color: {COLOR_SCHEME['accent_teal']}'>🤖</span> 
            <span style='background: linear-gradient(135deg, {COLOR_SCHEME['accent_teal']} 0%, {COLOR_SCHEME['accent_gold']} 100%); 
                         -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                         background-clip: text;'>Bentley Bot</span> 
            Dashboard
        </h1>
        <p style='color: rgba(255,255,255,0.9); font-size: 1.1rem; margin-bottom: 0.5rem;'>
            The ideal financial tool for time conscience folks who need to Capture that Bag
        </p>
        <div style='width: 60px; height: 3px; background: linear-gradient(90deg, {COLOR_SCHEME['accent_teal']} 0%, {COLOR_SCHEME['accent_gold']} 100%); 
                    margin: 1rem auto; border-radius: 2px;'></div>
    </div>
    """, unsafe_allow_html=True)

    # ==========================================================================
    # Bentley AI ChatBot Section - Primary Interface
    # ==========================================================================
    if CHATBOT_AVAILABLE:
        # Gather context data for the chatbot
        chatbot_context = get_chatbot_context_data()
        
        # Render chatbot interface at the top
        render_chatbot_interface(chatbot_context)
    else:
        st.markdown("---")
        st.info("🤖 **Bentley AI Assistant** - Coming soon! This will provide AI-powered financial insights and Q&A.")
    
    st.markdown("---")

    # ==========================================================================
    # Appwrite Quick Actions Section - Transaction & Watchlist Management
    # ==========================================================================
    if APPWRITE_SERVICES_AVAILABLE:
        st.header("⚡ Quick Actions")
        
        action_tab1, action_tab2 = st.tabs(["💸 Transactions", "📊 Watchlist"])
        
        with action_tab1:
            col_tx1, col_tx2 = st.columns(2)
            
            with col_tx1:
                st.subheader("View Transactions")
                user_id_tx = st.text_input("User ID", key="user_id_transactions")
                if st.button("📥 Fetch Transactions"):
                    if user_id_tx:
                        with st.spinner("Fetching transactions..."):
                            txs = get_transactions(user_id_tx, limit=10)
                            if txs.get("success"):
                                st.success(f"✅ Found {len(txs.get('transactions', []))} transactions")
                                if txs.get('transactions'):
                                    st.dataframe(pd.DataFrame(txs['transactions']))
                            else:
                                st.error(txs.get("error", "Failed to fetch transactions"))
                    else:
                        st.warning("Please enter a User ID")
            
            with col_tx2:
                st.subheader("Add Transaction")
                user_id_add = st.text_input("User ID", key="user_id_add_tx")
                amount_tx = st.number_input("Amount ($)", min_value=0.01, step=0.01, key="amount_tx")
                date_tx = st.date_input("Date", key="date_tx")
                
                if st.button("➕ Add Transaction"):
                    if user_id_add and amount_tx:
                        result = create_transaction(user_id_add, amount_tx, str(date_tx))
                        if result.get("success"):
                            st.success("✅ Transaction added successfully!")
                        else:
                            st.error(result.get("error", "Failed to add transaction"))
                    else:
                        st.warning("User ID and amount required")
        
        with action_tab2:
            col_wl1, col_wl2 = st.columns(2)
            
            with col_wl1:
                st.subheader("Add to Watchlist")
                user_id_wl = st.text_input("User ID", key="user_id_watchlist")
                symbol_wl = st.text_input("Symbol (e.g., AAPL)", key="symbol_watchlist")
                
                if st.button("➕ Add Symbol"):
                    if user_id_wl and symbol_wl:
                        result = add_to_watchlist(user_id_wl, symbol_wl)
                        if result.get("success"):
                            st.success(f"✅ Added {symbol_wl} to watchlist!")
                        else:
                            st.error(result.get("error", "Failed to add symbol"))
                    else:
                        st.warning("User ID and symbol required")
            
            with col_wl2:
                st.subheader("View Watchlist")
                user_id_view_wl = st.text_input("User ID", key="user_id_view_watchlist")
                
                if st.button("📋 View Watchlist"):
                    if user_id_view_wl:
                        wl = get_watchlist(user_id_view_wl)
                        if wl.get("success"):
                            st.success(f"✅ Found {len(wl.get('watchlist', []))} items")
                            if wl.get('watchlist'):
                                st.dataframe(pd.DataFrame(wl['watchlist']))
                        else:
                            st.error(wl.get("error", "Failed to fetch watchlist"))
                    else:
                        st.warning("Please enter a User ID")
        
        st.markdown("---")
    
    # ==========================================================================
    # Mansa Capital Fund Performance - MOVED HERE from below
    # ==========================================================================
    # Note: This section was moved here to ensure variables are defined first
    # It will be rendered after sidebar configuration
    
    # ==========================================================================
    # DCF Fundamental Analysis Section
    # ==========================================================================
    if DCF_WIDGET_AVAILABLE:
        st.markdown("## 📊 Fundamental Analysis")
        render_dcf_widget()
        st.markdown("---")
    
    # This section moved to after sidebar configuration where variables are defined
    
    st.markdown("---")
    
    # ==========================================================================
    # Economic Calendar & Market Data Section - MOVED TO BOTTOM
    # ==========================================================================
    if ECONOMIC_CALENDAR_AVAILABLE:
        st.markdown("## 📋 Markets & Economics")
        widget = get_calendar_widget()
        widget.render_full_dashboard()
        st.markdown("---")
    # Sidebar controls
    if os.getenv("ENVIRONMENT", "development").lower() == "development":
        with st.sidebar.expander("Dev: Database Health"):
            if st.button("Test MySQL Connection"):
                result = test_mysql_connection()
                if result.get("ok"):
                    st.success("MySQL connection OK")
                else:
                    st.error(f"MySQL connection failed: {result.get('error')}")
                if "config" in result:
                    st.code(
                        f"host={result['config'].get('host')}\n"
                        f"port={result['config'].get('port')}\n"
                        f"database={result['config'].get('database')}\n"
                        f"user={result['config'].get('user')}"
                    )

    # Login Section - Personal Budget Access
    st.sidebar.markdown("---")
    st.sidebar.header("🔐 Personal Budget Login")
    
    if RBAC_AVAILABLE:
        # Check if user is already logged in
        if 'rbac_user' in st.session_state and st.session_state.rbac_user:
            # User is logged in - show user info
            user = st.session_state.rbac_user
            st.sidebar.success(f"👤 Logged in as: **{user.get('username', 'User')}**")
            st.sidebar.caption(f"Role: {user.get('role', 'N/A')}")
            
            # Logout button
            if st.sidebar.button("🚪 Logout", key="sidebar_logout"):
                st.session_state.rbac_user = None
                st.rerun()
        else:
            # User not logged in - show login form
            st.sidebar.info("Sign in to access Personal Budget Analysis")
            
            with st.sidebar.expander("🔑 Login", expanded=False):
                show_login_form()
    else:
        st.sidebar.warning("⚠️ Login system unavailable")
        st.sidebar.caption("RBAC module not loaded")
    
    st.sidebar.markdown("---")
    st.sidebar.header("📄 Upload Portfolio CSV")
    
    # Add CSV upload information
    with st.sidebar.expander("ℹ️ CSV Format Help"):
        st.write("""
        **Required columns (use either naming):**
        - `Ticker` or `Symbol`: Stock ticker (e.g., AAPL, MSFT)
        - `Quantity` or `Shares`: Number of shares owned
        
        **Optional columns:**
        - `Purchase_Price` or `Price`: Price paid per share
        - `Purchase_Date` or `Date`: Date purchased (YYYY-MM-DD)
        
        **Note:** Column names are case-insensitive.
        """)
    
    portfolio_csv = st.sidebar.file_uploader(
        "Upload your portfolio data (CSV)",
        type=["csv"],
        help="CSV should contain columns: Ticker/Symbol and Quantity/Shares"
    )
    
    # Initialize portfolio_data in session state if not exists
    if 'portfolio_data' not in st.session_state:
        st.session_state.portfolio_data = None
        
    if portfolio_csv is not None:
        try:
            # Read the uploaded CSV
            portfolio_df = pd.read_csv(portfolio_csv)
            
            # Normalize column names to be case-insensitive
            portfolio_df.columns = portfolio_df.columns.str.strip()
            col_mapping = {col: col for col in portfolio_df.columns}
            
            # Map flexible column names to standard names
            for col in portfolio_df.columns:
                col_lower = col.lower()
                if col_lower in ['ticker', 'symbol']:
                    col_mapping[col] = 'Symbol'
                elif col_lower in ['quantity', 'shares', 'qty']:
                    col_mapping[col] = 'Quantity'
                elif col_lower in ['purchase_price', 'price', 'cost']:
                    col_mapping[col] = 'Purchase_Price'
                elif col_lower in ['purchase_date', 'date']:
                    col_mapping[col] = 'Purchase_Date'
            
            portfolio_df = portfolio_df.rename(columns=col_mapping)
            
            # Validate required columns exist
            if 'Symbol' not in portfolio_df.columns:
                st.sidebar.error("❌ CSV must contain 'Ticker' or 'Symbol' column")
                st.sidebar.info(f"Found columns: {', '.join(portfolio_df.columns.tolist())}")
            elif 'Quantity' not in portfolio_df.columns:
                st.sidebar.error("❌ CSV must contain 'Quantity' or 'Shares' column")
                st.sidebar.info(f"Found columns: {', '.join(portfolio_df.columns.tolist())}")
            else:
                # Clean the data
                portfolio_df['Symbol'] = portfolio_df['Symbol'].str.strip().str.upper()
                portfolio_df = portfolio_df[portfolio_df['Symbol'].notna()]
                
                st.session_state.portfolio_data = portfolio_df
                st.sidebar.success(f"✅ Portfolio loaded: {len(portfolio_df)} holdings")
                
                # Display a preview
                st.sidebar.write("**Preview:**")
                st.sidebar.dataframe(portfolio_df.head(3), use_container_width=True)
                
        except Exception as e:
            st.sidebar.error(f"❌ Error reading CSV: {str(e)}")
            st.sidebar.info("Make sure your file is a valid CSV format.")
    
    # CSV Template Download with both naming conventions
    template_col1, template_col2 = st.sidebar.columns(2)
    
    with template_col1:
        if st.button("📥 Template (Ticker)", use_container_width=True):
            sample_data = {
                'Ticker': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
                'Quantity': [10, 5, 3, 8, 2],
                'Purchase_Price': [150.00, 280.00, 2500.00, 3200.00, 800.00],
                'Purchase_Date': ['2023-01-15', '2023-02-10', '2023-03-05', '2023-01-20', '2023-02-28']
            }
            sample_df = pd.DataFrame(sample_data)
            csv_content = sample_df.to_csv(index=False)
            
            st.sidebar.download_button(
                label="⬇️ Download Ticker Template",
                data=csv_content,
                file_name="portfolio_template_ticker.csv",
                mime="text/csv",
                key="download_ticker_template"
            )
    
    with template_col2:
        if st.button("📥 Template (Symbol)", use_container_width=True):
            sample_data = {
                'Symbol': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
                'Quantity': [10, 5, 3, 8, 2],
                'Purchase_Price': [150.00, 280.00, 2500.00, 3200.00, 800.00],
                'Purchase_Date': ['2023-01-15', '2023-02-10', '2023-03-05', '2023-01-20', '2023-02-28']
            }
            sample_df = pd.DataFrame(sample_data)
            csv_content = sample_df.to_csv(index=False)
            
            st.sidebar.download_button(
                label="⬇️ Download Symbol Template",
                data=csv_content,
                file_name="portfolio_template_symbol.csv",
                mime="text/csv",
                key="download_symbol_template"
            )
    
    st.sidebar.markdown("---")
    st.sidebar.header("Mansa Capital Funds")

    bot_catalog_rows = get_bot_catalog_rows()
    MANSA_FUNDS = {row["bot"]: row["fund"] for row in bot_catalog_rows}
    MANSA_STRATEGIES = {row["bot"]: row["strategy"] for row in bot_catalog_rows}

    # Proxy market tickers keep charts functional while the dropdown uses fund names.
    FUND_MARKET_TICKERS = {
        "Titan": "SOUN",
        "Vega": "XRT",
        "Draco": "BIL",
        "Altair": "BOTZ",
        "Procryon": "BTC-USD",
        "Hydra": "XLV",
        "Triton": "IYT",
        "Dione": "VT",
        "Dogon": "VTI",
        "Cephei": "SH",
        "Rigel": "UUP",
        "Orion": "GLD",
        "Rhea": "VNQ",
        "Jupicita": "IWM",
    }

    fund_bots = list(MANSA_FUNDS.keys())

    def format_fund_name(bot_name):
        fund_name = MANSA_FUNDS.get(bot_name, bot_name)
        display_fund_name = fund_name.replace("_", " ")
        return f"{display_fund_name} ({bot_name})"

    selected_fund_bot = st.sidebar.selectbox(
        "Select a Mansa Capital Fund:",
        fund_bots,
        format_func=format_fund_name,
    )
    st.sidebar.caption(f"Strategy: {MANSA_STRATEGIES.get(selected_fund_bot, 'N/A')}")

    selected_market_ticker = FUND_MARKET_TICKERS.get(selected_fund_bot, selected_fund_bot)
    selected_tickers = [selected_market_ticker] if selected_market_ticker else []
    selected_ticker_to_fund = {selected_market_ticker: MANSA_FUNDS.get(selected_fund_bot, selected_fund_bot)}

    # All available market proxies for portfolio-wide fetch compatibility.
    portfolio_tickers = list(FUND_MARKET_TICKERS.values())

    today = date.today()
    five_years_ago = today - timedelta(days=5 * 365)

    from_date, to_date = st.sidebar.date_input(
        "Select date range:",
        value=[five_years_ago, today],
        min_value=date(2000, 1, 1),
        max_value=today,
    )

    if not selected_tickers:
        st.warning("Please select at least one ticker from the sidebar.")
        st.stop()

    if from_date > to_date:
        st.error("Error: Start date must be before end date.")
        st.stop()

    # ==========================================================================
    # Mansa Capital Fund Performance - MOVED HERE from line 576
    # ==========================================================================
    st.markdown("## 📈 Mansa Capital Fund Performance")
    
    # Fetch portfolio data
    portfolio_data = get_yfinance_data(selected_tickers, from_date, to_date)
    if portfolio_data.empty:
        st.warning("No data returned for the selected tickers / date range.")
    else:
        df = portfolio_data.copy()
        df['Daily Change %'] = df.groupby('Ticker')['Price'].pct_change() * 100
        
        # Add Fund Name column
        df['Fund Name'] = df['Ticker'].map(selected_ticker_to_fund).fillna(df['Ticker'])

        st.subheader('Fund Performance Over Time')
        st.line_chart(df, x='Date', y='Price', color='Fund Name')

        st.write("")
        # Format as: Month Day, Year (month spelled out)
        st.subheader(f"Metrics for {to_date.strftime('%B')} {to_date.day}, {to_date.year}")

        # Use metric cards per ticker (in columns)
        cols = st.columns(min(4, len(selected_tickers)))
        for i, ticker in enumerate(selected_tickers):
            col = cols[i % len(cols)]
            with col:
                ticker_data = df[df['Ticker'] == ticker]
                if not ticker_data.empty:
                    first_price = ticker_data['Price'].iloc[0]
                    last_price = ticker_data['Price'].iloc[-1]
                    if pd.notna(first_price) and first_price > 0:
                        growth_pct = ((last_price - first_price) / first_price) * 100
                        delta = f'{growth_pct:.2f}%'
                    else:
                        delta = 'n/a'
                    # Use fund name if available, otherwise ticker
                    display_name = selected_ticker_to_fund.get(ticker, ticker)
                    create_metric_card(f'{display_name}', f'${last_price:,.2f}', delta)
                else:
                    display_name = selected_ticker_to_fund.get(ticker, ticker)
                    create_metric_card(f'{display_name}', 'N/A', 'N/A')

        st.write("")
        st.subheader("Raw Fund Data")

    # Calculate portfolio metrics if CSV uploaded
    portfolio_value, num_assets, num_sectors, value_change = calculate_portfolio_metrics(
        st.session_state.get('portfolio_data')
    )

    # Example top-level metric cards (using real data if available)
    col1, col2, col3 = st.columns(3)

    with col1:
        if portfolio_value is not None:
            value_str = f"${portfolio_value:,.0f}"
            change_str = f"{value_change:+.1f}%" if value_change != 0 else "N/A"
            create_metric_card("Market Value", value_str, change_str)
        else:
            create_metric_card("Market Value", "$125,430", "+12%")

    with col2:
        if num_assets is not None:
            create_metric_card("Asset Allocation", f"{num_assets} Assets", "+2%")
        else:
            create_metric_card("Asset Allocation", "8 Assets", "+2%")

    with col3:
        if num_sectors is not None:
            create_metric_card("Sector Allocation", f"{num_sectors} Sectors", "+1%")
        else:
            create_metric_card("Sector Allocation", "5 Sectors", "+1%")

    # Portfolio Overview Section (if CSV uploaded)
    if st.session_state.get('portfolio_data') is not None:
        st.markdown("### 📊 Your Portfolio Overview")
        portfolio_df = st.session_state.portfolio_data
        
        # Display portfolio table
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**Holdings:**")
            display_df = portfolio_df.copy()
            
            # Add current value if we have current prices
            if YFINANCE_AVAILABLE:
                current_values = []
                for _, row in display_df.iterrows():
                    symbol = row['Symbol']
                    quantity = row.get('Quantity', 0)
                    try:
                        ticker = yf.Ticker(symbol)
                        info = ticker.info
                        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                        current_value = quantity * current_price
                        current_values.append(f"${current_value:,.2f}")
                    except:
                        current_values.append("N/A")
                
                display_df['Current Value'] = current_values
            
            st.dataframe(display_df, use_container_width=True)
        
        with col2:
            st.markdown("**Portfolio Summary:**")
            total_holdings = len(portfolio_df)
            total_shares = portfolio_df['Quantity'].sum() if 'Quantity' in portfolio_df.columns else 0
            
            st.metric("Total Holdings", total_holdings)
            st.metric("Total Shares", f"{total_shares:,.0f}")
            
            if 'Purchase_Price' in portfolio_df.columns:
                avg_purchase = portfolio_df['Purchase_Price'].mean()
                st.metric("Avg Purchase Price", f"${avg_purchase:.2f}")
        
        # OHLC Chart with Volume for Portfolio Tickers
        st.markdown("---")
        st.markdown("### 📈 Portfolio Holdings - Price & Volume Analysis")
        
        # Get unique symbols from uploaded CSV
        csv_symbols = portfolio_df['Symbol'].unique().tolist()
        
        if csv_symbols and YFINANCE_AVAILABLE:
            # Let user select which ticker to view
            selected_csv_ticker = st.selectbox(
                "Select a ticker to view OHLC chart:",
                csv_symbols,
                key="csv_ticker_selector"
            )
            
            # Date range for OHLC data (default: last 90 days)
            today_ohlc = date.today()
            ninety_days_ago = today_ohlc - timedelta(days=90)
            
            ohlc_col1, ohlc_col2 = st.columns(2)
            with ohlc_col1:
                ohlc_start_date = st.date_input(
                    "Start Date",
                    value=ninety_days_ago,
                    max_value=today_ohlc,
                    key="ohlc_start"
                )
            with ohlc_col2:
                ohlc_end_date = st.date_input(
                    "End Date",
                    value=today_ohlc,
                    max_value=today_ohlc,
                    key="ohlc_end"
                )
            
            if selected_csv_ticker:
                try:
                    # Fetch OHLC data with hourly intervals
                    ticker_obj = yf.Ticker(selected_csv_ticker)
                    
                    # For hourly data, use period-based approach for recent data
                    if (ohlc_end_date - ohlc_start_date).days <= 7:
                        # Last 7 days - use 1 hour interval
                        ohlc_df = ticker_obj.history(period="7d", interval="1h")
                    elif (ohlc_end_date - ohlc_start_date).days <= 60:
                        # Last 60 days - use 1 day interval
                        ohlc_df = ticker_obj.history(start=ohlc_start_date, end=ohlc_end_date, interval="1d")
                    else:
                        # Longer periods - use daily data
                        ohlc_df = ticker_obj.history(start=ohlc_start_date, end=ohlc_end_date, interval="1d")
                    
                    if not ohlc_df.empty:
                        # Import plotly for candlestick chart
                        import plotly.graph_objects as go
                        from plotly.subplots import make_subplots
                        
                        # Create subplots: candlestick on top, volume on bottom
                        fig = make_subplots(
                            rows=2, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.03,
                            subplot_titles=(f'{selected_csv_ticker} Price', 'Volume'),
                            row_heights=[0.7, 0.3]
                        )
                        
                        # Add candlestick chart
                        fig.add_trace(
                            go.Candlestick(
                                x=ohlc_df.index,
                                open=ohlc_df['Open'],
                                high=ohlc_df['High'],
                                low=ohlc_df['Low'],
                                close=ohlc_df['Close'],
                                name='OHLC'
                            ),
                            row=1, col=1
                        )
                        
                        # Add volume bars
                        colors = ['red' if ohlc_df['Close'].iloc[i] < ohlc_df['Open'].iloc[i] 
                                 else 'green' for i in range(len(ohlc_df))]
                        
                        fig.add_trace(
                            go.Bar(
                                x=ohlc_df.index,
                                y=ohlc_df['Volume'],
                                name='Volume',
                                marker_color=colors,
                                showlegend=False
                            ),
                            row=2, col=1
                        )
                        
                        # Update layout
                        fig.update_layout(
                            title=f'{selected_csv_ticker} - OHLC Chart with Volume',
                            yaxis_title='Price ($)',
                            yaxis2_title='Volume',
                            xaxis_rangeslider_visible=False,
                            height=700,
                            template='plotly_dark',
                            hovermode='x unified'
                        )
                        
                        # Display the chart
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show current stats
                        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
                        
                        with info_col1:
                            st.metric("Current Price", f"${ohlc_df['Close'].iloc[-1]:.2f}")
                        with info_col2:
                            day_change = ohlc_df['Close'].iloc[-1] - ohlc_df['Open'].iloc[-1]
                            day_change_pct = (day_change / ohlc_df['Open'].iloc[-1]) * 100
                            st.metric("Day Change", f"${day_change:.2f}", f"{day_change_pct:+.2f}%")
                        with info_col3:
                            st.metric("Volume", f"{ohlc_df['Volume'].iloc[-1]:,.0f}")
                        with info_col4:
                            avg_volume = ohlc_df['Volume'].mean()
                            st.metric("Avg Volume", f"{avg_volume:,.0f}")
                        
                    else:
                        st.warning(f"No OHLC data available for {selected_csv_ticker} in the selected date range.")
                        
                except Exception as e:
                    st.error(f"Error fetching OHLC data for {selected_csv_ticker}: {str(e)}")
        else:
            st.info("📄 Upload a portfolio CSV to view OHLC charts for your holdings.")
        
        st.markdown("---")

    # Footer
    add_footer()


if __name__ == "__main__":
    main()
