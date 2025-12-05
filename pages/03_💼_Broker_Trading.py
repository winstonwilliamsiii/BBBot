"""
Broker Trading Dashboard
Monitor positions and execute trades across Webull, IBKR, and Binance
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Import color scheme for consistent styling
try:
    from frontend.styles.colors import COLOR_SCHEME
    from frontend.utils.styling import apply_custom_styling
    apply_custom_styling()
except ImportError:
    # Fallback colors if import fails
    COLOR_SCHEME = {
        "background": "#0F172A",
        "secondary": "#0B1220",
        "text": "#E6EEF8",
        "primary": "#06B6D4",
        "card_background": "#071431"
    }
    
    # Apply background styling
    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(180deg, {COLOR_SCHEME['background']} 0%, {COLOR_SCHEME['secondary']} 100%);
        color: {COLOR_SCHEME['text']};
    }}
    
    /* Force white text color for all elements */
    .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, 
    .stMarkdown h4, .stMarkdown h5, .stMarkdown h6, .stText, div[data-testid="stMarkdownContainer"],
    div[data-testid="stText"], label, .stSelectbox label, .stMultiSelect label,
    .stDateInput label, .stCheckbox label, .stRadio label, .stNumberInput label,
    .stTextInput label, .row-widget label {{  
        color: {COLOR_SCHEME['text']} !important;
    }}
    
    /* Headers and subheaders */
    h1, h2, h3, h4, h5, h6 {{
        color: {COLOR_SCHEME['text']} !important;
    }}
    
    /* Dataframe headers and cells */
    .stDataFrame, .stDataFrame th, .stDataFrame td, 
    div[data-testid="stDataFrame"] {{
        color: {COLOR_SCHEME['text']} !important;
    }}
    
    /* Metric labels and values */
    div[data-testid="stMetricLabel"], div[data-testid="stMetricValue"] {{
        color: {COLOR_SCHEME['text']} !important;
    }}
    
    /* Caption text */
    .stCaption {{
        color: rgba(230, 238, 248, 0.8) !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# Add bbbot1_pipeline to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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


def main():
    st.set_page_config(
        page_title="Broker Trading Dashboard",
        page_icon="💼",
        layout="wide"
    )
    
    st.title("💼 Multi-Broker Trading Dashboard")
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
        # Connect to MySQL and fetch latest signals
        from sqlalchemy import create_engine
        engine = create_engine("mysql+pymysql://root:root@127.0.0.1:3307/bbbot1")
        
        query = """
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
            END as signal
        FROM marts.features_roi
        WHERE date = (SELECT MAX(date) FROM marts.features_roi)
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
                subset=['signal']
            )
            
            st.dataframe(styled_df, use_container_width=True)
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("🟢 BUY Signals", (df_signals['signal'] == 'BUY').sum())
            col2.metric("🔴 SELL Signals", (df_signals['signal'] == 'SELL').sum())
            col3.metric("⚪ HOLD Signals", (df_signals['signal'] == 'HOLD').sum())
        
        else:
            st.info("No trading signals available. Run the ML pipeline first.")
    
    except Exception as e:
        st.error(f"Failed to load trading signals: {e}")
        st.info("Make sure marts.features_roi table exists and has data")
    
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
