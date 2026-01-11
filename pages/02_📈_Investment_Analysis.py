"""
Investment Analysis Page with MLFlow Integration
Displays portfolio analysis with logged experiments and metrics

PERFORMANCE OPTIMIZATIONS (Dec 25, 2025):
- Added @st.cache_data to yfinance calls (1 hour TTL)
- Prevents API rate limiting on page refresh
- Reduces load time by 80%+ on cached data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import color scheme and styling from home page
try:
    from frontend.styles.colors import COLOR_SCHEME
    from frontend.utils.styling import apply_custom_styling
    
    # Apply home page styling first
    apply_custom_styling()
    
    # Add page-specific styling
    st.markdown(f"""
    <style>
    
    /* Ensure tab content has consistent background */
    .stTabs [data-baseweb="tab-panel"] {{
        background: transparent;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        background: transparent;
    }}
    
    /* CRITICAL: Force Streamlit metrics to match home page exactly */
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
    
    /* Tab labels - WHITE with ORANGE hover */
    .stTabs [data-baseweb="tab"] {{
        color: {COLOR_SCHEME['text']} !important;
        font-weight: 500 !important;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        color: #FF8C00 !important;
        background-color: rgba(255, 140, 0, 0.1) !important;
    }}
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: {COLOR_SCHEME['primary']} !important;
        border-bottom-color: {COLOR_SCHEME['primary']} !important;
    }}
    
    /* Caption text */
    .stCaption {{
        color: rgba(230, 238, 248, 0.8) !important;
    }}
    
    /* Ensure all text in columns is white */
    .element-container {{
        color: {COLOR_SCHEME['text']} !important;
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

    /* DROPDOWN MENU OPTIONS - Fix invisible text in dropdown */
    [data-baseweb="popover"] {{
        background-color: {COLOR_SCHEME['secondary']} !important;
    }}
    
    [data-baseweb="menu"] {{
        background-color: {COLOR_SCHEME['secondary']} !important;
    }}
    
    [data-baseweb="menu"] li {{
        background-color: {COLOR_SCHEME['secondary']} !important;
        color: {COLOR_SCHEME['text']} !important;
    }}
    
    [data-baseweb="menu"] li:hover {{
        background-color: rgba(6, 182, 212, 0.2) !important;
        color: {COLOR_SCHEME['text']} !important;
    }}
    
    /* Dropdown option text */
    [role="option"] {{
        background-color: {COLOR_SCHEME['secondary']} !important;
        color: {COLOR_SCHEME['text']} !important;
    }}
    
    [role="option"]:hover {{
        background-color: rgba(6, 182, 212, 0.2) !important;
        color: {COLOR_SCHEME['text']} !important;
    }}
    
    /* Select dropdown input field */
    [data-baseweb="select"] > div {{
        background-color: rgba(15, 23, 42, 0.6) !important;
        color: {COLOR_SCHEME['text']} !important;
    }}
    
    /* Selected value in dropdown */
    [data-baseweb="select"] input {{
        color: {COLOR_SCHEME['text']} !important;
    }}
    
    [data-baseweb="select"] span {{
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

# Import RBAC and broker connections
try:
    from frontend.utils.rbac import (
        RBACManager,
        Permission,
        show_login_form,
        show_user_info,
        show_permission_denied,
    )
    from frontend.utils.broker_connections import (
        display_broker_connections,
        display_webull_funds,
        display_position_analysis,
        display_connection_health,
    )
    RBAC_AVAILABLE = True
except ImportError:
    RBAC_AVAILABLE = False
    st.warning("⚠️ RBAC system not available.")

# Import multi-source fundamentals fetcher
try:
    from frontend.utils.fundamentals_fetcher import (
        cached_fetch_fundamentals,
        format_fundamental_value
    )
    FUNDAMENTALS_FETCHER_AVAILABLE = True
except ImportError:
    FUNDAMENTALS_FETCHER_AVAILABLE = False

# Import MLFlow tracker
try:
    from bbbot1_pipeline.mlflow_tracker import get_tracker
    from bbbot1_pipeline import load_tickers_config
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    st.warning("⚠️ MLFlow tracker not available. Install bbbot1_pipeline package.")

# Import yfinance if available
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    st.warning("⚠️ yfinance not available. Install with: pip install yfinance")


def display_investment_page():
    """Main investment analysis page with MLFlow integration"""
    
    st.title("📈 Mansa Capital Investment Dashboard")
    st.markdown("Real-time fund tracking with ML experiment logging | *Mansa Capital Funds*")
    
    # Initialize RBAC
    if RBAC_AVAILABLE:
        RBACManager.init_session_state()
        
        # Show login form or user info in sidebar
        if not RBACManager.is_authenticated():
            show_login_form()
            st.info("👈 Please login to access full features")
        else:
            show_user_info()
    
    # Broker Integration Section
    st.markdown("---")
    st.subheader("🔗 Broker Integration")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**Alpaca (Stocks/Crypto)**")
        if st.button("Connect Alpaca", key="alpaca_invest"):
            st.info("Navigate to **💼 Broker Trading** or **🌐 Multi-Broker Trading** to connect")
    
    with col2:
        st.markdown("**MT5 (FOREX/Futures)**")
        if st.button("Connect MT5", key="mt5_invest"):
            st.info("Navigate to **🌐 Multi-Broker Trading** to connect")
    
    with col3:
        st.markdown("**IBKR (Multi-Asset)**")
        if st.button("Connect IBKR", key="ibkr_invest"):
            st.info("Navigate to **🌐 Multi-Broker Trading** to connect")
    
    with col4:
        st.markdown("**Future Brokers**")
        st.caption("QuantConnect, TD Ameritrade, NinjaTrader, Binance")
    
    st.markdown("---")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Analysis Configuration")
    
    # Option to use real portfolio data
    use_real_portfolio = st.sidebar.checkbox(
        "📊 Use My Portfolio",
        value=False,
        help="Load your actual holdings from MySQL database via Appwrite"
    )
    
    # Mansa Capital Fund Names
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
    
    # Load tickers based on source
    if use_real_portfolio and APPWRITE_SERVICES_AVAILABLE:
        # Fetch user's actual portfolio
        from services.portfolio import get_portfolio_holdings
        
        with st.spinner("Loading your portfolio from database..."):
            user_id = st.session_state.get('user_id', 'demo_user')
            portfolio_data = get_portfolio_holdings(user_id)
            
            if "error" in portfolio_data:
                st.sidebar.warning(f"Could not load portfolio: {portfolio_data['error']}")
                st.sidebar.info("Using demo Mansa funds instead")
                available_tickers = list(MANSA_FUNDS.keys())
            else:
                # Extract tickers from user's holdings
                holdings = portfolio_data.get('holdings', [])
                if holdings:
                    available_tickers = [h['ticker'] for h in holdings]
                    st.sidebar.success(f"✅ Loaded {len(available_tickers)} holdings from your portfolio")
                else:
                    st.sidebar.info("No holdings found. Using demo Mansa funds.")
                    available_tickers = list(MANSA_FUNDS.keys())
    elif MLFLOW_AVAILABLE:
        # Load from MLFlow config
        try:
            config = load_tickers_config()
            available_tickers = config['tickers']['all']
        except:
            available_tickers = list(MANSA_FUNDS.keys())
    else:
        # Default demo tickers
        available_tickers = list(MANSA_FUNDS.keys())
    
    # Ticker selection with Mansa fund names
    ticker_options = [f"{ticker} - {MANSA_FUNDS.get(ticker, ticker)}" for ticker in available_tickers]
    selected_options = st.sidebar.multiselect(
        "Select Mansa Funds to Analyze",
        ticker_options,
        default=[f"{t} - {MANSA_FUNDS.get(t, t)}" for t in ['IONQ', 'QBTS', 'SOUN', 'RGTI']]
    )
    
    # Extract ticker symbols from selections
    selected_tickers = [opt.split(' - ')[0] for opt in selected_options]
    
    # Date range selection
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    date_range = st.sidebar.date_input(
        "Analysis Period",
        value=[start_date, end_date],
        max_value=datetime.now()
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
    
    # Enable MLFlow logging toggle
    enable_logging = st.sidebar.checkbox(
        "🔬 Enable MLFlow Logging",
        value=True,
        help="Log analysis to MLFlow for tracking"
    )
    
    if not selected_tickers:
        st.info("👈 Select tickers from the sidebar to begin analysis")
        return
    
    # Determine which tabs to show based on permissions
    if RBAC_AVAILABLE and RBACManager.require_connections_access():
        # Show all tabs including connections for authorized users
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Portfolio Overview",
            "🔬 MLFlow Experiments",
            "📈 Technical Analysis",
            "💰 Fundamental Ratios",
            "🔗 Broker Connections"
        ])
        
        # Tab 5: Broker Connections (Restricted)
        with tab5:
            display_broker_connections_tab()
    else:
        # Show standard tabs without connections
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Portfolio Overview",
            "🔬 MLFlow Experiments",
            "📈 Technical Analysis",
            "💰 Fundamental Ratios"
        ])
    
    # Tab 1: Portfolio Overview
    with tab1:
        display_portfolio_overview(selected_tickers, start_date, end_date, enable_logging, MANSA_FUNDS)
    
    # Tab 2: MLFlow Experiments
    with tab2:
        display_mlflow_experiments(selected_tickers)
    
    # Tab 3: Technical Analysis
    with tab3:
        display_technical_analysis(selected_tickers, start_date, end_date, MANSA_FUNDS)
    
    # Tab 4: Fundamental Ratios
    with tab4:
        display_fundamental_ratios(selected_tickers, enable_logging)


@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_stock_data(ticker, start_date, end_date):
    """Cached function to fetch stock data from yfinance
    
    Args:
        ticker: Stock ticker symbol
        start_date: Start date for data
        end_date: End date for data
    
    Returns:
        DataFrame with stock data or None if error
    """
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        return df if not df.empty else None
    except Exception as e:
        st.warning(f"⚠️ Failed to fetch {ticker}: {str(e)}")
        return None


def display_portfolio_overview(tickers, start_date, end_date, enable_logging, fund_names=None):
    """Display portfolio performance overview
    
    Args:
        tickers: List of ticker symbols
        start_date: Analysis start date
        end_date: Analysis end date
        enable_logging: Whether to log to MLFlow
        fund_names: Dict mapping ticker symbols to fund names (optional)
    """
    
    st.header("📊 Mansa Capital Fund Performance")
    
    if not YFINANCE_AVAILABLE:
        st.error("yfinance package required for portfolio data")
        return
    
    # Fetch data with timing
    start_time = time.time()
    
    with st.spinner("Fetching portfolio data..."):
        data_frames = []
        
        for ticker in tickers:
            try:
                df = fetch_stock_data(ticker, start_date, end_date)
                if not df.empty:
                    # Handle MultiIndex columns from yfinance
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    # Reset index to make Date a column
                    df = df.reset_index()
                    
                    # Add ticker column
                    df['Ticker'] = ticker
                    
                    # Select only the columns we need (handle missing columns gracefully)
                    cols_to_keep = []
                    for col in ['Date', 'Ticker', 'Close', 'Volume']:
                        if col in df.columns or col == 'Ticker':
                            cols_to_keep.append(col)
                    
                    if 'Close' in df.columns and 'Date' in df.columns:
                        # Reset index to avoid duplicate index errors during concat
                        df_to_add = df[cols_to_keep].reset_index(drop=True)
                        data_frames.append(df_to_add)
                    else:
                        st.warning(f"⚠️ {ticker}: Missing required columns")
            except Exception as e:
                st.warning(f"⚠️ Could not fetch {ticker}: {e}")
        
        if not data_frames:
            st.error("No data available for selected tickers")
            return
        
        # Concatenate with ignore_index=True to ensure clean index
        portfolio_df = pd.concat(data_frames, ignore_index=True, sort=False)
        
        # Add fund names column for display
        if fund_names:
            portfolio_df['Fund Name'] = portfolio_df['Ticker'].map(fund_names)
        else:
            portfolio_df['Fund Name'] = portfolio_df['Ticker']
        
        # Ensure Date column is datetime
        portfolio_df['Date'] = pd.to_datetime(portfolio_df['Date'])
    
    fetch_time = time.time() - start_time
    
    # Log to MLFlow if enabled
    if enable_logging and MLFLOW_AVAILABLE:
        try:
            tracker = get_tracker()
            tracker.log_data_ingestion(
                source="yfinance",
                tickers=tickers,
                rows_fetched=len(portfolio_df),
                success=True,
                response_time=fetch_time
            )
            st.success(f"✅ Logged data ingestion to MLFlow ({fetch_time:.2f}s)")
        except Exception as e:
            st.warning(f"⚠️ MLFlow logging failed: {e}")
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        try:
            latest_data = portfolio_df[portfolio_df['Date'] == portfolio_df['Date'].max()]
            latest_value = float(latest_data['Close'].sum())
            st.metric("Portfolio Value", f"${latest_value:,.2f}")
        except (TypeError, ValueError) as e:
            st.metric("Portfolio Value", "N/A")
            st.caption(f"Error: {e}")
    
    with col2:
        st.metric("Assets", len(tickers))
    
    with col3:
        try:
            latest_data = portfolio_df[portfolio_df['Date'] == portfolio_df['Date'].max()]
            total_volume = float(latest_data['Volume'].sum())
            st.metric("Daily Volume", f"{total_volume:,.0f}")
        except (TypeError, ValueError) as e:
            st.metric("Daily Volume", "N/A")
    
    with col4:
        try:
            # Calculate portfolio return
            first_data = portfolio_df[portfolio_df['Date'] == portfolio_df['Date'].min()]
            first_value = float(first_data['Close'].sum())
            latest_value = float(latest_data['Close'].sum())
            portfolio_return = ((latest_value - first_value) / first_value) * 100 if first_value > 0 else 0
            st.metric("Total Return", f"{portfolio_return:+.2f}%")
        except (TypeError, ValueError, ZeroDivisionError) as e:
            st.metric("Total Return", "N/A")
    
    # Plot portfolio performance
    st.subheader("Fund Price Performance")
    
    try:
        # Ensure data is valid for plotting
        plot_df = portfolio_df[['Date', 'Close', 'Fund Name']].dropna()
        
        if not plot_df.empty:
            fig = px.line(
                plot_df,
                x='Date',
                y='Close',
                color='Fund Name',
                title='Mansa Capital Fund Price History',
                labels={'Close': 'Price ($)', 'Date': 'Date', 'Fund Name': 'Fund'}
            )
            
            fig.update_layout(
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No valid data to plot")
    except Exception as e:
        st.error(f"Unable to create price chart: {e}")
        st.info("Data shape: " + str(portfolio_df.shape) + " | Columns: " + str(list(portfolio_df.columns)))
    
    # Individual ticker performance
    st.subheader("Individual Ticker Performance")
    
    ticker_metrics = []
    for ticker in tickers:
        ticker_data = portfolio_df[portfolio_df['Ticker'] == ticker]
        if not ticker_data.empty:
            first_price = ticker_data['Close'].iloc[0]
            last_price = ticker_data['Close'].iloc[-1]
            pct_change = ((last_price - first_price) / first_price) * 100 if first_price > 0 else 0
            
            ticker_metrics.append({
                'Ticker': ticker,
                'Start Price': f"${first_price:.2f}",
                'Current Price': f"${last_price:.2f}",
                'Change': f"{pct_change:+.2f}%",
                'Volume': f"{ticker_data['Volume'].iloc[-1]:,.0f}"
            })
    
    st.dataframe(
        pd.DataFrame(ticker_metrics),
        use_container_width=True,
        hide_index=True
    )


def display_mlflow_experiments(tickers):
    """Display MLFlow logged experiments"""
    
    st.header("🔬 MLFlow Experiment Tracking")
    
    if not MLFLOW_AVAILABLE:
        st.error("MLFlow tracker not available. Install bbbot1_pipeline package.")
        return
    
    try:
        tracker = get_tracker()
        
        # Get recent runs
        st.subheader("Recent Experiments")
        
        max_results = st.slider("Number of runs to display", 5, 50, 20)
        recent_runs = tracker.get_recent_runs(max_results=max_results)
        
        if not recent_runs:
            st.info("No experiments logged yet. Enable logging in the sidebar to start tracking.")
            return
        
        # Display runs in a table
        runs_data = []
        for run in recent_runs:
            run_data = {
                'Run Name': run.info.run_name,
                'Start Time': datetime.fromtimestamp(run.info.start_time / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                'Status': run.info.status,
            }
            
            # Add key parameters
            if 'ticker' in run.data.params:
                run_data['Ticker'] = run.data.params['ticker']
            
            if 'source' in run.data.params:
                run_data['Source'] = run.data.params['source']
            
            # Add key metrics
            for metric_name in ['pe_ratio', 'total_value', 'rows_fetched', 'response_time_seconds']:
                if metric_name in run.data.metrics:
                    run_data[metric_name] = f"{run.data.metrics[metric_name]:.2f}"
            
            runs_data.append(run_data)
        
        runs_df = pd.DataFrame(runs_data)
        st.dataframe(runs_df, use_container_width=True, hide_index=True)
        
        # Ticker-specific analysis
        st.subheader("Ratio Analysis by Ticker")
        
        selected_ticker = st.selectbox("Select ticker for detailed view", tickers)
        
        if selected_ticker:
            ratio_runs = tracker.get_ratio_analysis_runs(ticker=selected_ticker, max_results=10)
            
            if ratio_runs:
                st.success(f"Found {len(ratio_runs)} ratio analysis runs for {selected_ticker}")
                
                # Extract and display ratio trends
                ratio_data = []
                for run in ratio_runs:
                    entry = {
                        'Date': run.data.params.get('report_date', 'N/A')
                    }
                    entry.update(run.data.metrics)
                    ratio_data.append(entry)
                
                ratio_df = pd.DataFrame(ratio_data)
                st.dataframe(ratio_df, use_container_width=True)
                
                # Plot ratio trends if we have data
                if len(ratio_df) > 1 and 'Date' in ratio_df.columns:
                    numeric_cols = ratio_df.select_dtypes(include=['float64', 'int64']).columns
                    
                    if len(numeric_cols) > 0:
                        selected_metric = st.selectbox("Select metric to plot", numeric_cols)
                        
                        try:
                            # Ensure Date column is valid and data is clean
                            plot_df = ratio_df[['Date', selected_metric]].dropna()
                            
                            if not plot_df.empty:
                                fig = px.line(
                                    plot_df,
                                    x='Date',
                                    y=selected_metric,
                                    title=f'{selected_metric} Trend for {selected_ticker}',
                                    markers=True
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("No valid data to plot")
                        except Exception as e:
                            st.error(f"Unable to create trend chart: {e}")
            else:
                st.info(f"No ratio analysis runs found for {selected_ticker}")
        
    except Exception as e:
        st.error(f"Error loading MLFlow experiments: {e}")
        st.exception(e)


def display_technical_analysis(tickers, start_date, end_date, fund_names=None):
    """Display technical analysis charts
    
    Args:
        tickers: List of ticker symbols
        start_date: Analysis start date
        end_date: Analysis end date
        fund_names: Dict mapping ticker symbols to fund names (optional)
    """
    
    st.header("📈 Technical Analysis")
    
    if not YFINANCE_AVAILABLE:
        st.error("yfinance package required")
        return
    
    # Create ticker options with fund names
    if fund_names:
        ticker_options = {f"{ticker} - {fund_names.get(ticker, ticker)}": ticker for ticker in tickers}
        selected_option = st.selectbox(
            "Select Mansa fund for technical analysis", 
            list(ticker_options.keys()), 
            key="tech_ticker"
        )
        selected_ticker = ticker_options[selected_option]
        display_name = fund_names.get(selected_ticker, selected_ticker)
    else:
        selected_ticker = st.selectbox("Select ticker for technical analysis", tickers, key="tech_ticker")
        display_name = selected_ticker
    
    with st.spinner(f"Analyzing {display_name}..."):
        try:
            df = fetch_stock_data(selected_ticker, start_date, end_date)
            
            if df is None or df.empty:
                st.warning(f"No data available for {selected_ticker}")
                return
            
            # Handle MultiIndex columns from yfinance
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Verify required columns exist
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                st.error(f"Missing columns: {missing_cols}")
                return
            
            # Calculate moving averages
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA50'] = df['Close'].rolling(window=50).mean()
            df['MA200'] = df['Close'].rolling(window=200).mean()
            
            # Create candlestick chart with moving averages
            fig = go.Figure()
            
            # Candlestick
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Price'
            ))
            
            # Moving averages
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20', line=dict(color='orange', width=1)))
            fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], name='MA50', line=dict(color='blue', width=1)))
            fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], name='MA200', line=dict(color='red', width=1)))
            
            fig.update_layout(
                title=f'{display_name} Price with Moving Averages',
                yaxis_title='Price ($)',
                xaxis_title='Date',
                height=600,
                xaxis_rangeslider_visible=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Volume chart
            fig_volume = go.Figure()
            fig_volume.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume'))
            fig_volume.update_layout(
                title=f'{display_name} Trading Volume',
                yaxis_title='Volume',
                xaxis_title='Date',
                height=300
            )
            
            st.plotly_chart(fig_volume, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error in technical analysis: {e}")


def display_fundamental_ratios(tickers, enable_logging):
    """Display and log fundamental ratios with multi-source support"""
    
    st.header("💰 Fundamental Analysis")
    
    selected_ticker = st.selectbox("Select ticker for fundamentals", tickers, key="fund_ticker")
    
    # Data source selection
    if FUNDAMENTALS_FETCHER_AVAILABLE:
        data_source = st.radio(
            "Data Source",
            [
                "Auto (Alpha Vantage → yfinance)",
                "Alpha Vantage only",
                "yfinance only",
                "Tiingo only"
            ],
            horizontal=True,
            help="Auto tries Alpha Vantage first, then falls back to yfinance. Configure API keys in .env file."
        )
        
        # Determine source priority based on selection
        if "Auto" in data_source:
            use_multi_source = True
            source_priority = ['alpha_vantage', 'yfinance']
        elif "Alpha Vantage only" in data_source:
            use_multi_source = True
            source_priority = ['alpha_vantage']
        elif "Tiingo only" in data_source:
            use_multi_source = True
            source_priority = ['tiingo']
        else:  # yfinance only
            use_multi_source = False
            source_priority = []
    else:
        use_multi_source = False
        source_priority = []
        st.info("💡 Using yfinance only. Install multi-source fetcher for Alpha Vantage support.")
    
    with st.spinner(f"Fetching fundamentals for {selected_ticker}..."):
        try:
            fundamentals = {}
            data_source_used = "unknown"
            raw_data = {}  # Store raw data for "View All" section
            
            # Try multi-source fetcher first
            if use_multi_source and FUNDAMENTALS_FETCHER_AVAILABLE:
                # Use custom source priority
                from frontend.utils.fundamentals_fetcher import fetch_fundamentals_multi_source
                data = fetch_fundamentals_multi_source(selected_ticker, sources=source_priority)
                raw_data = data  # Store for display
                
                if data:
                    data_source_used = data.get('source', 'unknown')
                    
                    # Custom styling for Tiingo data source
                    if data_source_used == 'tiingo':
                        st.markdown(
                            '<div style="padding: 0.5rem; border-radius: 0.3rem; '
                            'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
                            'color: white; font-weight: 600; text-align: center; '
                            'box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);">' 
                            f'✅ Data from: <strong>{data_source_used.upper()}</strong> (Premium)' 
                            '</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.success(f"✅ Data from: **{data_source_used}**")
                    
                    # Map to display format
                    fundamentals = {
                        'Market Cap': data.get('market_cap', 'N/A'),
                        'P/E Ratio': data.get('pe_ratio', 'N/A'),
                        'Forward P/E': data.get('forward_pe', 'N/A'),
                        'PEG Ratio': data.get('peg_ratio', 'N/A'),
                        'Price to Book': data.get('price_to_book', 'N/A'),
                        'Price to Sales': data.get('price_to_sales', 'N/A'),
                        'Dividend Yield': data.get('dividend_yield', 'N/A'),
                        'EPS': data.get('eps', 'N/A'),
                        'Revenue TTM': data.get('revenue_ttm', 'N/A'),
                        'Profit Margin': data.get('profit_margin', 'N/A'),
                        'Operating Margin': data.get('operating_margin', 'N/A'),
                        'ROE': data.get('roe', 'N/A'),
                        'ROA': data.get('roa', 'N/A'),
                        'Beta': data.get('beta', 'N/A'),
                        '52W High': data.get('52_week_high', 'N/A'),
                        '52W Low': data.get('52_week_low', 'N/A'),
                        'SMA 50': data.get('50_day_ma', 'N/A'),
                        'SMA 200': data.get('200_day_ma', 'N/A'),
                    }
                    
                    # Add additional fields based on source
                    if data_source_used == 'alpha_vantage':
                        fundamentals.update({
                            'Sector': data.get('sector', 'N/A'),
                            'Industry': data.get('industry', 'N/A'),
                            'Analyst Target': data.get('analyst_target_price', 'N/A'),
                            'Q. Rev Growth': data.get('quarterly_revenue_growth', 'N/A'),
                            'Q. Earnings Growth': data.get('quarterly_earnings_growth', 'N/A'),
                        })
                    elif data_source_used == 'tiingo':
                        # Show Tiingo-specific info if available
                        if data.get('description'):
                            with st.expander("📋 Company Description"):
                                st.write(data.get('description'))
                        
                        # Add exchange and date info
                        tiingo_info = []
                        if data.get('exchange') != 'N/A':
                            tiingo_info.append(f"Exchange: {data.get('exchange')}")
                        if data.get('start_date') != 'N/A':
                            tiingo_info.append(f"Data Since: {data.get('start_date')}")
                        
                        if tiingo_info:
                            st.caption(" | ".join(tiingo_info))
                else:
                    # Only show errors if this is a single-source mode
                    # For Auto mode, silently fall back to yfinance
                    if len(source_priority) == 1:
                        if 'alpha_vantage' in source_priority:
                            st.warning("⚠️ Alpha Vantage unavailable, trying yfinance fallback...")
                        elif 'tiingo' in source_priority:
                            st.warning("⚠️ Tiingo unavailable, trying yfinance fallback...")
                            st.info("💡 **Tiingo Subscription Note:**\n"
                                   "If you just purchased a subscription, API access may take 15-30 minutes to activate. "
                                   "Check your email for confirmation and API key updates.")
            
            # Fallback to yfinance
            if not fundamentals and YFINANCE_AVAILABLE:
                ticker = yf.Ticker(selected_ticker)
                info = ticker.info
                raw_data = info  # Store for display
                data_source_used = "yfinance"
                
                # Extract key fundamentals from yfinance
                fundamentals = {
                    'Market Cap': info.get('marketCap', 'N/A'),
                    'P/E Ratio': info.get('trailingPE', 'N/A'),
                    'Forward P/E': info.get('forwardPE', 'N/A'),
                    'PEG Ratio': info.get('pegRatio', 'N/A'),
                    'Price to Book': info.get('priceToBook', 'N/A'),
                    'Dividend Yield': info.get('dividendYield', 'N/A'),
                    'ROE': info.get('returnOnEquity', 'N/A'),
                    'ROA': info.get('returnOnAssets', 'N/A'),
                    'Debt to Equity': info.get('debtToEquity', 'N/A'),
                    'Current Ratio': info.get('currentRatio', 'N/A'),
                    'Revenue': info.get('totalRevenue', 'N/A'),
                    'Profit Margin': info.get('profitMargins', 'N/A'),
                }
            
            # Final check - if still no data, show comprehensive error
            if not fundamentals or len(fundamentals) == 0:
                st.error(f"❌ Unable to fetch fundamentals for **{selected_ticker}** from any source")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.warning("**Possible Issues:**")
                    st.markdown(
                        "- Invalid ticker symbol\n"
                        "- Ticker not found in databases\n"
                        "- Rate limits exceeded\n"
                        "- Network connectivity issues"
                    )
                
                with col2:
                    st.info("**Solutions:**")
                    st.markdown(
                        "- Verify ticker symbol is correct\n"
                        "- Try 'Auto' mode for multiple sources\n"
                        "- Wait 5-10 minutes if rate limited\n"
                        "- Check API keys in `.env` file"
                    )
                
                # Show which sources were tried
                if use_multi_source and source_priority:
                    st.caption(f"📍 Tried sources: {', '.join(source_priority)}")
                
                return
            
            # Display in columns
            col1, col2, col3 = st.columns(3)
            
            keys = list(fundamentals.keys())
            for i, key in enumerate(keys):
                col = [col1, col2, col3][i % 3]
                value = fundamentals[key]
                
                # Format value with improved handling
                if use_multi_source and FUNDAMENTALS_FETCHER_AVAILABLE:
                    value_str = format_fundamental_value(key.lower().replace(' ', '_'), value)
                else:
                    # Original yfinance formatting
                    if isinstance(value, (int, float)):
                        if 'Cap' in key or 'Revenue' in key:
                            if value >= 1_000_000_000_000:
                                value_str = f"${value/1_000_000_000_000:.2f}T"
                            elif value >= 1_000_000_000:
                                value_str = f"${value/1_000_000_000:.2f}B"
                            elif value >= 1_000_000:
                                value_str = f"${value/1_000_000:.2f}M"
                            else:
                                value_str = f"${value:,.0f}"
                        elif 'Ratio' in key or 'Margin' in key or 'Yield' in key or key in ['ROE', 'ROA']:
                            value_str = f"{value:.2f}"
                        else:
                            value_str = f"{value:,.2f}"
                    else:
                        value_str = str(value)
                
                col.metric(key, value_str)
            
            # Log to MLFlow if enabled
            if enable_logging and MLFLOW_AVAILABLE:
                try:
                    # Filter numeric ratios for MLFlow
                    numeric_ratios = {
                        k: v for k, v in fundamentals.items()
                        if isinstance(v, (int, float)) and v != 'N/A'
                    }
                    
                    if numeric_ratios:
                        tracker = get_tracker()
                        tracker.log_fundamental_ratios(
                            ticker=selected_ticker,
                            report_date=datetime.now().strftime('%Y-%m-%d'),
                            ratios=numeric_ratios,
                            source="yfinance"
                        )
                        
                        st.success(f"✅ Logged {len(numeric_ratios)} ratios to MLFlow")
                except Exception as e:
                    st.warning(f"⚠️ MLFlow logging failed: {e}")
            
            # Display full info in expander with custom styling
            with st.expander("📋 View All Available Data"):
                # Add custom CSS for the data display with visible JSON
                st.markdown("""
                <style>
                .data-section {
                    padding: 1rem;
                    border-radius: 0.5rem;
                    margin-bottom: 1rem;
                }
                .alpha-vantage-data {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .tiingo-data {
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                }
                .yfinance-data {
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    color: #1a1a1a;
                }
                
                /* Force JSON viewer to be visible with proper colors */
                .stJson {
                    background-color: rgba(28, 28, 28, 0.95) !important;
                    padding: 1.5rem !important;
                    border-radius: 0.5rem !important;
                    border: 2px solid rgba(255, 140, 0, 0.3) !important;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
                }
                
                /* JSON content colors */
                .stJson pre {
                    color: #e6eef8 !important;
                    font-family: 'Courier New', monospace !important;
                    font-size: 0.9rem !important;
                    line-height: 1.6 !important;
                }
                
                /* JSON syntax highlighting */
                .stJson .token.property {
                    color: #79c0ff !important;
                }
                .stJson .token.string {
                    color: #a5d6ff !important;
                }
                .stJson .token.number {
                    color: #ffa657 !important;
                }
                .stJson .token.boolean {
                    color: #ff7b72 !important;
                }
                .stJson .token.null {
                    color: #8b949e !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Determine which data to show based on source
                if data_source_used == 'alpha_vantage':
                    st.markdown(
                        '<div class="data-section alpha-vantage-data" style="margin-bottom: 1.5rem;">'
                        '<h4 style="margin: 0 0 0.5rem 0; font-size: 1.2rem;">📊 Alpha Vantage Data (Premium)</h4>'
                        '<p style="margin: 0; opacity: 0.9; font-size: 0.9rem;">Source: Alpha Vantage API | Comprehensive Fundamentals</p>'
                        '</div>',
                        unsafe_allow_html=True
                    )
                    # Display with color-coded background
                    st.markdown('<div style="background: rgba(102, 126, 234, 0.1); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #667eea;">', unsafe_allow_html=True)
                    st.json(raw_data if raw_data else fundamentals)
                    st.markdown('</div>', unsafe_allow_html=True)
                        
                elif data_source_used == 'tiingo':
                    st.markdown(
                        '<div class="data-section tiingo-data" style="margin-bottom: 1.5rem;">'
                        '<h4 style="margin: 0 0 0.5rem 0; font-size: 1.2rem;">📈 Tiingo Data (Premium)</h4>'
                        '<p style="margin: 0; opacity: 0.9; font-size: 0.9rem;">Source: Tiingo API | Professional Grade</p>'
                        '</div>',
                        unsafe_allow_html=True
                    )
                    # Display with color-coded background
                    st.markdown('<div style="background: rgba(240, 147, 251, 0.1); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #f093fb;">', unsafe_allow_html=True)
                    st.json(raw_data if raw_data else fundamentals)
                    st.markdown('</div>', unsafe_allow_html=True)
                        
                elif data_source_used == 'yfinance':
                    st.markdown(
                        '<div class="data-section yfinance-data" style="margin-bottom: 1.5rem;">'
                        '<h4 style="margin: 0 0 0.5rem 0; font-size: 1.2rem; color: #1a1a1a;">📉 Yahoo Finance Data (Free)</h4>'
                        '<p style="margin: 0; opacity: 0.8; font-size: 0.9rem; color: #1a1a1a;">Source: yfinance Library | Community Maintained</p>'
                        '</div>',
                        unsafe_allow_html=True
                    )
                    # Display with color-coded background
                    st.markdown('<div style="background: rgba(79, 172, 254, 0.1); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #4facfe;">', unsafe_allow_html=True)
                    st.json(raw_data if raw_data else fundamentals)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    # Fallback for unknown source
                    st.warning(f"⚠️ Unknown data source: {data_source_used}")
                    st.json(raw_data if raw_data else fundamentals)
            
        except Exception as e:
            st.error(f"Error fetching fundamentals: {e}")


def display_broker_connections_tab():
    """Display broker connections tab (requires KYC and investment agreement)"""
    
    if not RBAC_AVAILABLE:
        st.error("RBAC system not available")
        return
    
    # Check authentication and permissions
    if not RBACManager.is_authenticated():
        st.warning("⚠️ Please login to access broker connections")
        show_login_form()
        return
    
    # Check if user has required permissions and compliance
    if not RBACManager.require_connections_access():
        show_permission_denied("Broker Connections Access")
        
        st.markdown("### 📋 Requirements")
        st.markdown("""
        This tab is restricted to **Asset Management Clients** and **Investors** who have:
        
        1. ✅ **Completed KYC** (Know Your Customer) verification
        2. ✅ **Signed Investment Management Agreement**
        
        These requirements ensure compliance with financial regulations and protect both parties.
        """)
        
        user = RBACManager.get_current_user()
        if user:
            st.markdown("### 📊 Your Status")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if user.kyc_completed:
                    st.success("✅ KYC Completed")
                    if user.kyc_date:
                        st.caption(f"Completed on: {user.kyc_date.strftime('%Y-%m-%d')}")
                else:
                    st.error("❌ KYC Not Completed")
                    st.caption("Please contact support to complete KYC")
            
            with col2:
                if user.investment_agreement_signed:
                    st.success("✅ Investment Agreement Signed")
                    if user.agreement_date:
                        st.caption(f"Signed on: {user.agreement_date.strftime('%Y-%m-%d')}")
                else:
                    st.error("❌ Investment Agreement Not Signed")
                    st.caption("Please contact support to sign agreement")
        
        st.markdown("---")
        st.info("💡 **Contact Support:** For assistance with onboarding, email: support@bentleybot.com")
        
        return
    
    # User has access - display broker connections
    st.header("🔗 Broker Connections & Fund Management")
    st.markdown("Manage your connected broker accounts and monitor fund positions")
    
    # Create sub-tabs for different connection views
    conn_tab1, conn_tab2, conn_tab3, conn_tab4 = st.tabs([
        "🏦 Accounts",
        "💼 WeFolio Funds",
        "📊 Positions",
        "🔍 Health Monitor"
    ])
    
    with conn_tab1:
        display_broker_connections()
    
    with conn_tab2:
        display_webull_funds()
    
    with conn_tab3:
        display_position_analysis()
    
    with conn_tab4:
        display_connection_health()


if __name__ == "__main__":
    st.set_page_config(
        page_title="Investment Analysis - BentleyBot",
        page_icon="📈",
        layout="wide"
    )
    
    display_investment_page()
