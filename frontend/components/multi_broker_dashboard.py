"""
Unified Multi-Broker Dashboard
Integrates MT5 (FOREX/Futures), Alpaca (Stocks/Crypto), and IBKR (All Assets)
"""

import streamlit as st
import pandas as pd
import os
import time
from dotenv import load_dotenv
from frontend.utils.broker_trade_sync import sync_connected_brokers

load_dotenv(override=True)

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
            'ibkr': None,
            'axi': None,
        }
    
    # Broker status overview
    render_broker_status()
    
    st.markdown("---")
    
    # Tabs for each broker
    tabs = st.tabs([
        "🔌 MT5 (FOREX/Futures)",
        "📈 Alpaca (Stocks/Crypto)",
        "🏦 IBKR (Multi-Asset)",
        "🎯 AXI (Prop Firm)",
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
        render_axi_section()

    with tabs[4]:
        render_combined_portfolio()

    with tabs[5]:
        render_ml_trading_signals()


def render_broker_status():
    """Display connection status for all brokers"""

    # Streamlit session state resets on app restarts/sleep.
    # Auto-reconnect Alpaca periodically so production recovers without manual clicks.
    if ALPACA_AVAILABLE and st.session_state.brokers.get('alpaca') is None:
        _last_err = st.session_state.get('alpaca_last_connect_error', '')
        _is_auth_fail = '401' in _last_err or '403' in _last_err or 'Auth failed' in _last_err
        # Skip auto-reconnect on auth failures — they require user action (new credentials).
        # Only auto-retry transient errors (network timeouts, server unavailable, etc.).
        if not _is_auth_fail:
            now_ts = time.time()
            last_attempt_ts = st.session_state.get('alpaca_auto_connect_last_attempt', 0.0)
            cooldown_seconds = 60
            if now_ts - float(last_attempt_ts) >= cooldown_seconds:
                st.session_state['alpaca_auto_connect_last_attempt'] = now_ts
                connect_alpaca(silent=True, rerun_on_success=False)
    
    st.subheader("🔗 Broker Connections")
    
    col1, col2, col3, col4 = st.columns(4)

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
            last_err = st.session_state.get('alpaca_last_connect_error', '')
            if '401' in last_err or 'Auth failed' in last_err:
                st.caption("⚠️ Auth failed — update keys in Alpaca tab")
            if st.button("Connect Alpaca", key="connect_alpaca_main_dashboard"):
                # Use manually-entered session credentials if the user already typed them
                # in the Alpaca tab form; otherwise fall back to env/secrets.
                _stored_key = st.session_state.get('alpaca_api_key_stored', '')
                _stored_secret = st.session_state.get('alpaca_secret_key_stored', '')
                if _stored_key and _stored_secret:
                    connect_alpaca(
                        api_key=_stored_key,
                        secret_key=_stored_secret,
                        paper=st.session_state.get('alpaca_paper_trading', True),
                    )
                else:
                    connect_alpaca()

    with col3:
        ibkr_connected = st.session_state.brokers['ibkr'] is not None
        status = "🟢 Connected" if ibkr_connected else "🔴 Disconnected"
        st.metric("IBKR (Multi-Asset)", status)
        if not ibkr_connected and IBKR_AVAILABLE:
            if st.button("Connect IBKR", key="connect_ibkr_main_dashboard"):
                connect_ibkr()

    with col4:
        axi_connected = st.session_state.brokers.get('axi') is not None
        status = "🟢 Connected" if axi_connected else "🔴 Disconnected"
        st.metric("AXI (Prop Firm)", status)
        if not axi_connected and MT5_AVAILABLE:
            if st.button("Connect AXI", key="connect_axi_main_dashboard"):
                connect_axi()

    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if st.button("🧪 Test Connected Brokers", key="test_connected_brokers_btn", use_container_width=True):
            results = _run_connected_broker_smoke_tests(st.session_state.brokers)
            st.session_state["broker_test_results"] = results
    with action_col2:
        if st.button("🔄 Sync Broker Trades", key="sync_broker_trades_btn", use_container_width=True):
            with st.spinner("Syncing broker trades into Trade History..."):
                sync_results = sync_connected_brokers(st.session_state.brokers)
            st.session_state["broker_sync_results"] = [
                {
                    "Broker": item.broker,
                    "Inserted": item.inserted,
                    "Skipped": item.skipped,
                    "Notified": item.notified,
                    "Errors": item.errors,
                }
                for item in sync_results
            ]
            st.cache_data.clear()

    test_results = st.session_state.get("broker_test_results")
    if test_results:
        st.markdown("**Latest Broker Connection Test**")
        st.dataframe(pd.DataFrame(test_results), use_container_width=True, hide_index=True)

    sync_results = st.session_state.get("broker_sync_results")
    if sync_results:
        st.markdown("**Latest Broker Trade Sync**")
        st.dataframe(pd.DataFrame(sync_results), use_container_width=True, hide_index=True)

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


def _run_connected_broker_smoke_tests(brokers: dict) -> list[dict]:
    """Run lightweight connection tests without placing any orders."""
    checks: list[dict] = []

    mt5 = brokers.get('mt5')
    if mt5 is None:
        checks.append({"Broker": "MT5", "Result": "SKIPPED", "Details": "Not connected"})
    else:
        ok = bool(mt5.health_check())
        checks.append({
            "Broker": "MT5",
            "Result": "PASS" if ok else "FAIL",
            "Details": "API bridge reachable" if ok else "MT5 API bridge unavailable",
        })

    axi = brokers.get('axi')
    if axi is None:
        checks.append({"Broker": "AXI", "Result": "SKIPPED", "Details": "Not connected"})
    else:
        ok = bool(axi.health_check())
        checks.append({
            "Broker": "AXI",
            "Result": "PASS" if ok else "FAIL",
            "Details": "AXI MT5 bridge reachable" if ok else "AXI MT5 bridge unavailable",
        })

    alpaca = brokers.get('alpaca')
    if alpaca is None:
        checks.append({"Broker": "Alpaca", "Result": "SKIPPED", "Details": "Not connected"})
    else:
        account = alpaca.get_account()
        ok = bool(account)
        details = "Authenticated" if ok else (getattr(alpaca, "last_error", "Account query failed") or "Account query failed")
        checks.append({
            "Broker": "Alpaca",
            "Result": "PASS" if ok else "FAIL",
            "Details": details,
        })

    ibkr = brokers.get('ibkr')
    if ibkr is None:
        checks.append({"Broker": "IBKR", "Result": "SKIPPED", "Details": "Not connected"})
    else:
        ok = bool(ibkr.is_authenticated())
        checks.append({
            "Broker": "IBKR",
            "Result": "PASS" if ok else "FAIL",
            "Details": "Gateway authenticated" if ok else "Gateway not authenticated",
        })

    return checks


def connect_mt5(
    user: str | None = None,
    password: str | None = None,
    host: str | None = None,
    port: int | None = None,
    api_url: str | None = None,
):
    """Connect to MT5"""
    try:
        from frontend.utils.mt5_connector import MT5Connector
        
        # Use MT5_API_URL or MT5_REST_API_URL (fallback to 8002, not 8000 which is Airbyte)
        default_url = "http://localhost:8002"
        resolved_api_url = (
            (api_url or "").strip()
            or os.getenv("MT5_API_URL")
            or os.getenv("MT5_REST_API_URL", default_url)
        )
        resolved_user = (user or os.getenv("MT5_USER", "")).strip()
        resolved_password = password or os.getenv("MT5_PASSWORD", "")
        resolved_host = (host or os.getenv("MT5_HOST", "")).strip()
        resolved_port = int(port if port is not None else os.getenv("MT5_PORT", "443"))

        connector = MT5Connector(resolved_api_url)
        
        if connector.connect(
            user=resolved_user,
            password=resolved_password,
            host=resolved_host,
            port=resolved_port,
        ):
            st.session_state.brokers['mt5'] = connector
            st.success("✅ MT5 Connected!")
            st.rerun()
        else:
            detail = getattr(connector, "last_connect_error", "").strip()
            st.error(
                "❌ MT5 connection failed"
            )
            if detail:
                st.info(f"Failure detail: {detail}")
            st.info("💡 Run: src\\START_MT5_SERVER.bat to start the MT5 API server")
    except Exception as e:
        st.error("❌ MT5 API server is not responding")
        st.info(f"Error details: {e}")
        st.warning(
            "🔧 **Quick Fix:**\n"
            "1. Make sure MT5 desktop is logged in\n"
            "2. Run `src\\START_MT5_SERVER.bat` to start the API bridge\n"
            "3. Try connecting again"
        )


def connect_alpaca(
    api_key: str | None = None,
    secret_key: str | None = None,
    paper: bool | None = None,
    silent: bool = False,
    rerun_on_success: bool = True,
):
    """Connect to Alpaca"""
    try:
        from frontend.utils.secrets_helper import get_alpaca_config
        from frontend.components.alpaca_connector import AlpacaConnector

        # Prefer credentials entered in UI; fallback to secrets/env.
        key = (api_key or "").strip()
        secret = (secret_key or "").strip()
        source = "manual"

        if not key or not secret:
            try:
                config = get_alpaca_config()
                key = str(config["api_key"])
                secret = str(config["secret_key"])
                if paper is None:
                    paper = bool(config["paper"])
                source = "secrets"
            except ValueError as e:
                st.session_state['alpaca_last_connect_error'] = str(e)
                if not silent:
                    st.error(f"❌ {str(e)}")
                    st.info("Configure in Streamlit Secrets (Cloud) or .env file (Local)")
                return

        if paper is None:
            paper = True

        requested_mode = bool(paper)
        key_prefix = key[:2].upper() if key else ""

        # Respect key type first to avoid invalid cross-mode attempts.
        if key_prefix == "PK":
            attempted_modes: list[bool] = [True]
        elif key_prefix == "AK":
            attempted_modes = [False]
        else:
            attempted_modes = [requested_mode, not requested_mode]

        connected = False
        connected_mode = requested_mode
        account = None
        connector = None
        failure_detail = ""

        for mode_flag in attempted_modes:
            connector_candidate = AlpacaConnector(key, secret, mode_flag)
            account_candidate = connector_candidate.get_account()
            if account_candidate:
                connector = connector_candidate
                account = account_candidate
                connected = True
                connected_mode = mode_flag
                break
            failure_detail = getattr(connector_candidate, "last_error", "") or failure_detail

        if connected and connector and account:
            st.session_state.brokers['alpaca'] = connector
            portfolio_val = float(account.get('portfolio_value', 0.0))
            st.session_state['alpaca_last_connect_error'] = ""
            st.session_state['alpaca_connected_mode'] = (
                "paper" if connected_mode else "live"
            )
            if not silent:
                source_msg = source
                if connected_mode != requested_mode:
                    source_msg += ", mode auto-corrected"
                st.success(
                    f"✅ Alpaca Connected ({source_msg})! Portfolio: ${portfolio_val:,.2f}"
                )
            if rerun_on_success:
                st.rerun()
        else:
            requested_mode_name = "paper" if requested_mode else "live"
            attempted_mode_names = ", ".join(
                ["paper" if m else "live" for m in attempted_modes]
            )
            key_hint = "paper-key" if key_prefix == "PK" else (
                "live-key" if key_prefix == "AK" else "unknown-key-type"
            )
            err_msg = (
                f"Alpaca connection failed (requested: {requested_mode_name}; "
                f"attempted: {attempted_mode_names}; key: {key_hint}). "
                "Verify production secrets and endpoint reachability."
            )
            if failure_detail:
                err_msg = f"{err_msg} Cause: {failure_detail}"
                if "HTTP 401" in failure_detail or "HTTP 403" in failure_detail:
                    err_msg += " (Auth failed: verify ALPACA/API secret pair and paper-mode key in production secrets.)"
            st.session_state['alpaca_last_connect_error'] = err_msg
            if not silent:
                st.error(f"❌ {err_msg}")
    except Exception as e:
        st.session_state['alpaca_last_connect_error'] = str(e)
        if not silent:
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
            st.success(f"✅ IBKR Connected! Accounts: {accounts_str}")
            st.rerun()
        else:
            st.error("❌ IBKR Gateway not authenticated. Make sure Gateway is running.")
    except Exception as e:
        st.error(f"IBKR error: {e}")


def connect_axi():
    """Connect to AXI Select prop firm account via MT5 bridge"""
    try:
        from frontend.utils.mt5_connector import MT5Connector
        from frontend.utils.secrets_helper import get_secret

        api_url = (
            get_secret("AXI_MT5_API_URL", section="axi", default=None)
            or get_secret("AXI_MT5_API_URL", default=None)
            or get_secret("MT5_API_URL", default="http://localhost:8002")
        )
        connector = MT5Connector(api_url)

        user = (
            get_secret("AXI_MT5_USER", section="axi", default=None)
            or get_secret("AXI_MT5_USER", default=None)
            or get_secret("MT5_USER", default="")
        )
        password = (
            get_secret("AXI_MT5_PASSWORD", section="axi", default=None)
            or get_secret("AXI_MT5_PASSWORD", default=None)
            or get_secret("MT5_PASSWORD", default="")
        )
        host = (
            get_secret("AXI_MT5_HOST", section="axi", default=None)
            or get_secret("AXI_MT5_SERVER", section="axi", default=None)
            or get_secret("AXI_MT5_HOST", default=None)
            or get_secret("AXI_MT5_SERVER", default=None)
            or get_secret("MT5_SERVER", default=None)
            or get_secret("MT5_HOST", default="")
        )
        port = int(
            get_secret("AXI_MT5_PORT", section="axi", default=None)
            or get_secret("AXI_MT5_PORT", default=None)
            or get_secret("MT5_PORT", default="443")
        )

        if not host:
            st.error(
                "❌ AXI MT5 server not configured. Set AXI_MT5_SERVER or "
                "AXI_MT5_HOST in .env, or reuse MT5_SERVER/MT5_HOST."
            )
            st.info("Examples — AXI demo: mt5-demo07.axi.com | AXI live: Axi-US51-Live")
            return

        if connector.connect(user=user, password=password, host=host, port=port):
            st.session_state.brokers['axi'] = connector
            st.success("✅ AXI Select connected via MT5!")
            st.rerun()
        else:
            st.error("❌ AXI MT5 connection failed — check credentials and server")
    except Exception as e:
        st.error(f"AXI connection error: {e}")


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
            default_url = "http://localhost:8002"
            api_url_value = os.getenv("MT5_API_URL") or os.getenv("MT5_REST_API_URL", default_url)
            
            with col1:
                user = st.text_input("MT5 Account", value=os.getenv("MT5_USER", ""))
                host = st.text_input("Broker Host", value=os.getenv("MT5_HOST", ""))
            
            with col2:
                password = st.text_input("Password", type="password", value=os.getenv("MT5_PASSWORD", ""))
                port = st.number_input("Port", value=int(os.getenv("MT5_PORT", "443")))
            api_url = st.text_input("MT5 API URL", value=api_url_value)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("Connect", type="primary", use_container_width=True):
                    connect_mt5(
                        user=user,
                        password=password,
                        host=host,
                        port=int(port),
                        api_url=api_url,
                    )
            
            with col_btn2:
                if st.button("🏥 Health Check", use_container_width=True):
                    base_url = (api_url or "").strip() or api_url_value
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
        last_error = st.session_state.get('alpaca_last_connect_error', '')
        is_auth_failure = ('401' in last_error or '403' in last_error or 'Auth failed' in last_error)

        if is_auth_failure:
            st.error(f"❌ {last_error}")
            st.warning(
                "🔑 The stored Alpaca credentials are invalid (HTTP 401). "
                "Enter updated API key and secret below."
            )
        else:
            st.info("👆 Connect to Alpaca to access Stock and Crypto trading")

        with st.expander(
            "🔗 Alpaca Connection" + (" — ⚠️ Update Credentials" if is_auth_failure else ""),
            expanded=is_auth_failure,
        ):
            if is_auth_failure:
                st.markdown(
                    "**Steps to fix:**\n"
                    "1. Go to [alpaca.markets](https://app.alpaca.markets) → Paper Trading → API Keys\n"
                    "2. Regenerate or copy your key/secret\n"
                    "3. Paste below and click Connect"
                )
            # Initialize session state for Alpaca credentials if not present
            if 'alpaca_api_key_stored' not in st.session_state:
                st.session_state.alpaca_api_key_stored = ""
            if 'alpaca_secret_key_stored' not in st.session_state:
                st.session_state.alpaca_secret_key_stored = ""
            if 'alpaca_paper_trading' not in st.session_state:
                st.session_state.alpaca_paper_trading = True

            # Use form to properly handle inputs and submission
            with st.form(key="alpaca_connection_form", clear_on_submit=False):
                api_key = st.text_input(
                    "API Key",
                    value=st.session_state.alpaca_api_key_stored,
                    type="password",
                    key="alpaca_api_key_form_input"
                )
                secret_key = st.text_input(
                    "Secret Key",
                    value=st.session_state.alpaca_secret_key_stored,
                    type="password",
                    key="alpaca_secret_key_form_input"
                )
                paper = st.checkbox(
                    "Paper Trading (Test Account)",
                    value=st.session_state.alpaca_paper_trading,
                    key="alpaca_paper_form_input"
                )

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submit_manual = st.form_submit_button(
                        "🔑 Connect with API Keys",
                        type="primary",
                        use_container_width=True,
                        key="alpaca_connect_form_btn"
                    )
                with col_btn2:
                    submit_env = st.form_submit_button(
                        "🔧 Use .env / Secrets",
                        use_container_width=True,
                        key="alpaca_env_connect_form_btn"
                    )

                if submit_manual:
                    if api_key and secret_key:
                        st.session_state.alpaca_api_key_stored = api_key
                        st.session_state.alpaca_secret_key_stored = secret_key
                        st.session_state.alpaca_paper_trading = paper
                        connect_alpaca(api_key=api_key, secret_key=secret_key, paper=paper)
                    else:
                        st.error("❌ API Key and Secret Key are required for manual connection")

                if submit_env:
                    # Clear stored values to use env/secrets
                    st.session_state.alpaca_api_key_stored = ""
                    st.session_state.alpaca_secret_key_stored = ""
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
        1. Install IBKR Gateway (port 5000) **or** TWS (port 7496/7497)
        2. Enable API connections in Gateway/TWS → Settings → API
        3. Click Connect above
        """)

        # TWS socket connectivity test
        with st.expander("🖥️ Test IBKR TWS Connection (Ports 7496/7497)"):
            st.markdown(
                "Trader Workstation (TWS) exposes a socket API on **port 7497** (paper) "
                "or **port 7496** (live). This test checks whether TWS is running and "
                "accepting API connections."
            )
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                tws_host = st.text_input(
                    "TWS Host", value=os.getenv("IBKR_HOST", "127.0.0.1"), key="tws_host_input"
                )
            with col_t2:
                tws_port = st.selectbox(
                    "TWS Port", [7497, 7496],
                    format_func=lambda p: f"{p} ({'paper' if p == 7497 else 'live'})",
                    key="tws_port_input",
                )
            if st.button("🧪 Test TWS Socket", key="test_tws_btn"):
                import socket
                try:
                    with socket.create_connection((tws_host, int(tws_port)), timeout=3):
                        st.success(
                            f"✅ TWS port {tws_port} is open on {tws_host} — "
                            "API connections accepted."
                        )
                except (socket.timeout, ConnectionRefusedError, OSError) as err:
                    st.error(
                        f"❌ TWS port {tws_port} not reachable on {tws_host}: {err}"
                    )
                    st.info(
                        "Make sure TWS is running and API is enabled: "
                        "TWS → Edit → Global Configuration → API → Settings → "
                        "Enable ActiveX and Socket Clients."
                    )

        # Gateway manual connect form
        with st.expander("🔗 IBKR Gateway Connection"):
            gateway_url = st.text_input(
                "Gateway URL",
                value=os.getenv("IBKR_GATEWAY_URL", "https://localhost:5000"),
                key="ibkr_gateway_url_input",
            )
            if st.button("Connect Gateway", type="primary", key="ibkr_gateway_connect_btn"):
                try:
                    from frontend.utils.ibkr_connector import IBKRConnector
                    temp_connector = IBKRConnector(gateway_url)
                    if temp_connector.is_authenticated():
                        st.session_state.brokers['ibkr'] = temp_connector
                        accounts = temp_connector.get_accounts()
                        st.success(f"✅ IBKR Gateway connected! Accounts: {', '.join(accounts or [])}")
                        st.rerun()
                    else:
                        st.error("❌ Gateway not authenticated — check Gateway is running and logged in.")
                except Exception as e:
                    st.error(f"IBKR Gateway error: {e}")
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


def render_axi_section():
    """AXI Select prop firm trading section (via MT5 bridge)"""

    if not MT5_AVAILABLE:
        st.error("MT5 connector not available — required for AXI Select")
        return

    connector = st.session_state.brokers.get('axi')

    if not connector:
        st.info("Connect to your AXI Select prop firm account through the MT5 API bridge.")

        with st.expander("🎯 AXI Select Configuration", expanded=True):
            from frontend.utils.secrets_helper import get_secret

            st.markdown(
                "**AXI Select** is a prop trading firm that provides funded accounts via "
                "MetaTrader 5. Configure your AXI MT5 server credentials below.\n\n"
                "Set `AXI_MT5_*` vars in your `.env` file to persist these settings."
            )
            col1, col2 = st.columns(2)
            with col1:
                axi_user = st.text_input(
                    "AXI Account Number",
                    value=(
                        get_secret("AXI_MT5_USER", section="axi", default=None)
                        or get_secret("AXI_MT5_USER", default="")
                    ),
                    key="axi_user_input",
                )
                axi_host = st.text_input(
                    "AXI MT5 Server / Host",
                    value=(
                        get_secret("AXI_MT5_HOST", section="axi", default=None)
                        or get_secret("AXI_MT5_SERVER", section="axi", default=None)
                        or get_secret("AXI_MT5_HOST", default=None)
                        or get_secret("AXI_MT5_SERVER", default=None)
                        or get_secret("MT5_SERVER", default=None)
                        or get_secret("MT5_HOST", default=None)
                        or "mt5-demo07.axi.com"
                    ),
                    key="axi_host_input",
                )
            with col2:
                axi_password = st.text_input(
                    "Password",
                    type="password",
                    value="",
                    key="axi_pass_input",
                )
                axi_port = st.number_input(
                    "Port",
                    value=int(
                        get_secret("AXI_MT5_PORT", section="axi", default=None)
                        or get_secret("AXI_MT5_PORT", default="443")
                    ),
                    key="axi_port_input",
                )

            axi_api_url = st.text_input(
                "MT5 API Bridge URL",
                value=(
                    get_secret("AXI_MT5_API_URL", section="axi", default=None)
                    or get_secret("AXI_MT5_API_URL", default=None)
                    or get_secret("MT5_API_URL", default="http://localhost:8002")
                ),
                key="axi_api_url_input",
            )

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("Connect AXI", type="primary", use_container_width=True, key="axi_connect_btn"):
                    with st.spinner("Connecting to AXI Select…"):
                        try:
                            from frontend.utils.mt5_connector import MT5Connector
                            temp_connector = MT5Connector(axi_api_url)
                            pwd = (
                                axi_password
                                or get_secret("AXI_MT5_PASSWORD", section="axi", default=None)
                                or get_secret("AXI_MT5_PASSWORD", default="")
                            )
                            if temp_connector.connect(
                                user=axi_user, password=pwd, host=axi_host, port=int(axi_port)
                            ):
                                st.session_state.brokers['axi'] = temp_connector
                                st.success("✅ AXI Select connected via MT5!")
                                st.rerun()
                            else:
                                st.error(
                                    "❌ AXI MT5 connection failed — verify account number, "
                                    "password, and server/host value."
                                )
                        except Exception as e:
                            st.error(f"AXI error: {e}")
            with col_btn2:
                if st.button("🏥 Test MT5 Bridge", use_container_width=True, key="axi_health_btn"):
                    from frontend.utils.mt5_connector import MT5Connector
                    temp = MT5Connector(axi_api_url)
                    if temp.health_check():
                        st.success("✅ MT5 API bridge is reachable")
                    else:
                        st.error("❌ MT5 API bridge not responding")
                        st.info("Start the MT5 REST server: `src\\START_MT5_SERVER.bat`")

            st.markdown("---")
            st.markdown("**Required `.env` settings:**")
            st.code(
                "AXI_MT5_USER=your_axi_account_number\n"
                "AXI_MT5_PASSWORD=your_axi_password\n"
                "AXI_MT5_SERVER=Axi-US51-Live  # or AXI_MT5_HOST=mt5-demo07.axi.com\n"
                "AXI_MT5_PORT=443\n"
                "AXI_MT5_API_URL=http://localhost:8002  # shared MT5 bridge\n\n"
                "# Optional shared fallback for both FTMO and AXI\n"
                "MT5_SERVER=Axi-US51-Live",
                language="bash",
            )
        return

    # ── Connected ──────────────────────────────────────────────────────────────
    st.success("🟢 AXI Select connected via MT5")
    account = connector.get_account_info()

    if account:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("AXI Balance", f"${account.get('balance', 0):,.2f}")
        with col2:
            st.metric("Equity", f"${account.get('equity', 0):,.2f}")
        with col3:
            st.metric("Free Margin", f"${account.get('free_margin', 0):,.2f}")
        with col4:
            floating = account.get('equity', 0) - account.get('balance', 0)
            st.metric("Floating P/L", f"${floating:,.2f}")

    st.subheader("📊 AXI Positions")
    positions = connector.get_positions()
    if positions:
        pos_data = [
            {
                'Symbol': p.symbol,
                'Type': p.type,
                'Volume': p.volume,
                'Open Price': p.open_price,
                'Current Price': p.current_price,
                'Profit': p.profit,
            }
            for p in positions
        ]
        st.dataframe(pd.DataFrame(pos_data), use_container_width=True, hide_index=True)
    else:
        st.info("No open AXI positions")

    if st.button("🔌 Disconnect AXI", key="axi_disconnect_btn"):
        st.session_state.brokers['axi'] = None
        st.rerun()


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
