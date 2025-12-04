"""
Investment Analysis Page with MLFlow Integration
Displays portfolio analysis with logged experiments and metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

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
    
    st.title("📈 Investment Analysis Dashboard")
    st.markdown("Real-time portfolio tracking with ML experiment logging")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Analysis Configuration")
    
    # Load tickers from config
    if MLFLOW_AVAILABLE:
        try:
            config = load_tickers_config()
            available_tickers = config['tickers']['all']
        except:
            available_tickers = ['IONQ', 'QBTS', 'SOUN', 'RGTI', 'AMZN', 'MSFT', 'GOOGL']
    else:
        available_tickers = ['IONQ', 'QBTS', 'SOUN', 'RGTI', 'AMZN', 'MSFT', 'GOOGL']
    
    # Ticker selection
    selected_tickers = st.sidebar.multiselect(
        "Select Tickers to Analyze",
        available_tickers,
        default=['IONQ', 'QBTS', 'SOUN', 'RGTI']
    )
    
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
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Portfolio Overview",
        "🔬 MLFlow Experiments",
        "📈 Technical Analysis",
        "💰 Fundamental Ratios"
    ])
    
    # Tab 1: Portfolio Overview
    with tab1:
        display_portfolio_overview(selected_tickers, start_date, end_date, enable_logging)
    
    # Tab 2: MLFlow Experiments
    with tab2:
        display_mlflow_experiments(selected_tickers)
    
    # Tab 3: Technical Analysis
    with tab3:
        display_technical_analysis(selected_tickers, start_date, end_date)
    
    # Tab 4: Fundamental Ratios
    with tab4:
        display_fundamental_ratios(selected_tickers, enable_logging)


def display_portfolio_overview(tickers, start_date, end_date, enable_logging):
    """Display portfolio performance overview"""
    
    st.header("📊 Portfolio Performance")
    
    if not YFINANCE_AVAILABLE:
        st.error("yfinance package required for portfolio data")
        return
    
    # Fetch data with timing
    start_time = time.time()
    
    with st.spinner("Fetching portfolio data..."):
        data_frames = []
        
        for ticker in tickers:
            try:
                df = yf.download(ticker, start=start_date, end=end_date, progress=False)
                if not df.empty:
                    df['Ticker'] = ticker
                    df['Date'] = df.index
                    data_frames.append(df[['Date', 'Ticker', 'Close', 'Volume']])
            except Exception as e:
                st.warning(f"⚠️ Could not fetch {ticker}: {e}")
        
        if not data_frames:
            st.error("No data available for selected tickers")
            return
        
        portfolio_df = pd.concat(data_frames, ignore_index=True)
    
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
    st.subheader("Price Performance")
    
    fig = px.line(
        portfolio_df,
        x='Date',
        y='Close',
        color='Ticker',
        title='Portfolio Price History',
        labels={'Close': 'Price ($)', 'Date': 'Date'}
    )
    
    fig.update_layout(
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
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
                        
                        fig = px.line(
                            ratio_df,
                            x='Date',
                            y=selected_metric,
                            title=f'{selected_metric} Trend for {selected_ticker}',
                            markers=True
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No ratio analysis runs found for {selected_ticker}")
        
    except Exception as e:
        st.error(f"Error loading MLFlow experiments: {e}")
        st.exception(e)


def display_technical_analysis(tickers, start_date, end_date):
    """Display technical analysis charts"""
    
    st.header("📈 Technical Analysis")
    
    if not YFINANCE_AVAILABLE:
        st.error("yfinance package required")
        return
    
    selected_ticker = st.selectbox("Select ticker for technical analysis", tickers, key="tech_ticker")
    
    with st.spinner(f"Analyzing {selected_ticker}..."):
        try:
            df = yf.download(selected_ticker, start=start_date, end=end_date, progress=False)
            
            if df.empty:
                st.warning(f"No data available for {selected_ticker}")
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
                title=f'{selected_ticker} Price with Moving Averages',
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
                title=f'{selected_ticker} Trading Volume',
                yaxis_title='Volume',
                xaxis_title='Date',
                height=300
            )
            
            st.plotly_chart(fig_volume, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error in technical analysis: {e}")


def display_fundamental_ratios(tickers, enable_logging):
    """Display and log fundamental ratios"""
    
    st.header("💰 Fundamental Analysis")
    
    if not YFINANCE_AVAILABLE:
        st.error("yfinance package required")
        return
    
    selected_ticker = st.selectbox("Select ticker for fundamentals", tickers, key="fund_ticker")
    
    with st.spinner(f"Fetching fundamentals for {selected_ticker}..."):
        try:
            ticker = yf.Ticker(selected_ticker)
            info = ticker.info
            
            # Extract key fundamentals
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
            
            # Display in columns
            col1, col2, col3 = st.columns(3)
            
            keys = list(fundamentals.keys())
            for i, key in enumerate(keys):
                col = [col1, col2, col3][i % 3]
                value = fundamentals[key]
                
                # Format value
                if isinstance(value, (int, float)):
                    if key == 'Market Cap' or key == 'Revenue':
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
            
            # Display full info in expander
            with st.expander("📋 View All Available Data"):
                st.json(info)
            
        except Exception as e:
            st.error(f"Error fetching fundamentals: {e}")


if __name__ == "__main__":
    st.set_page_config(
        page_title="Investment Analysis - BentleyBot",
        page_icon="📈",
        layout="wide"
    )
    
    display_investment_page()
