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
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# RBAC imports
try:
    from frontend.utils.rbac import RBACManager, Permission, show_login_form, show_user_info
    RBAC_AVAILABLE = True
except ImportError:
    RBAC_AVAILABLE = False

# Import color scheme and styling from home page
try:
    from frontend.styles.colors import COLOR_SCHEME
    from frontend.utils.styling import apply_custom_styling
    
    # Page config
    st.set_page_config(
        page_title="Live Crypto Dashboard | BBBot",
        page_icon="🔴",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply home page styling first
    apply_custom_styling()

    if RBAC_AVAILABLE:
        RBACManager.init_session_state()
        show_user_info()
        if not RBACManager.is_authenticated() or not RBACManager.has_permission(Permission.VIEW_CRYPTO):
            st.error("🚫 Access Denied - Requires Client, Investor, or Admin role")
            show_login_form()
            st.stop()
        # Hide admin-only pages 6–8 from sidebar for non-ADMIN users
        if not RBACManager.has_permission(Permission.VIEW_TRADING_BOT):
            st.markdown(
                f"""
                <style>
                [data-testid=\"stSidebarNav\"] li:nth-child(6),
                [data-testid=\"stSidebarNav\"] li:nth-child(7),
                [data-testid=\"stSidebarNav\"] li:nth-child(8) {{
                    display: none !important;
                }}
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
        color: #FFFFFF !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }}
    
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {{
        color: #FFFFFF !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }}
    
    [data-testid="stMetricDelta"],
    [data-testid="stMetricDelta"] * {{
        color: #FFFFFF !important;
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
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }}
    
    /* Headers and text */
    h1, h2, h3, h4, h5, h6, p, span, div {{
        color: #FFFFFF !important;
    }}

    /* DROPDOWN MENU OPTIONS - Ensure visibility */
    [data-baseweb="popover"],
    [data-baseweb="menu"] {{
        background-color: {COLOR_SCHEME['secondary']} !important;
    }}
    
    [data-baseweb="menu"] li,
    [role="option"] {{
        background-color: {COLOR_SCHEME['secondary']} !important;
        color: #FFFFFF !important;
    }}
    
    [data-baseweb="menu"] li:hover,
    [role="option"]:hover {{
        background-color: rgba(6, 182, 212, 0.2) !important;
        color: #FFFFFF !important;
    }}

    /* Sidebar styling - prevent color changes */
    [data-testid="stSidebar"] {{
        background-color: {COLOR_SCHEME['secondary']} !important;
    }}
    
    [data-testid="stSidebar"] * {{
        color: #FFFFFF !important;
    }}
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label {{
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }}

    /* Ensure table text is bright white and readable */
    table, th, td {{
        color: #FFFFFF !important;
    }}

    /* Ensure helper text and captions are not dimmed */
    small, .stCaption, [data-testid="stCaptionContainer"] * {{
        color: #FFFFFF !important;
        opacity: 1 !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    
except ImportError:
    # Fallback if frontend modules not available
    st.warning("⚠️ Styling modules not found. Using fallback styles.")


def fetch_crypto_market_data(selected_cryptos, crypto_pairs, timeframe):
    """Fetch crypto history in one batch and derive display metrics from OHLCV."""

    selected_symbols = [crypto_pairs[name] for name in selected_cryptos]
    errors = []
    crypto_data = {}
    downloaded = pd.DataFrame()

    if YFINANCE_AVAILABLE:
        try:
            downloaded = yf.download(
                selected_symbols,
                period=timeframe,
                auto_adjust=False,
                progress=False,
                threads=True,
                group_by="ticker",
            )
        except Exception as e:
            downloaded = pd.DataFrame()
            errors.append(f"Batch history download failed: {e}")
    else:
        errors.append("yfinance unavailable, using CoinMarketCap fallback quotes")

    cmc_symbol_map = {
        name: symbol.split("-")[0].upper()
        for name, symbol in crypto_pairs.items()
    }
    requested_cmc_symbols = [cmc_symbol_map[name] for name in selected_cryptos]
    cmc_quotes = fetch_coinmarketcap_quotes(requested_cmc_symbols)

    for name in selected_cryptos:
        symbol = crypto_pairs[name]
        cmc_symbol = cmc_symbol_map[name]
        cmc_quote = cmc_quotes.get(cmc_symbol, {})
        data_source = "Yahoo"

        hist = pd.DataFrame()
        if isinstance(downloaded, pd.DataFrame) and not downloaded.empty:
            try:
                if isinstance(downloaded.columns, pd.MultiIndex):
                    if symbol in downloaded.columns.get_level_values(0):
                        hist = downloaded[symbol].dropna(how="all")
                else:
                    # Single-symbol download returns flat columns.
                    hist = downloaded.dropna(how="all")
            except Exception:
                hist = pd.DataFrame()

        close_series = hist["Close"] if not hist.empty and "Close" in hist.columns else pd.Series(dtype=float)
        latest_close = float(close_series.iloc[-1]) if not close_series.empty else 0.0
        previous_close = float(close_series.iloc[-2]) if len(close_series) > 1 else latest_close

        if not hist.empty and {"High", "Low"}.issubset(hist.columns):
            day_high = float(hist["High"].iloc[-1])
            day_low = float(hist["Low"].iloc[-1])
        else:
            day_high = latest_close
            day_low = latest_close

        volume_val = 0.0
        if not hist.empty and "Volume" in hist.columns:
            volume_val = float(hist["Volume"].iloc[-1] or 0.0)
        market_cap_val = 0.0

        if hist.empty:
            fallback_price = float(cmc_quote.get("price") or 0.0)
            fallback_prev = float(cmc_quote.get("previous_close") or fallback_price)
            fallback_volume = float(cmc_quote.get("volume") or 0.0)
            fallback_mcap = float(cmc_quote.get("market_cap") or 0.0)

            if fallback_price > 0:
                latest_close = fallback_price
                previous_close = fallback_prev
                day_high = fallback_price
                day_low = fallback_price
                volume_val = fallback_volume
                market_cap_val = fallback_mcap
                data_source = "CoinMarketCap"
                errors.append(f"{name}: using CoinMarketCap fallback quote")
            else:
                data_source = "Unavailable"
                errors.append(f"{name}: no historical data returned and no CoinMarketCap fallback quote")

        crypto_data[name] = {
            "symbol": symbol,
            "history": hist,
            "current_price": latest_close,
            "previous_close": previous_close,
            "volume": volume_val,
            "market_cap": market_cap_val,
            "day_high": day_high,
            "day_low": day_low,
            "source": data_source,
        }

    return crypto_data, errors


def render_source_badge_html(source):
    """Render a color badge while keeping text fully white for readability."""

    source_lower = str(source).lower()
    if source_lower == "yahoo":
        return (
            "<span style='background:#0f766e;color:#FFFFFF;padding:2px 8px;"
            "border-radius:999px;font-size:0.8rem;font-weight:700;'>Yahoo</span>"
        )
    if source_lower == "coinmarketcap":
        return (
            "<span style='background:#b45309;color:#FFFFFF;padding:2px 8px;"
            "border-radius:999px;font-size:0.8rem;font-weight:700;'>CoinMarketCap</span>"
        )
    return (
        "<span style='background:#b91c1c;color:#FFFFFF;padding:2px 8px;"
        "border-radius:999px;font-size:0.8rem;font-weight:700;'>Unavailable</span>"
    )


@st.cache_data(ttl=120)
def fetch_coinmarketcap_quotes(symbols):
    """Best-effort fallback quotes from public CoinMarketCap data API."""

    if not symbols:
        return {}

    url = (
        "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing"
        "?start=1&limit=5000&sortBy=market_cap&sortType=desc&convert=USD"
    )
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError):
        return {}

    entries = payload.get("data", {}).get("cryptoCurrencyList", [])
    wanted = {symbol.upper() for symbol in symbols}
    results = {}

    for entry in entries:
        entry_symbol = str(entry.get("symbol", "")).upper()
        if entry_symbol not in wanted:
            continue

        quotes = entry.get("quotes") or []
        usd_quote = quotes[0] if quotes else {}

        price = float(usd_quote.get("price") or 0.0)
        pct_24h = float(usd_quote.get("percentChange24h") or 0.0)
        previous_close = price
        if price > 0 and pct_24h > -99.99:
            previous_close = price / (1 + (pct_24h / 100.0))

        results[entry_symbol] = {
            "price": price,
            "previous_close": previous_close,
            "volume": float(usd_quote.get("volume24h") or 0.0),
            "market_cap": float(usd_quote.get("marketCap") or 0.0),
        }

    return results

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
    from bbbot1_pipeline.mlflow_config import print_connection_details, get_mlflow_config, MYSQL_WORKBENCH_INFO
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
            config = get_mlflow_config()
            st.sidebar.code(f"""
Connection: Bentley_Budget
Host: {config['host']}:{config['port']}
Database: {config['database']}
User: {config['user']}@localhost
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
        
        crypto_data, fetch_errors = fetch_crypto_market_data(
            selected_cryptos=selected_cryptos,
            crypto_pairs=crypto_pairs,
            timeframe=timeframe,
        )
        for fetch_error in fetch_errors:
            st.warning(f"⚠️ {fetch_error}")
        
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
            st.markdown(render_source_badge_html(data.get("source", "Unknown")), unsafe_allow_html=True)
    
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
            "Data Source": data.get('source', 'Unknown'),
            "Price": f"${current_price:,.2f}",
            "Change %": f"{change_pct:+.2f}%",
            "Volume": f"{data['volume']:,.0f}",
            "Market Cap": f"${data['market_cap']:,.0f}" if data['market_cap'] > 0 else "N/A",
            "Day High": f"${data['day_high']:,.2f}",
            "Day Low": f"${data['day_low']:,.2f}"
        })
    
    df = pd.DataFrame(table_data)

    table_for_html = df.copy()
    table_for_html["Data Source"] = table_for_html["Data Source"].apply(render_source_badge_html)

    st.markdown(
        table_for_html.to_html(index=False, escape=False),
        unsafe_allow_html=True,
    )
    
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
            config = get_mlflow_config()
            st.code(f"""
Name: Bentley_Budget
Host: {config['host']}
Port: {config['port']}
Database: {config['database']}
User: {config['user']}@localhost
            """)
        
    except Exception as e:
        st.error(f"Error loading MLFlow logs: {e}")
        st.exception(e)


display_live_crypto_dashboard()
