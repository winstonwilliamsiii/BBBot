"""
Live Crypto Dashboard - Real-time Cryptocurrency Tracking
Displays live crypto prices, volume, and market data
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta

# Import color scheme and styling from home page
try:
    from frontend.styles.colors import COLOR_SCHEME
    from frontend.utils.styling import apply_custom_styling
    
    # Apply home page styling first
    apply_custom_styling()
    
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
    </style>
    """, unsafe_allow_html=True)
    
except ImportError:
    # Fallback if frontend modules not available
    st.warning("⚠️ Styling modules not found. Using fallback styles.")

# Import yfinance for crypto data
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    st.error("⚠️ yfinance not available. Install with: pip install yfinance")

# Import MLFlow tracker
try:
    from bbbot1_pipeline.mlflow_tracker import get_tracker
    from bbbot1_pipeline.mlflow_config import print_connection_details
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


def display_live_crypto_dashboard():
    """Main live crypto dashboard page"""
    
    st.title("🔴 Live Crypto Dashboard")
    st.markdown("Real-time cryptocurrency market monitoring with MLFlow tracking")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Dashboard Settings")
    
    # Crypto pairs selection
    crypto_pairs = {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Solana": "SOL-USD",
        "Cardano": "ADA-USD",
        "Polygon": "MATIC-USD",
        "Avalanche": "AVAX-USD",
        "Chainlink": "LINK-USD",
        "Polkadot": "DOT-USD"
    }
    
    selected_cryptos = st.sidebar.multiselect(
        "Select Cryptocurrencies",
        options=list(crypto_pairs.keys()),
        default=["Bitcoin", "Ethereum", "Solana"]
    )
    
    # Timeframe selection
    timeframe = st.sidebar.selectbox(
        "Timeframe",
        ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
        index=2
    )
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)", value=False)
    
    # MLFlow logging toggle
    enable_logging = st.sidebar.checkbox(
        "🔬 Enable MLFlow Logging",
        value=True,
        help="Log crypto data to MLFlow database"
    )
    
    # Connection details button
    if st.sidebar.button("🔌 Show MLFlow Connection"):
        if MLFLOW_AVAILABLE:
            st.sidebar.code("""
Connection: Bentley_Budget
Host: 127.0.0.1:3306
Database: mlflow_db
User: root@localhost
            """)
        else:
            st.sidebar.warning("MLFlow not configured")
    
    if not selected_cryptos:
        st.info("👈 Select cryptocurrencies from the sidebar to begin monitoring")
        return
    
    if not YFINANCE_AVAILABLE:
        st.error("Cannot fetch crypto data. Please install yfinance.")
        return
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Live Prices",
        "📈 Price Charts",
        "📉 Volume Analysis",
        "🔬 MLFlow Logs"
    ])
    
    # Fetch crypto data
    crypto_data = {}
    selected_symbols = [crypto_pairs[name] for name in selected_cryptos]
    
    with st.spinner("Fetching live crypto data..."):
        fetch_start = time.time()
        
        for name in selected_cryptos:
            symbol = crypto_pairs[name]
            try:
                ticker = yf.Ticker(symbol)
                
                # Get current price info
                info = ticker.info
                
                # Get historical data
                hist = ticker.history(period=timeframe)
                
                crypto_data[name] = {
                    "symbol": symbol,
                    "info": info,
                    "history": hist,
                    "current_price": info.get('regularMarketPrice', info.get('currentPrice', 0)),
                    "previous_close": info.get('previousClose', 0),
                    "volume": info.get('volume', 0),
                    "market_cap": info.get('marketCap', 0),
                    "day_high": info.get('dayHigh', 0),
                    "day_low": info.get('dayLow', 0),
                }
            except Exception as e:
                st.warning(f"⚠️ Could not fetch {name}: {e}")
                continue
        
        fetch_time = time.time() - fetch_start
    
    # Log to MLFlow if enabled
    if enable_logging and MLFLOW_AVAILABLE and crypto_data:
        try:
            tracker = get_tracker()
            tracker.log_data_ingestion(
                source="yfinance_crypto",
                tickers=selected_symbols,
                rows_fetched=sum(len(d["history"]) for d in crypto_data.values()),
                success=True,
                response_time=fetch_time
            )
            st.success(f"✅ Logged to MLFlow (fetch time: {fetch_time:.2f}s)")
        except Exception as e:
            st.warning(f"⚠️ MLFlow logging failed: {e}")
    
    # Tab 1: Live Prices
    with tab1:
        display_live_prices(crypto_data)
    
    # Tab 2: Price Charts
    with tab2:
        display_price_charts(crypto_data, timeframe)
    
    # Tab 3: Volume Analysis
    with tab3:
        display_volume_analysis(crypto_data)
    
    # Tab 4: MLFlow Logs
    with tab4:
        display_mlflow_crypto_logs()
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(30)
        st.rerun()


