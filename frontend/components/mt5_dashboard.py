"""
Streamlit component for MetaTrader 5 trading interface
Integrates MT5 REST API with Bentley Budget Bot dashboard
"""

import streamlit as st
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    from frontend.utils.mt5_connector import MT5Connector, quick_connect
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


def render_mt5_dashboard():
    """Main MT5 trading dashboard for Streamlit"""
    
    if not MT5_AVAILABLE:
        st.error("MT5 Connector not available. Check installation.")
        return
    
    st.title("🔌 MetaTrader 5 Trading")
    
    # Initialize session state
    if 'mt5_connector' not in st.session_state:
        st.session_state.mt5_connector = None
    if 'mt5_connected' not in st.session_state:
        st.session_state.mt5_connected = False
    
    # Connection section
    with st.expander("🔗 MT5 Connection Settings", expanded=not st.session_state.mt5_connected):
        render_connection_form()
    
    # Only show trading interface if connected
    if st.session_state.mt5_connected and st.session_state.mt5_connector:
        render_trading_interface()
    else:
        st.info("👆 Please connect to your MT5 account to access trading features")


def render_connection_form():
    """Render MT5 connection form"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        base_url = st.text_input(
            "MT5 API Server URL",
            value="http://localhost:8000",
            help="Base URL of your MT5 REST API server"
        )
        user = st.text_input(
            "MT5 Account Number",
            help="Your MT5 account login"
        )
        host = st.text_input(
            "Broker Server",
            value="",
            help="Broker server hostname (e.g., broker.com)"
        )
    
    with col2:
        password = st.text_input(
            "MT5 Password",
            type="password",
            help="Your MT5 account password"
        )
        port = st.number_input(
            "Port",
            value=443,
            min_value=1,
            max_value=65535,
            help="Connection port (usually 443)"
        )
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("🔌 Connect", type="primary", use_container_width=True):
            if not all([base_url, user, password, host]):
                st.error("Please fill in all connection fields")
            else:
                with st.spinner("Connecting to MT5..."):
                    connector = MT5Connector(base_url)
                    if connector.connect(user, password, host, int(port)):
                        st.session_state.mt5_connector = connector
                        st.session_state.mt5_connected = True
                        st.success("✅ Connected to MT5 successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to connect. Check credentials and server.")
    
    with col_btn2:
        if st.button("🔌 Disconnect", disabled=not st.session_state.mt5_connected, use_container_width=True):
            if st.session_state.mt5_connector:
                st.session_state.mt5_connector.disconnect()
            st.session_state.mt5_connector = None
            st.session_state.mt5_connected = False
            st.success("Disconnected from MT5")
            st.rerun()
    
    with col_btn3:
        if st.button("🏥 Health Check", use_container_width=True):
            connector = MT5Connector(base_url)
            if connector.health_check():
                st.success("✅ MT5 API server is healthy")
            else:
                st.error("❌ MT5 API server is not responding")


def render_trading_interface():
    """Render main trading interface"""
    
    connector = st.session_state.mt5_connector
    
    # Account summary at top
    render_account_summary(connector)
    
    st.markdown("---")
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Positions",
        "📈 Market Data",
        "💰 Place Trade",
        "🔔 Webhooks"
    ])
    
    with tab1:
        render_positions_tab(connector)
    
    with tab2:
        render_market_data_tab(connector)
    
    with tab3:
        render_place_trade_tab(connector)
    
    with tab4:
        render_webhooks_tab(connector)


def render_account_summary(connector: MT5Connector):
    """Display account information summary"""
    
    account_info = connector.get_account_info()
    
    if not account_info:
        st.error("Failed to retrieve account information")
        return
    
    st.subheader("💼 Account Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        balance = account_info.get('balance', 0)
        st.metric("Balance", f"${balance:,.2f}")
    
    with col2:
        equity = account_info.get('equity', 0)
        profit = equity - balance
        st.metric("Equity", f"${equity:,.2f}", delta=f"${profit:,.2f}")
    
    with col3:
        margin = account_info.get('margin', 0)
        st.metric("Margin Used", f"${margin:,.2f}")
    
    with col4:
        free_margin = account_info.get('free_margin', 0)
        st.metric("Free Margin", f"${free_margin:,.2f}")
    
    # Additional account details
    with st.expander("📋 Detailed Account Info"):
        st.json(account_info)


def render_positions_tab(connector: MT5Connector):
    """Display and manage open positions"""
    
    st.subheader("📊 Open Positions")
    
    positions = connector.get_positions()
    
    if not positions:
        st.info("No open positions")
        return
    
    # Create DataFrame
    positions_data = []
    for pos in positions:
        positions_data.append({
            'Ticket': pos.ticket,
            'Symbol': pos.symbol,
            'Type': pos.type,
            'Volume': pos.volume,
            'Open Price': pos.open_price,
            'Current Price': pos.current_price,
            'Profit': pos.profit,
            'Open Time': pos.open_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    df = pd.DataFrame(positions_data)
    
    # Display positions
    st.dataframe(
        df.style.applymap(
            lambda x: 'color: green' if isinstance(x, (int, float)) and x > 0 else 'color: red',
            subset=['Profit']
        ),
        use_container_width=True,
        hide_index=True
    )
    
    # Position management
    st.markdown("### Manage Position")
    col1, col2 = st.columns(2)
    
    with col1:
        ticket_to_close = st.selectbox(
            "Select position to close",
            options=[pos.ticket for pos in positions],
            format_func=lambda x: f"Ticket {x}"
        )
        
        if st.button("🔴 Close Position", type="primary"):
            with st.spinner("Closing position..."):
                if connector.close_position(ticket_to_close):
                    st.success(f"✅ Position {ticket_to_close} closed successfully")
                    st.rerun()
                else:
                    st.error("❌ Failed to close position")
    
    with col2:
        ticket_to_modify = st.selectbox(
            "Select position to modify",
            options=[pos.ticket for pos in positions],
            format_func=lambda x: f"Ticket {x}",
            key="modify_ticket"
        )
        
        new_sl = st.number_input("New Stop Loss (0 = remove)", min_value=0.0, step=0.00001, format="%.5f")
        new_tp = st.number_input("New Take Profit (0 = remove)", min_value=0.0, step=0.00001, format="%.5f")
        
        if st.button("✏️ Modify Position"):
            with st.spinner("Modifying position..."):
                sl = new_sl if new_sl > 0 else None
                tp = new_tp if new_tp > 0 else None
                
                if connector.modify_position(ticket_to_modify, sl=sl, tp=tp):
                    st.success(f"✅ Position {ticket_to_modify} modified successfully")
                    st.rerun()
                else:
                    st.error("❌ Failed to modify position")


def render_market_data_tab(connector: MT5Connector):
    """Display market data and charts"""
    
    st.subheader("📈 Market Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        symbol = st.text_input("Symbol", value="EURUSD", help="Trading symbol (e.g., EURUSD, BTCUSD)")
    
    with col2:
        timeframe = st.selectbox(
            "Timeframe",
            options=["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"],
            index=4  # H1
        )
    
    with col3:
        bars = st.number_input("Bars", min_value=10, max_value=5000, value=100)
    
    if st.button("📊 Fetch Market Data", type="primary"):
        with st.spinner(f"Fetching {symbol} data..."):
            market_data = connector.get_market_data(symbol, timeframe, int(bars))
            
            if market_data:
                # Display symbol info
                symbol_info = connector.get_symbol_info(symbol)
                if symbol_info:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Bid", f"{symbol_info.get('bid', 0):.5f}")
                    with col2:
                        st.metric("Ask", f"{symbol_info.get('ask', 0):.5f}")
                    with col3:
                        st.metric("Spread", f"{symbol_info.get('spread', 0)}")
                    with col4:
                        st.metric("Volume", f"{symbol_info.get('volume', 0)}")
                
                # Create candlestick chart
                if 'bars' in market_data and len(market_data['bars']) > 0:
                    df = pd.DataFrame(market_data['bars'])
                    
                    fig = go.Figure(data=[go.Candlestick(
                        x=df['time'],
                        open=df['open'],
                        high=df['high'],
                        low=df['low'],
                        close=df['close']
                    )])
                    
                    fig.update_layout(
                        title=f"{symbol} - {timeframe}",
                        yaxis_title="Price",
                        xaxis_title="Time",
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Display data table
                    with st.expander("📊 Raw Data"):
                        st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.warning("No market data available")
            else:
                st.error("Failed to fetch market data")


def render_place_trade_tab(connector: MT5Connector):
    """Place new trade orders"""
    
    st.subheader("💰 Place Trade Order")
    
    col1, col2 = st.columns(2)
    
    with col1:
        symbol = st.text_input("Symbol", value="EURUSD", key="trade_symbol")
        order_type = st.selectbox(
            "Order Type",
            options=["BUY", "SELL", "BUY_LIMIT", "SELL_LIMIT", "BUY_STOP", "SELL_STOP"]
        )
        volume = st.number_input("Volume (lots)", min_value=0.01, value=0.1, step=0.01, format="%.2f")
    
    with col2:
        price = st.number_input(
            "Price (for pending orders)",
            min_value=0.0,
            value=0.0,
            step=0.00001,
            format="%.5f",
            help="Leave 0 for market orders"
        )
        sl = st.number_input("Stop Loss", min_value=0.0, value=0.0, step=0.00001, format="%.5f")
        tp = st.number_input("Take Profit", min_value=0.0, value=0.0, step=0.00001, format="%.5f")
    
    comment = st.text_input("Comment", value="Bentley Bot Trade")
    
    if st.button("🚀 Place Trade", type="primary", use_container_width=True):
        with st.spinner("Placing trade order..."):
            result = connector.place_trade(
                symbol=symbol,
                order_type=order_type,
                volume=volume,
                price=price if price > 0 else None,
                sl=sl if sl > 0 else None,
                tp=tp if tp > 0 else None,
                comment=comment
            )
            
            if result and result.get('success'):
                st.success(f"✅ Trade placed successfully! Ticket: {result.get('ticket')}")
                st.json(result)
            else:
                st.error(f"❌ Failed to place trade: {result.get('error') if result else 'Unknown error'}")


def render_webhooks_tab(connector: MT5Connector):
    """Configure webhooks for real-time events"""
    
    st.subheader("🔔 Webhook Configuration")
    
    st.info("Set up webhooks to receive real-time notifications about trades, positions, and account events.")
    
    webhook_url = st.text_input(
        "Webhook URL",
        placeholder="https://your-server.com/webhook",
        help="URL to receive webhook POST requests"
    )
    
    st.markdown("**Select Events:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        trade_events = st.checkbox("Trade Events", value=True)
        position_events = st.checkbox("Position Events", value=True)
    
    with col2:
        account_events = st.checkbox("Account Events", value=False)
        market_events = st.checkbox("Market Events", value=False)
    
    if st.button("📡 Setup Webhook", type="primary"):
        events = []
        if trade_events:
            events.append('trade')
        if position_events:
            events.append('position')
        if account_events:
            events.append('account')
        if market_events:
            events.append('market')
        
        if not webhook_url:
            st.error("Please enter a webhook URL")
        elif not events:
            st.error("Please select at least one event type")
        else:
            with st.spinner("Setting up webhook..."):
                if connector.setup_webhook(webhook_url, events):
                    st.success(f"✅ Webhook configured successfully for events: {', '.join(events)}")
                else:
                    st.error("❌ Failed to setup webhook")
    
    # Webhook testing section
    with st.expander("🧪 Test Webhook"):
        st.markdown("Send a test event to your webhook URL to verify configuration")
        if st.button("Send Test Event"):
            st.info("Test webhook functionality - to be implemented on server side")


# Standalone page function for navigation
def mt5_trading_page():
    """Standalone page for MT5 trading (can be imported in multipage app)"""
    render_mt5_dashboard()


if __name__ == "__main__":
    # For testing the component standalone
    render_mt5_dashboard()
