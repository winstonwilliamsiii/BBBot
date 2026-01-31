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

    # Try connecting with database; if it fails, create it
    try:
        conn = mysql.connector.connect(**config)
    except Exception:
        base_config = dict(config)
        base_config.pop("database", None)
        conn = mysql.connector.connect(**base_config)
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        conn.close()
        config["database"] = db_name
        conn = mysql.connector.connect(**config)

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

    st.subheader("📊 Featured Trading Bots")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        create_metric_card("RSI-MACD Strategy", "+24.3% YTD", "Win Rate 68%")
    with col_b2:
        create_metric_card("Mean Reversion Alpha", "+18.7% YTD", "Win Rate 61%")

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
    # Economic Calendar & Market Data Section
    # ==========================================================================
    if ECONOMIC_CALENDAR_AVAILABLE:
        st.markdown("## 📊 Markets & Economics")
        widget = get_calendar_widget()
        widget.render_full_dashboard()
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

    st.sidebar.header("Portfolio Data Upload")
    
    # Option to upload a full portfolio CSV
    st.sidebar.subheader("📄 Upload Portfolio CSV")
    
    # Add information about CSV format
    with st.sidebar.expander("ℹ️ CSV Format Help"):
        st.write("""
        **Required columns:**
        - `Symbol`: Stock ticker (e.g., AAPL, MSFT)
        - `Quantity`: Number of shares owned
        
        **Optional columns:**
        - `Purchase_Price`: Price paid per share
        - `Purchase_Date`: Date purchased (YYYY-MM-DD)
        - `Current_Price`: Current price per share
        """)
    
    portfolio_csv = st.sidebar.file_uploader(
        "Upload your portfolio data (CSV)",
        type=["csv"],
        help="CSV should contain columns: Symbol, Quantity, Purchase_Price (optional: Purchase_Date, Current_Price)"
    )
    
    # Initialize portfolio_data in session state if not exists
    if 'portfolio_data' not in st.session_state:
        st.session_state.portfolio_data = None
        
    if portfolio_csv is not None:
        try:
            # Read the uploaded CSV
            portfolio_df = pd.read_csv(portfolio_csv)
            
            # Validate required columns
            required_cols = ['Symbol', 'Quantity']
            if all(col in portfolio_df.columns for col in required_cols):
                st.session_state.portfolio_data = portfolio_df
                st.sidebar.success(f"✅ Portfolio loaded: {len(portfolio_df)} holdings")
                
                # Display a preview
                st.sidebar.write("**Preview:**")
                st.sidebar.dataframe(portfolio_df.head(3), use_container_width=True)
            else:
                st.sidebar.error(f"❌ CSV must contain columns: {', '.join(required_cols)}")
                
        except Exception as e:
            st.sidebar.error(f"❌ Error reading CSV: {str(e)}")
    
    # CSV Template Download
    if st.sidebar.button("📥 Download CSV Template"):
        # Create sample CSV data
        sample_data = {
            'Symbol': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
            'Quantity': [10, 5, 3, 8, 2],
            'Purchase_Price': [150.00, 280.00, 2500.00, 3200.00, 800.00],
            'Purchase_Date': ['2023-01-15', '2023-02-10', '2023-03-05', '2023-01-20', '2023-02-28']
        }
        sample_df = pd.DataFrame(sample_data)
        
        # Convert to CSV
        csv_content = sample_df.to_csv(index=False)
        
        st.sidebar.download_button(
            label="Download portfolio_template.csv",
            data=csv_content,
            file_name="portfolio_template.csv",
            mime="text/csv"
        )
    
    st.sidebar.markdown("---")
    st.sidebar.header("Portfolio Selection")
    # default tickers (fallback)
    default_portfolio_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']

    # Allow user to enter a Yahoo Finance portfolio root page (public portfolios)
    yahoo_root = st.sidebar.text_input(
        "Yahoo portfolios page URL",
        value="https://finance.yahoo.com/portfolio",
        help="Enter a Yahoo Finance portfolio page (for example: https://finance.yahoo.com/portfolio)",
    )

    @st.cache_data
    def _cached_fetch(url: str):
        return fetch_portfolio_list(url)

    portfolios = []
    if yahoo_root:
        portfolios = _cached_fetch(yahoo_root)

    if portfolios:
        # map display names
        names = [p["name"] for p in portfolios]
        selected_portfolio_idx = st.sidebar.selectbox(
            "Choose a Yahoo portfolio:",
            options=list(range(len(names))),
            format_func=lambda i: names[i],
        )
        selected_portfolio = portfolios[selected_portfolio_idx]
        st.sidebar.markdown(f"**Selected:** [{selected_portfolio['name']}]({selected_portfolio['url']})")

        # Try to fetch tickers from the selected portfolio and use them as the
        # available portfolio_tickers for the multiselect below.
        @st.cache_data
        def _cached_fetch_holdings(url: str):
            try:
                return fetch_portfolio_tickers(url)
            except Exception:
                return []

        fetched_tickers = _cached_fetch_holdings(selected_portfolio["url"])
        if fetched_tickers:
            portfolio_tickers = fetched_tickers
            st.sidebar.success(f"Loaded {len(fetched_tickers)} tickers from portfolio")
        else:
            portfolio_tickers = default_portfolio_tickers
            st.sidebar.info("Could not extract holdings from selected portfolio; using default tickers.")
    else:
        st.sidebar.info("No portfolios found on the provided URL. Enter a different Yahoo portfolio page or ensure the page is public.")
        portfolio_tickers = default_portfolio_tickers
        # Provide fallback inputs: allow user to paste tickers or upload a CSV
        pasted = st.sidebar.text_area("Paste tickers (comma or whitespace separated)", value="")
        uploaded = st.sidebar.file_uploader("Or upload a CSV/ TXT with tickers (one per line)", type=["csv", "txt"])
        if uploaded is not None:
            try:
                content = uploaded.read().decode('utf-8')
                lines = [ln.strip() for ln in content.replace(',','\n').splitlines() if ln.strip()]
                if lines:
                    portfolio_tickers = lines
                    st.sidebar.success(f"Loaded {len(lines)} tickers from uploaded file")
            except Exception:
                st.sidebar.error("Failed to read uploaded file; please ensure it's plain text or CSV with tickers.")
        elif pasted:
            parsed = [t.strip().upper() for t in re.split(r"[\s,]+", pasted) if t.strip()]
            if parsed:
                portfolio_tickers = parsed
                st.sidebar.success(f"Loaded {len(parsed)} tickers from paste")
    
    # Define default tickers that should always be available
    default_portfolio_tickers_fallback = ['IONQ', 'QBTS', 'SOUN', 'RGTI']
    
    # Ensure portfolio_tickers is not empty
    if not portfolio_tickers:
        portfolio_tickers = default_portfolio_tickers_fallback
    
    # Default selection: filter to only include tickers that exist in portfolio_tickers
    default_selection_candidates = ['IONQ', 'QBTS', 'SOUN', 'RGTI']
    default_selection = [t for t in default_selection_candidates if t in portfolio_tickers]
    
    # If no defaults match, use first few from portfolio_tickers
    if not default_selection and portfolio_tickers:
        default_selection = portfolio_tickers[:min(4, len(portfolio_tickers))]
    
    # Mansa Capital Fund Names for display
    MANSA_FUNDS = {
        'IONQ': 'Mansa AI',
        'QBTS': 'Mansa AI2',
        'SOUN': 'Mansa Tech',
        'RGTI': 'Mansa Jugarnaut',
        'AMZN': 'Mansa Jugarnaut',
        'NVDA': 'Mansa Jugarnaut',
        'B': 'Mansa Minerals',
        'IAU': 'Mansa Minerals'
    }
    
    # Create ticker labels with fund names
    def format_ticker(ticker):
        if ticker in MANSA_FUNDS:
            return f"{MANSA_FUNDS[ticker]} ({ticker})"
        return ticker

    selected_tickers = st.sidebar.multiselect(
        'Select Mansa Capital Funds:',
        portfolio_tickers,
        default_selection,
        format_func=format_ticker
    )

    # Optional: give user a way to validate tickers via yfinance (best-effort)
    if st.sidebar.button("Validate selected tickers"):
        if not YFINANCE_AVAILABLE:
            st.sidebar.error("yfinance not installed; cannot validate tickers.")
        else:
            invalid = []
            valid = []
            max_check = 20
            to_check = selected_tickers[:max_check]
            progress = st.sidebar.progress(0)
            for i, sym in enumerate(to_check):
                try:
                    t = yf.Ticker(sym)
                    info = t.info
                    # heuristic: valid if info contains a longName or regularMarketPrice
                    if info and (info.get('longName') or info.get('regularMarketPrice') is not None):
                        valid.append(sym)
                    else:
                        invalid.append(sym)
                except Exception:
                    invalid.append(sym)
                progress.progress(int((i + 1) / len(to_check) * 100))
            progress.empty()
            st.sidebar.write(f"Valid: {valid}")
            if invalid:
                st.sidebar.warning(f"Possibly invalid or not-found tickers (first {max_check} checked): {invalid}")

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

    # Bot status card - positioned above portfolio metrics
    create_custom_card(
        "Bot Status",
        "All systems operational. Bot is responding normally to user queries.",
    )

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

    # Fetch portfolio data
    portfolio_data = get_yfinance_data(selected_tickers, from_date, to_date)
    if portfolio_data.empty:
        st.warning("No data returned for the selected tickers / date range.")
    else:
        df = portfolio_data.copy()
        df['Daily Change %'] = df.groupby('Ticker')['Price'].pct_change() * 100
        
        # Add Fund Name column
        df['Fund Name'] = df['Ticker'].map(MANSA_FUNDS).fillna(df['Ticker'])

        st.header('Mansa Capital Fund Performance Over Time')
        st.line_chart(df, x='Date', y='Price', color='Fund Name')

        st.write("")
        # Format as: Month Day, Year (month spelled out)
        st.header(f"Metrics for {to_date.strftime('%B')} {to_date.day}, {to_date.year}")

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
                    display_name = MANSA_FUNDS.get(ticker, ticker)
                    create_metric_card(f'{display_name}', f'${last_price:,.2f}', delta)
                else:
                    display_name = MANSA_FUNDS.get(ticker, ticker)
                    create_metric_card(f'{display_name}', 'N/A', 'N/A')

        st.write("")
        st.header("Raw Portfolio Data")
        st.dataframe(df, use_container_width=True)

    # Footer
    add_footer()


if __name__ == "__main__":
    main()
