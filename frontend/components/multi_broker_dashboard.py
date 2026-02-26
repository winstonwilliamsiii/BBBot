"""
Unified Multi-Broker Dashboard
Integrates MT5 (FOREX/Futures), Alpaca (Stocks/Crypto), and IBKR (All Assets)
"""

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# Import connectors
try:
    from frontend.utils.mt5_connector import MT5Connector
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

try:
    from frontend.utils.alpaca_connector import AlpacaConnector
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False

try:
    from frontend.utils.ibkr_connector import IBKRConnector
    IBKR_AVAILABLE = True
except ImportError:
    IBKR_AVAILABLE = False


def render_multi_broker_dashboard():
    """Main multi-broker trading dashboard"""
    
    st.title("🌐 Multi-Broker Trading Hub")
    st.markdown("Manage all your trading accounts in one place")
    from frontend.utils.styling import apply_custom_styling
    apply_custom_styling()
    
    # Initialize session state
    if 'brokers' not in st.session_state:
        st.session_state.brokers = {
            'mt5': None,
            'alpaca': None,
            'ibkr': None
        }
    
    # Broker status overview
    render_broker_status()
    
    st.markdown("---")
    
    # Tabs for each broker
    tabs = st.tabs([
        "🔌 MT5 (FOREX/Futures)",
        "📈 Alpaca (Stocks/Crypto)",
        "🏦 IBKR (Multi-Asset)",
        "📊 Combined View",
        "🤖 ML Trading Signals"
    ])
    
    with tabs[0]:
        render_mt5_section()
    
    with tabs[1]:
        render_alpaca_section()
    
    with tabs[2]:
        render_ibkr_section()
    
    with tabs[3]:
        render_combined_portfolio()

    with tabs[4]:
        render_ml_trading_signals()


