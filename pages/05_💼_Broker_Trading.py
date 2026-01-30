"""
Broker Trading Dashboard
Monitor positions and execute trades across Webull, IBKR, and Binance
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from frontend.utils.rbac import RBACManager, Permission, show_login_form, show_user_info, show_permission_denied

# Load environment variables - use explicit path for local development
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
# Note: Streamlit Cloud uses st.secrets instead of .env

# Import color scheme and styling from home page
try:
    from frontend.styles.colors import COLOR_SCHEME
    from frontend.utils.styling import apply_custom_styling
    
    # Apply home page styling first
    apply_custom_styling()
    RBACManager.init_session_state()
    show_user_info()
    if not RBACManager.is_authenticated():
        st.error("🔐 Authentication Required")
        show_login_form()
        st.stop()
    if not RBACManager.has_permission(Permission.VIEW_BROKER_TRADING):
        show_permission_denied("INVESTOR role with KYC + legal documents")
        st.stop()
    user = RBACManager.get_current_user()
    if not (user and user.kyc_completed and user.investment_agreement_signed):
        st.warning("⚠️ KYC and investment agreement required")
        st.stop()
    # Hide admin-only pages 6–8 from sidebar for non-ADMIN users
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
    
    # Add page-specific enhancements
    st.markdown(f"""
    <style>
    /* CRITICAL: Force Streamlit metrics to match home page visibility */
    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] * {{
        color: rgba(230, 238, 248, 0.9) !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }}
    
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {{
        color: {COLOR_SCHEME['text']} !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }}
    
    [data-testid="stMetricDelta"],
    [data-testid="stMetricDelta"] * {{
        color: rgba(230, 238, 248, 0.9) !important;
        opacity: 0.9 !important;
    }}
    
    /* Force all input labels to be visible - match home page */
    label, .stSelectbox label, .stMultiSelect label, .stTextInput label,
    .stNumberInput label, .stDateInput label, .stTimeInput label,
    .stTextArea label, .stCheckbox label, .stRadio label,
    .stSlider label, .stFileUploader label,
    div[data-baseweb="select"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stSelectbox"] > label,
    .row-widget label {{
        color: {COLOR_SCHEME['text']} !important;
        font-weight: 500 !important;
    }}
    
    /* Headers and text */
    h1, h2, h3, h4, h5, h6, p, span, div {{
        color: {COLOR_SCHEME['text']} !important;
    }}

    /* DROPDOWN MENU OPTIONS - Ensure visibility */
    [data-baseweb="popover"],
    [data-baseweb="menu"] {{
        background-color: {COLOR_SCHEME['secondary']} !important;
    }}
    
    [data-baseweb="menu"] li,
    [role="option"] {{
        background-color: {COLOR_SCHEME['secondary']} !important;
        color: {COLOR_SCHEME['text']} !important;
    }}
    
    [data-baseweb="menu"] li:hover,
    [role="option"]:hover {{
        background-color: rgba(6, 182, 212, 0.2) !important;
        color: {COLOR_SCHEME['text']} !important;
    }}

    /* Sidebar styling - prevent color changes */
    [data-testid="stSidebar"] {{
        background-color: {COLOR_SCHEME['secondary']} !important;
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
    
except ImportError:
    # Fallback if frontend modules not available
    st.warning("⚠️ Styling modules not found. Using fallback styles.")

# Add bbbot1_pipeline to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import broker connectors
try:
    from frontend.components.alpaca_connector import AlpacaConnector
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False

try:
    from frontend.utils.mt5_connector import MT5Connector
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

try:
    from frontend.utils.ibkr_connector import IBKRConnector
    IBKR_AVAILABLE = True
except ImportError:
    IBKR_AVAILABLE = False

try:
    from bbbot1_pipeline.broker_api import (
        execute_trade, 
        get_all_positions,
        WebullClient,
        IBKRClient,
        BinanceClient
    )
    BROKER_API_AVAILABLE = True
except ImportError as e:
    # Broker APIs not available in cloud deployment
    BROKER_API_AVAILABLE = False
    BROKER_IMPORT_ERROR = str(e)


def test_alpaca_connection():
    """Test Alpaca connection and display status"""
    st.subheader("🧪 Test Alpaca Connection")
    
    # Use the unified secrets helper for consistent credential retrieval
    try:
        from frontend.utils.secrets_helper import get_alpaca_config
        config = get_alpaca_config()
        api_key = config['api_key']
        secret_key = config['secret_key']
        paper = config['paper']
        source = "Unified Secrets Helper"
    except ValueError as e:
        # Credentials not configured
        st.error(f"❌ {str(e)}")
        return
    except ImportError:
        # Fallback to manual retrieval if helper not available
        try:
            api_key = st.secrets.get("ALPACA_API_KEY", "")
            secret_key = st.secrets.get("ALPACA_SECRET_KEY", "")
            paper = st.secrets.get("ALPACA_PAPER", "true")
            source = "Streamlit Secrets"
        except (AttributeError, FileNotFoundError):
            api_key = os.getenv("ALPACA_API_KEY", "")
            secret_key = os.getenv("ALPACA_SECRET_KEY", "")
            paper = os.getenv("ALPACA_PAPER", "true")
            source = "Environment Variables (.env)"
        paper = str(paper).lower() == "true"
    
    # Show configuration source
    st.caption(f"📋 Configuration source: {source}")
    
    # Debug info (can be removed after testing)
    with st.expander("🔍 Debug Information"):
        env_path = Path(__file__).parent.parent / '.env'
        st.code(f"""
Environment: {'Streamlit Cloud' if '/mount/src/' in str(Path.cwd()) else 'Local Development'}
Current directory: {os.getcwd()}
.env path: {env_path}
.env exists: {env_path.exists()}
API Key loaded: {bool(api_key)} ({api_key[:10]}... if available)
Secret Key loaded: {bool(secret_key)} ({secret_key[:10]}... if available)
Configuration source: {source}
        """)
    
    if not api_key or not secret_key:
        st.error("❌ Alpaca credentials not configured")
        
        # Show appropriate instructions based on environment
        if '/mount/src/' in str(Path.cwd()):
            # Streamlit Cloud
            st.warning("🌐 **Streamlit Cloud Detected**")
            st.info("""
            **To add credentials in Streamlit Cloud:**
            
            1. Go to your app dashboard: https://share.streamlit.io/
            2. Click on your app
            3. Click "Settings" → "Secrets"
            4. Add the following:
            
            ```toml
            ALPACA_API_KEY = "your_key_here"
            ALPACA_SECRET_KEY = "your_secret_here"
            ALPACA_PAPER = "true"
            ```
            
            5. Click "Save" and the app will automatically restart
            """)
        else:
            # Local development
            st.info("💻 **Local Development Detected**")
            st.code("""
# Add to .env file:
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
ALPACA_PAPER=true
            """)
        return
    
    with st.spinner("Testing Alpaca connection..."):
        try:
            from frontend.components.alpaca_connector import AlpacaConnector
            
            alpaca = AlpacaConnector(api_key, secret_key, paper)
            account = alpaca.get_account()
            
            if account:
                st.success("✅ Alpaca Connected!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Portfolio Value", f"${float(account.get('portfolio_value', 0)):,.2f}")
                with col2:
                    st.metric("Buying Power", f"${float(account.get('buying_power', 0)):,.2f}")
                with col3:
                    st.metric("Cash", f"${float(account.get('cash', 0)):,.2f}")
                
                trading_blocked = account.get('trading_blocked', False)
                account_blocked = account.get('account_blocked', False)
                
                if not trading_blocked and not account_blocked:
                    st.success("🟢 Ready to Trade!")
                else:
                    st.warning("⚠️ Trading Restricted")
                
                st.session_state.alpaca_connected = True
                st.session_state.alpaca = alpaca
            else:
                st.error("❌ Failed to retrieve account information")
                st.warning("**Troubleshooting:**")
                st.info("""
                - Check that your Alpaca API key is valid
                - Verify API key is for Paper Trading (not live)
                - Ensure account is funded with $0.01+ (paper trading)
                - Check Alpaca dashboard: https://app.alpaca.markets/
                """)
        except Exception as e:
            st.error(f"❌ Connection failed: {e}")
            st.warning("**Check these:**")
            st.code(f"""
            - API Key: {api_key[:8] if api_key else 'NOT SET'}...
            - Secret Key: {secret_key[:8] if secret_key else 'NOT SET'}...
            - Paper Trading: {paper}
            - Error: {str(e)}
            """)


def main():
    st.set_page_config(
        page_title="Broker Trading Dashboard",
        page_icon="💼",
        layout="wide"
    )
    
    st.title("💼 Multi-Broker Trading Dashboard")
    st.markdown("---")
    
    # Connection Status Section
    st.header("🔗 Broker Connections")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        alpaca_status = "🟢 Connected" if st.session_state.get('alpaca_connected') else "🔴 Disconnected"
        st.metric("Alpaca (Stocks/Crypto)", alpaca_status)
        if st.button("Test Alpaca", key="test_alpaca_main"):
            test_alpaca_connection()
    
    with col2:
        mt5_status = "🟢 Connected" if st.session_state.get('mt5_connected') else "🔴 Disconnected"
        st.metric("MT5 (FOREX/Futures)", mt5_status)
    
    with col3:
        ibkr_status = "🟢 Connected" if st.session_state.get('ibkr_connected') else "🔴 Disconnected"
        st.metric("IBKR (Multi-Asset)", ibkr_status)
    
    with col4:
        st.metric("Future Brokers", "🔜 Coming Soon")
        st.caption("QuantConnect, TD Ameritrade, NinjaTrader, Binance")
    
    st.markdown("---")
    
    if not BROKER_API_AVAILABLE:
        st.warning("🌐 **Cloud Deployment Mode**: Broker trading APIs are available in local development only.")
        st.info("""
        This feature requires local installation with broker API packages:
        ```bash
        pip install -r requirements-local.txt
        ```
        
        **Available locally:**
        - Webull (Equities & ETFs)
        - Interactive Brokers (Forex, Futures, Commodities)
        - Binance (Cryptocurrency)
        
        **For more information**, see [Broker Trading Setup Guide](https://github.com/winstonwilliamsiii/BBBot/blob/main/docs/BROKER_TRADING_SETUP.md)
        """)
        
        st.markdown("---")
        st.subheader("📊 Portfolio Analytics (Cloud)")
        st.info("Showing read-only portfolio analytics. For live trading, run locally.")
        return
    
    # Sidebar - Trade Execution
    with st.sidebar:
        st.header("🎯 Execute Trade")
        
        broker = st.selectbox(
            "Broker",
            ["webull", "ibkr", "binance"],
            help="Webull: Equities/ETFs | IBKR: Forex/Futures | Binance: Crypto"
        )
        
        symbol = st.text_input(
            "Symbol",
            value="AAPL" if broker == "webull" else "BTCUSDT" if broker == "binance" else "ES"
        )
        
        side = st.radio("Side", ["BUY", "SELL"])
        
        quantity = st.number_input(
            "Quantity",
            min_value=0.0001,
            value=1.0 if broker != "binance" else 0.001,
            step=0.0001 if broker == "binance" else 1.0
        )
        
        # Advanced options for IBKR
        if broker == "ibkr":
            st.subheader("IBKR Options")
            sec_type = st.selectbox("Security Type", ["FUT", "CASH", "CMDTY"])
            exchange = st.text_input("Exchange", value="CME")
        
        if st.button("🚀 Execute Trade", type="primary"):
            with st.spinner(f"Placing {side} order on {broker.upper()}..."):
                try:
                    if broker == "ibkr":
                        result = execute_trade(
                            broker, symbol, side, quantity,
                            sec_type=sec_type, exchange=exchange
                        )
                    else:
                        result = execute_trade(broker, symbol, side, quantity)
                    
                    if "error" in result:
                        st.error(f"❌ Trade failed: {result['error']}")
                    else:
                        st.success(f"✅ Trade executed successfully!")
                        st.json(result)
                
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        st.markdown("---")
        st.caption("⚠️ Ensure broker APIs are configured in .env file")
    
    # Main content - Positions across all brokers
    st.header("📊 Current Positions")
    
    col1, col2, col3 = st.columns(3)
    
    # Fetch all positions
    if st.button("🔄 Refresh Positions", key="refresh"):
        with st.spinner("Fetching positions from all brokers..."):
            try:
                all_positions = get_all_positions()
                st.session_state.positions = all_positions
                st.session_state.last_refresh = datetime.now()
            except Exception as e:
                st.error(f"Failed to fetch positions: {e}")
    
    # Display positions
    if "positions" in st.session_state:
        positions = st.session_state.positions
        
        # Webull positions
        with col1:
            st.subheader("💼 Webull (Equities/ETFs)")
            webull_positions = positions.get('webull', [])
            
            if webull_positions and isinstance(webull_positions, list) and len(webull_positions) > 0:
                # Convert to DataFrame if not already
                if isinstance(webull_positions[0], dict):
                    df_webull = pd.DataFrame(webull_positions)
                    st.dataframe(df_webull, use_container_width=True)
                else:
                    st.info("No Webull positions")
            else:
                st.info("No Webull positions")
        
        # IBKR positions
        with col2:
            st.subheader("🌐 IBKR (Forex/Futures)")
            ibkr_positions = positions.get('ibkr', [])
            
            if ibkr_positions and len(ibkr_positions) > 0:
                df_ibkr = pd.DataFrame(ibkr_positions)
                st.dataframe(df_ibkr, use_container_width=True)
            else:
                st.info("No IBKR positions")
                st.caption("Note: IBKR positions require async callback handling")
        
        # Binance positions
        with col3:
            st.subheader("₿ Binance (Crypto)")
            binance_positions = positions.get('binance', [])
            
            if binance_positions and len(binance_positions) > 0:
                df_binance = pd.DataFrame(binance_positions)
                # Filter to show only non-zero balances
                df_binance['total'] = df_binance['free'].astype(float) + df_binance['locked'].astype(float)
                df_binance = df_binance[df_binance['total'] > 0]
                st.dataframe(df_binance[['asset', 'free', 'locked', 'total']], use_container_width=True)
            else:
                st.info("No Binance balances")
        
        # Last refresh time
        if "last_refresh" in st.session_state:
            st.caption(f"Last refreshed: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
    
    else:
        st.info("👆 Click 'Refresh Positions' to load broker data")
    
    # Trade History Section
    st.markdown("---")
    st.header("📜 Recent Trade History")
    
    # In production, load from database
    st.info("Trade history tracking coming soon - will integrate with MLFlow experiments")
    
    # Trading signals from ML pipeline
    st.markdown("---")
    st.header("🤖 ML Trading Signals")
    
    try:
        # Connect to MySQL using unified secrets helper (avoids hardcoded bbbot1)
        from sqlalchemy import create_engine, inspect
        from frontend.utils.secrets_helper import get_mysql_config, get_mysql_url

        # IMPORTANT: For trading signals, we need to use the 'bbbot1' database
        mysql_config = get_mysql_config(database='bbbot1')
        connection_string = get_mysql_url(database='bbbot1')
        engine = create_engine(connection_string)

        inspector = inspect(engine)
        schema_names = inspector.get_schema_names()
        has_marts_schema = 'marts' in schema_names

        if has_marts_schema:
            table_exists = 'features_roi' in inspector.get_table_names(schema='marts')
            table_ref = 'marts.features_roi'
        else:
            table_exists = 'features_roi' in inspector.get_table_names()
            table_ref = 'features_roi'

        if not table_exists:
            st.warning("⚠️ Trading signals table not found in database.")
            st.info("The 'features_roi' table will be created once the ML pipeline runs. Showing demo signals for now.")
            sample_signals = pd.DataFrame({
                'ticker': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
                'signal_date': pd.to_datetime(['2026-01-28'] * 5),
                'price': [189.32, 408.12, 152.44, 176.83, 232.19],
                'rsi_14': [48.2, 72.1, 51.4, 29.6, 68.3],
                'macd': [0.42, -0.11, 0.05, 0.31, -0.09],
                'macd_signal': [0.38, -0.05, 0.02, 0.29, -0.06],
                'sentiment_score': [0.12, -0.04, 0.08, 0.21, -0.02],
                'trade_signal': ['HOLD', 'SELL', 'HOLD', 'BUY', 'HOLD'],
            })
            df_signals = sample_signals
        else:
            query = f"""
            SELECT 
                ticker,
                date as signal_date,
                close as price,
                rsi_14,
                macd,
                macd_signal,
                sentiment_score,
                CASE 
                    WHEN rsi_14 < 30 AND macd > macd_signal THEN 'BUY'
                    WHEN rsi_14 > 70 AND macd < macd_signal THEN 'SELL'
                    ELSE 'HOLD'
                END as trade_signal
            FROM {table_ref}
            WHERE date = (SELECT MAX(date) FROM {table_ref})
            ORDER BY ticker
            LIMIT 20;
            """

            df_signals = pd.read_sql(query, engine)

        engine.dispose()

        if not df_signals.empty:
            # Color code signals
            def highlight_signal(val):
                if val == 'BUY':
                    return 'background-color: #90EE90'
                elif val == 'SELL':
                    return 'background-color: #FFB6C1'
                else:
                    return ''
            
            styled_df = df_signals.style.applymap(
                highlight_signal,
                subset=['trade_signal']
            )
            
            st.dataframe(styled_df, use_container_width=True)
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("🟢 BUY Signals", (df_signals['trade_signal'] == 'BUY').sum())
            col2.metric("🔴 SELL Signals", (df_signals['trade_signal'] == 'SELL').sum())
            col3.metric("⚪ HOLD Signals", (df_signals['trade_signal'] == 'HOLD').sum())
        
        else:
            st.info("No trading signals available. Run the ML pipeline first.")
    
    except Exception as e:
        db_name = mysql_config.get('database', 'unknown') if 'mysql_config' in locals() else 'unknown'
        db_host = mysql_config.get('host', 'unknown') if 'mysql_config' in locals() else 'unknown'
        
        # Check if it's a connection error
        error_str = str(e)
        if "Can't connect" in error_str or "Connection refused" in error_str:
            st.warning("⚠️ **Database Connection Failed**")
            st.info(f"Trying to connect to: `{db_name}` on `{db_host}`")
            
            with st.expander("🔧 How to Fix This"):
                st.markdown(f"""
                ### Database Connection Error
                
                **Current Configuration:**
                - Database: `{db_name}`
                - Host: `{db_host}`
                
                **Solutions:**
                
                #### Option 1: Use Railway MySQL (Recommended for Production)
                Add these secrets to your Streamlit Cloud or `.env` file:
                ```toml
                MYSQL_HOST = "nozomi.proxy.rlwy.net"
                MYSQL_PORT = "54537"
                MYSQL_USER = "root"
                MYSQL_PASSWORD = "your_railway_password"
                MYSQL_DATABASE = "railway"
                ```
                
                #### Option 2: Start Local MySQL (Development)
                ```bash
                docker-compose up -d mysql
                ```
                
                #### Option 3: Check Environment Variables
                Make sure these are set in your `.env` or Streamlit secrets:
                - `MYSQL_HOST`
                - `MYSQL_PORT`
                - `MYSQL_USER`
                - `MYSQL_PASSWORD`
                - `MYSQL_DATABASE`
                """)
        elif "Unknown database" in error_str or "1049" in error_str:
            st.error(f"❌ Database not found: **{db_name}** on {db_host}")
            st.warning("**The database doesn't exist on the server.**")
            st.info(f"""
            ✅ **Fix:** The database name has been automatically corrected to use **'bbbot1'** which contains the trading signals.
            
            **Note:** Your database configuration maps:
            - `mansa_bot` → `bbbot1` (on Railway production)
            - `railway` → `bbbot1` (on Railway production)
            - Local database stays as configured
            
            If this persists, check that the Railway MySQL server is running and the connection credentials are correct.
            """)
        else:
            st.error(f"Failed to load trading signals (database: {db_name}): {e}")
            st.info("Make sure `marts.features_roi` table exists and has data")
    
    # Configuration Guide
    with st.expander("⚙️ Broker API Configuration Guide"):
        st.markdown("""
        ### Setup Instructions
        
        #### 1. Webull (Equities & ETFs)
        ```bash
        pip install webull
        ```
        Add to `.env`:
        ```
        WEBULL_USERNAME=your_email@example.com
        WEBULL_PASSWORD=your_password
        WEBULL_DEVICE_ID=your_device_id
        ```
        
        #### 2. Interactive Brokers (Forex/Futures/Commodities)
        ```bash
        pip install ibapi
        ```
        - Download TWS or IB Gateway
        - Enable API connections in settings
        - Set socket port (7497 for paper, 7496 for live)
        
        Add to `.env`:
        ```
        IBKR_HOST=127.0.0.1
        IBKR_PORT=7497
        IBKR_CLIENT_ID=1
        ```
        
        #### 3. Binance (Cryptocurrency)
        ```bash
        pip install python-binance
        ```
        - Create API key at binance.com
        - Enable spot trading permissions
        
        Add to `.env`:
        ```
        BINANCE_API_KEY=your_api_key
        BINANCE_API_SECRET=your_secret
        BINANCE_TESTNET=true  # Use testnet for testing
        ```
        
        #### 4. Test Configuration
        ```bash
        python bbbot1_pipeline/broker_api.py
        ```
        """)


if __name__ == "__main__":
    main()