def display_live_prices(crypto_data):
    """Display live crypto prices with metrics"""
    
    st.header("💰 Live Cryptocurrency Prices")
    
    if not crypto_data:
        st.warning("No crypto data available")
        return
    
    # Display metrics in columns
    cols = st.columns(min(3, len(crypto_data)))
    
    for idx, (name, data) in enumerate(crypto_data.items()):
        col = cols[idx % len(cols)]
        
        current_price = data['current_price']
        previous_close = data['previous_close']
        
        if previous_close > 0:
            change_pct = ((current_price - previous_close) / previous_close) * 100
            delta = f"{change_pct:+.2f}%"
        else:
            delta = "N/A"
        
        with col:
            st.metric(
                label=f"{name} ({data['symbol']})",
                value=f"${current_price:,.2f}",
                delta=delta
            )
    
    # Detailed table
    st.subheader("📋 Detailed Market Data")
    
    table_data = []
    for name, data in crypto_data.items():
        current_price = data['current_price']
        previous_close = data['previous_close']
        change_pct = ((current_price - previous_close) / previous_close) * 100 if previous_close > 0 else 0
        
        table_data.append({
            "Crypto": name,
            "Symbol": data['symbol'],
            "Price": f"${current_price:,.2f}",
            "Change %": f"{change_pct:+.2f}%",
            "Volume": f"{data['volume']:,.0f}",
            "Market Cap": f"${data['market_cap']:,.0f}" if data['market_cap'] > 0 else "N/A",
            "Day High": f"${data['day_high']:,.2f}",
            "Day Low": f"${data['day_low']:,.2f}"
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Last updated timestamp
    st.caption(f"⏱️ Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def display_price_charts(crypto_data, timeframe):
    """Display interactive price charts"""
    
    st.header("📈 Price Movement Charts")
    
    if not crypto_data:
        st.warning("No crypto data available")
        return
    
    # Individual charts for each crypto
    for name, data in crypto_data.items():
        hist = data['history']
        
        if hist.empty:
            continue
        
        st.subheader(f"{name} ({data['symbol']})")
        
        # Create candlestick chart
        fig = go.Figure()
        
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name=name
        ))
        
        # Add moving averages
        if len(hist) >= 7:
            hist['MA7'] = hist['Close'].rolling(window=7).mean()
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['MA7'],
                name='MA7',
                line=dict(color='orange', width=1)
            ))
        
        if len(hist) >= 20:
            hist['MA20'] = hist['Close'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['MA20'],
                name='MA20',
                line=dict(color='blue', width=1)
            ))
        
        fig.update_layout(
            title=f"{name} Price Chart ({timeframe})",
            yaxis_title='Price (USD)',
            xaxis_title='Date',
            height=500,
            xaxis_rangeslider_visible=False
        )
        
        st.plotly_chart(fig, use_container_width=True)


def display_volume_analysis(crypto_data):
    """Display volume analysis"""
    
    st.header("📉 Trading Volume Analysis")
    
    if not crypto_data:
        st.warning("No crypto data available")
        return
    
    # Compare volumes
    st.subheader("Volume Comparison")
    
    volume_data = []
    for name, data in crypto_data.items():
        volume_data.append({
            "Crypto": name,
            "24h Volume": data['volume']
        })
    
    volume_df = pd.DataFrame(volume_data)
    
    if not volume_df.empty:
        fig = go.Figure(data=[
            go.Bar(
                x=volume_df['Crypto'],
                y=volume_df['24h Volume'],
                text=volume_df['24h Volume'].apply(lambda x: f"{x:,.0f}"),
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title='24-Hour Trading Volume Comparison',
            yaxis_title='Volume',
            xaxis_title='Cryptocurrency',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Volume trend charts
    st.subheader("Volume Trends")
    
    for name, data in crypto_data.items():
        hist = data['history']
        
        if hist.empty or 'Volume' not in hist.columns:
            continue
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=hist.index,
            y=hist['Volume'],
            name='Volume',
            marker_color='lightblue'
        ))
        
        fig.update_layout(
            title=f"{name} Volume Trend",
            yaxis_title='Volume',
            xaxis_title='Date',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)


def display_mlflow_crypto_logs():
    """Display MLFlow logged crypto data"""
    
    st.header("🔬 MLFlow Experiment Logs")
    
    if not MLFLOW_AVAILABLE:
        st.error("MLFlow not available")
        return
    
    try:
        tracker = get_tracker()
        recent_runs = tracker.get_recent_runs(max_results=20)
        
        if not recent_runs:
            st.info("No experiments logged yet. Enable logging to start tracking.")
            return
        
        # Filter for crypto-related runs
        crypto_runs = [run for run in recent_runs 
                      if 'crypto' in run.info.run_name.lower() or 
                      'yfinance_crypto' in run.data.params.get('source', '')]
        
        if not crypto_runs:
            st.info("No crypto-specific experiments found.")
            return
        
        st.success(f"Found {len(crypto_runs)} crypto-related experiment runs")
        
        # Display runs table
        runs_data = []
        for run in crypto_runs:
            run_data = {
                'Run Name': run.info.run_name,
                'Start Time': datetime.fromtimestamp(run.info.start_time / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                'Status': run.info.status,
            }
            
            # Add metrics
            if 'rows_fetched' in run.data.metrics:
                run_data['Rows'] = int(run.data.metrics['rows_fetched'])
            
            if 'response_time_seconds' in run.data.metrics:
                run_data['Fetch Time'] = f"{run.data.metrics['response_time_seconds']:.2f}s"
            
            # Add parameters
            if 'source' in run.data.params:
                run_data['Source'] = run.data.params['source']
            
            runs_data.append(run_data)
        
        runs_df = pd.DataFrame(runs_data)
        st.dataframe(runs_df, use_container_width=True, hide_index=True)
        
        # Show connection info
        with st.expander("🔌 MLFlow Connection Details"):
            st.code("""
Name: Bentley_Budget
Host: 127.0.0.1
Port: 3306
Database: mlflow_db
User: root@localhost
            """)
        
    except Exception as e:
        st.error(f"Error loading MLFlow logs: {e}")
        st.exception(e)


if __name__ == "__main__":
    st.set_page_config(
        page_title="Live Crypto Dashboard - BentleyBot",
        page_icon="🔴",
        layout="wide"
    )
    
    display_live_crypto_dashboard()