def render_broker_status():
    """Display connection status for all brokers"""
    
    st.subheader("🔗 Broker Connections")
    
    col1, col2, col3 = st.columns(3)

    with col1:
        mt5_connected = st.session_state.brokers['mt5'] is not None
        status = "🟢 Connected" if mt5_connected else "🔴 Disconnected"
        st.metric("MT5 (FOREX/Futures)", status)
        if not mt5_connected and MT5_AVAILABLE:
            if st.button("Connect MT5", key="connect_mt5_main_dashboard"):
                connect_mt5()

    with col2:
        alpaca_connected = st.session_state.brokers['alpaca'] is not None
        status = "🟢 Connected" if alpaca_connected else "🔴 Disconnected"
        st.metric("Alpaca (Stocks/Crypto)", status)
        if not alpaca_connected and ALPACA_AVAILABLE:
            if st.button("Connect Alpaca", key="connect_alpaca_main_dashboard"):
                connect_alpaca()

    with col3:
        ibkr_connected = st.session_state.brokers['ibkr'] is not None
        status = "🟢 Connected" if ibkr_connected else "🔴 Disconnected"
        st.metric("IBKR (Multi-Asset)", status)
        if not ibkr_connected and IBKR_AVAILABLE:
            if st.button("Connect IBKR", key="connect_ibkr_main_dashboard"):
                connect_ibkr()

    # Show open Alpaca orders below broker status
    if ALPACA_AVAILABLE and st.session_state.brokers['alpaca'] is not None:
        connector = st.session_state.brokers['alpaca']
        st.subheader("📬 Open Alpaca Orders")
        orders = connector.get_orders(status="open")
        if orders and len(orders) > 0:
            order_data = [{
                'Order ID': o.get('id', '')[:8],
                'Symbol': o.get('symbol', ''),
                'Side': o.get('side', ''),
                'Type': o.get('type', ''),
                'Qty': o.get('qty', ''),
                'Limit Price': o.get('limit_price', ''),
                'Status': o.get('status', ''),
                'Submitted At': o.get('submitted_at', '')
            } for o in orders]
            df_orders = pd.DataFrame(order_data)
            st.dataframe(
                df_orders,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No open orders")


    if not ibkr_connected and IBKR_AVAILABLE:
        if st.button("Connect IBKR", key="connect_ibkr_main"):
            connect_ibkr()


def connect_mt5():
    """Connect to MT5"""
    try:
        from frontend.utils.mt5_connector import MT5Connector
        
        # Use MT5_API_URL or MT5_REST_API_URL (fallback to 8002, not 8000 which is Airbyte)
        default_url = "http://localhost:8002"
        api_url = os.getenv("MT5_API_URL") or os.getenv("MT5_REST_API_URL", default_url)
        connector = MT5Connector(api_url)
        
        if connector.connect(
            user=os.getenv("MT5_USER", ""),
            password=os.getenv("MT5_PASSWORD", ""),
            host=os.getenv("MT5_HOST", ""),
            port=int(os.getenv("MT5_PORT", "443"))
        ):
            st.session_state.brokers['mt5'] = connector
            st.success("✅ MT5 Connected!")
            st.rerun()
        else:
            st.error(
                "❌ MT5 connection failed - Check if MT5 REST server is running"
            )
            st.info("💡 Run: START_MT5_SERVER.bat to start the MT5 API server")
    except Exception as e:
        st.error("❌ MT5 API server is not responding")
        st.info(f"Error details: {e}")
        st.warning(
            "🔧 **Quick Fix:**\n"
            "1. Make sure MT5 desktop is logged in\n"
            "2. Run `START_MT5_SERVER.bat` to start the API bridge\n"
            "3. Try connecting again"
        )


def connect_alpaca():
    """Connect to Alpaca"""
    try:
        from frontend.utils.secrets_helper import get_alpaca_config
        from frontend.components.alpaca_connector import AlpacaConnector
        
        # Use the unified secrets helper for consistent credential retrieval
        try:
            config = get_alpaca_config()
            api_key = config['api_key']
            secret_key = config['secret_key']
            paper = config['paper']
        except ValueError as e:
            st.error(f"❌ {str(e)}")
            st.info("Configure in Streamlit Secrets (Cloud) or .env file (Local)")
            return
        
        connector = AlpacaConnector(api_key, secret_key, paper)
        account = connector.get_account()
        
        if account:
            st.session_state.brokers['alpaca'] = connector
            portfolio_val = float(account['portfolio_value']) if account and 'portfolio_value' in account else 0.0
            st.success(
                f"✅ Alpaca Connected! Portfolio: ${portfolio_val:,.2f}"
            )
            st.rerun()
        else:
            st.error("❌ Alpaca connection failed")
    except Exception as e:
        st.error(f"Alpaca error: {e}")
def connect_ibkr():
    """Connect to IBKR Gateway"""
    try:
        from frontend.utils.ibkr_connector import IBKRConnector
        
        gateway_url = os.getenv("IBKR_GATEWAY_URL", "https://localhost:5000")
        
        connector = IBKRConnector(gateway_url)
        
        if connector.is_authenticated():
            st.session_state.brokers['ibkr'] = connector
            accounts = connector.get_accounts()
            accounts_str = ', '.join(accounts) if accounts else 'None'
            st.success(
                f"✅ IBKR Connected! Accounts: {accounts_str}"
            )
            st.rerun()
        else:
            st.error(
                "❌ IBKR Gateway not authenticated. Make sure Gateway is running."
            )
    except Exception as e:
        st.error(f"IBKR error: {e}")


def render_mt5_section():
    """MT5 trading section"""
    
    if not MT5_AVAILABLE:
        st.error("MT5 connector not available")
        return
    
    connector = st.session_state.brokers.get('mt5')
    
    if not connector:
        st.info(
            "👆 Connect to MT5 to access FOREX and Commodities Futures trading"
        )
        
        with st.expander("🔗 MT5 Connection"):
            col1, col2 = st.columns(2)
            
            with col1:
                user = st.text_input("MT5 Account", value=os.getenv("MT5_USER", ""))
                host = st.text_input("Broker Host", value=os.getenv("MT5_HOST", ""))
            
            with col2:
                password = st.text_input("Password", type="password", value=os.getenv("MT5_PASSWORD", ""))
                port = st.number_input("Port", value=int(os.getenv("MT5_PORT", "443")))
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("Connect", type="primary", use_container_width=True):
                    connect_mt5()
            
            with col_btn2:
                if st.button("🏥 Health Check", use_container_width=True):
                    base_url = os.getenv("MT5_API_URL", "http://localhost:8000")
                    temp_connector = MT5Connector(base_url)
                    if temp_connector.health_check():
                        st.success("✅ MT5 API server is healthy")
                    else:
                        st.error("❌ MT5 API server is not responding")
        return
    
    # Show MT5 account info
    account = connector.get_account_info()
    
    if account:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Balance", f"${account.get('balance', 0):,.2f}")
        with col2:
            st.metric("Equity", f"${account.get('equity', 0):,.2f}")
        with col3:
            st.metric("Free Margin", f"${account.get('free_margin', 0):,.2f}")
        
        # Show positions
        st.subheader("📊 MT5 Positions")
        positions = connector.get_positions()
        
        if positions:
            pos_data = [{
                'Symbol': p.symbol,
                'Type': p.type,
                'Volume': p.volume,
                'Price': p.current_price,
                'Profit': p.profit
            } for p in positions]
            
            st.dataframe(pd.DataFrame(pos_data), use_container_width=True, hide_index=True)
        else:
            st.info("No open positions")


def render_alpaca_section():
    """Alpaca trading section"""
    
    if not ALPACA_AVAILABLE:
        st.error("Alpaca connector not available")
        return
    
    connector = st.session_state.brokers.get('alpaca')
    
    if not connector:
        st.info("👆 Connect to Alpaca to access Stock and Crypto trading")
        
        with st.expander("🔗 Alpaca Connection"):
            api_key = st.text_input("API Key", value=os.getenv("ALPACA_API_KEY", ""), type="password")
            secret_key = st.text_input("Secret Key", value=os.getenv("ALPACA_SECRET_KEY", ""), type="password")
            paper = st.checkbox("Paper Trading", value=True)
            
            if st.button("Connect", type="primary", key="alpaca_connect_btn"):
                connect_alpaca()
        return
    
    # Show Alpaca account info
    account = connector.get_account()
    
    if account:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Portfolio Value", f"${float(account['portfolio_value']):,.2f}")
        with col2:
            st.metric("Cash", f"${float(account['cash']):,.2f}")
        with col3:
            st.metric("Buying Power", f"${float(account['buying_power']):,.2f}")
        with col4:
            equity = float(account['equity'])
            last_equity = float(account['last_equity'])
            change = equity - last_equity
            st.metric("Today's P/L", f"${change:,.2f}", delta=f"{(change/last_equity*100):.2f}%")
        
        # Show positions
        st.subheader("📊 Alpaca Positions")
        positions = connector.get_positions()
        
        if positions:
            pos_data = [{
                'Symbol': p.symbol,
                'Qty': p.qty,
                'Side': p.side,
                'Current Price': f"${p.current_price:.2f}",
                'Avg Entry': f"${p.avg_entry_price:.2f}",
                'Market Value': f"${p.market_value:.2f}",
                'P/L': f"${p.unrealized_pl:.2f}",
                'P/L %': f"{p.unrealized_plpc*100:.2f}%"
            } for p in positions]
            
            st.dataframe(pd.DataFrame(pos_data), use_container_width=True, hide_index=True)
        else:
            st.info("No open positions")


def render_ibkr_section():
    """IBKR trading section"""
    
    if not IBKR_AVAILABLE:
        st.error("IBKR connector not available")
        return
    
    connector = st.session_state.brokers.get('ibkr')
    
    if not connector:
        st.info("👆 Connect to IBKR Gateway to access multi-asset trading")
        st.markdown("""
        **Requirements:**
        1. Install IBKR Gateway or TWS
        2. Start Gateway (default port: 5000)
        3. Configure API settings
        4. Click Connect above
        """)
        return
    
    # Get accounts
    accounts = connector.get_accounts()
    
    if accounts:
        st.success(f"Connected to {len(accounts)} account(s): {', '.join(accounts)}")
        
        selected_account = st.selectbox("Select Account", accounts)
        
        # Show positions
        st.subheader("📊 IBKR Positions")
        positions = connector.get_positions(selected_account)
        
        if positions:
            pos_data = [{
                'Symbol': p.symbol,
                'Position': p.position,
                'Market Value': f"${p.market_value:,.2f}",
                'Avg Cost': f"${p.avg_cost:.2f}",
                'Unrealized P/L': f"${p.unrealized_pnl:,.2f}",
                'Realized P/L': f"${p.realized_pnl:,.2f}"
            } for p in positions]
            
            st.dataframe(pd.DataFrame(pos_data), use_container_width=True, hide_index=True)
        else:
            st.info("No open positions")


def render_combined_portfolio():
    """Combined view of all portfolios"""
    
    st.subheader("📊 Combined Portfolio View")
    
    all_positions = []
    total_value = 0
    total_pnl = 0
    
    # Collect MT5 positions
    if st.session_state.brokers.get('mt5'):
        mt5 = st.session_state.brokers['mt5']
        account = mt5.get_account_info()
        positions = mt5.get_positions()
        
        if account:
            total_value += account.get('equity', 0)
            total_pnl += account.get('equity', 0) - account.get('balance', 0)
        
        if positions:
            for p in positions:
                all_positions.append({
                    'Broker': 'MT5',
                    'Symbol': p.symbol,
                    'Type': 'FOREX/Futures',
                    'Value': f"${abs(p.volume * p.current_price):,.2f}",
                    'P/L': f"${p.profit:.2f}"
                })
    
    # Collect Alpaca positions
    if st.session_state.brokers.get('alpaca'):
        alpaca = st.session_state.brokers['alpaca']
        account = alpaca.get_account()
        positions = alpaca.get_positions()
        
        if account:
            total_value += float(account['portfolio_value'])
            total_pnl += float(account['equity']) - float(account['last_equity'])
        
        if positions:
            for p in positions:
                all_positions.append({
                    'Broker': 'Alpaca',
                    'Symbol': p.symbol,
                    'Type': 'Stock/Crypto',
                    'Value': f"${p.market_value:.2f}",
                    'P/L': f"${p.unrealized_pl:.2f}"
                })
    
    # Collect IBKR positions
    if st.session_state.brokers.get('ibkr'):
        ibkr = st.session_state.brokers['ibkr']
        accounts = ibkr.get_accounts()
        
        if accounts:
            for account_id in accounts:
                positions = ibkr.get_positions(account_id)
                
                if positions:
                    for p in positions:
                        all_positions.append({
                            'Broker': 'IBKR',
                            'Symbol': p.symbol,
                            'Type': 'Multi-Asset',
                            'Value': f"${p.market_value:,.2f}",
                            'P/L': f"${p.unrealized_pnl:,.2f}"
                        })
                        
                        total_value += p.market_value
                        total_pnl += p.unrealized_pnl
    
    # Display summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Portfolio Value", f"${total_value:,.2f}")
    with col2:
        st.metric("Total Unrealized P/L", f"${total_pnl:,.2f}")
    with col3:
        st.metric("Number of Positions", len(all_positions))
    
    # Display all positions
    if all_positions:
        st.dataframe(pd.DataFrame(all_positions), use_container_width=True, hide_index=True)
    else:
        st.info("No positions across any broker")


def render_ml_trading_signals():
    """Display ML trading signals with DB fallback and MLflow indicator linkage."""
    st.subheader("🤖 ML Trading Signals")

    try:
        from sqlalchemy import create_engine, inspect
        from sqlalchemy.exc import OperationalError
        from frontend.utils.secrets_helper import get_mysql_config

        mysql_config = get_mysql_config()
        base_host = mysql_config.get('host', '127.0.0.1')
        base_port = mysql_config.get('port', 3306)
        base_user = mysql_config.get('user', 'root')
        base_password = mysql_config.get('password', 'root')
        configured_db = mysql_config.get('database')

        candidate_dbs = []
        for db_name in [configured_db, 'bbbot1', 'railway', 'mansa_bot']:
            if db_name and db_name not in candidate_dbs:
                candidate_dbs.append(db_name)

        df_signals = pd.DataFrame()
        selected_db = None
        table_ref = None

        for db_name in candidate_dbs:
            try:
                connection_string = (
                    f"mysql+pymysql://{base_user}:{base_password}@{base_host}:{base_port}/{db_name}"
                )
                engine = create_engine(connection_string)
                inspector = inspect(engine)

                schema_names = inspector.get_schema_names()
                has_marts_schema = 'marts' in schema_names

                if has_marts_schema and 'features_roi' in inspector.get_table_names(schema='marts'):
                    table_ref = 'marts.features_roi'
                elif 'features_roi' in inspector.get_table_names():
                    table_ref = 'features_roi'
                else:
                    engine.dispose()
                    continue

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
                LIMIT 25;
                """

                df_signals = pd.read_sql(query, engine)
                selected_db = db_name
                engine.dispose()
                break

            except OperationalError as e:
                if "Unknown database" in str(e):
                    continue
                continue
            except Exception:
                continue

        if df_signals.empty:
            st.warning("⚠️ No trading signals found in available databases.")
            st.info("Run the ML feature pipeline to populate `features_roi` and refresh this tab.")
            return

        st.success(f"✅ Loaded signals from database: {selected_db} ({table_ref})")

        def highlight_signal(val):
            if val == 'BUY':
                return 'background-color: #90EE90'
            if val == 'SELL':
                return 'background-color: #FFB6C1'
            return ''

        styled_df = df_signals.style.applymap(highlight_signal, subset=['trade_signal'])
        st.dataframe(styled_df, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("🟢 BUY Signals", int((df_signals['trade_signal'] == 'BUY').sum()))
        col2.metric("🔴 SELL Signals", int((df_signals['trade_signal'] == 'SELL').sum()))
        col3.metric("⚪ HOLD Signals", int((df_signals['trade_signal'] == 'HOLD').sum()))

        st.markdown("---")
        st.subheader("🧠 Experiment Output Indicator")
        try:
            import mlflow
            from mlflow.tracking import MlflowClient
            from bbbot1_pipeline.mlflow_config import get_mlflow_tracking_uri

            mlflow.set_tracking_uri(get_mlflow_tracking_uri())
            client = MlflowClient()
            experiments = client.search_experiments(max_results=1)
            if experiments:
                runs = mlflow.search_runs(experiment_ids=[experiments[0].experiment_id], max_results=1)
                if not runs.empty:
                    st.success("✅ ML Trading Signals synced to MLflow experiment outputs (latest run detected)")
                else:
                    st.warning("⚠️ MLflow is reachable, but no runs found yet for latest experiment")
            else:
                st.warning("⚠️ MLflow reachable, but no experiments found")
        except Exception as mlflow_error:
            st.warning(f"⚠️ MLflow linkage check unavailable: {mlflow_error}")

    except Exception as e:
        st.error(f"Failed to load trading signals: {e}")


# Standalone page function
def multi_broker_page():
    """Standalone page for multi-broker trading"""
    render_multi_broker_dashboard()


if __name__ == "__main__":
    render_multi_broker_dashboard()
