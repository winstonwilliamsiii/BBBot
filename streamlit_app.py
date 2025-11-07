import streamlit as st
import pandas as pd
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

    # Apply custom styling (CSS)
    apply_custom_styling()

    # Main title with custom styling
    st.markdown(f"""
    <h1 style='text-align: center; color: {COLOR_SCHEME['text']}; 
    margin-bottom: 2rem; font-size: 3rem;'>
    🤖 Bentley Bot Dashboard
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("<p style='text-align: center;'>An ideal dashboard tool for viewing your financial portfolios.</p>", unsafe_allow_html=True)

    # Sidebar controls
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
    # default selection: if we loaded fetched tickers, select them; otherwise pick a few defaults
    default_selection = portfolio_tickers if (portfolio_tickers and portfolio_tickers != default_portfolio_tickers) else ['AAPL', 'MSFT', 'GOOGL']

    selected_tickers = st.sidebar.multiselect(
        'Which stocks would you like to view?',
        portfolio_tickers,
        default_selection
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

    # Bot status card
    create_custom_card(
        "Bot Status",
        "All systems operational. Bot is responding normally to user queries.",
    )

    # Fetch portfolio data
    portfolio_data = get_yfinance_data(selected_tickers, from_date, to_date)
    if portfolio_data.empty:
        st.warning("No data returned for the selected tickers / date range.")
    else:
        df = portfolio_data.copy()
        df['Daily Change %'] = df.groupby('Ticker')['Price'].pct_change() * 100

        st.header('Portfolio Performance Over Time')
        st.line_chart(df, x='Date', y='Price', color='Ticker')

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
                    create_metric_card(f'{ticker} Price', f'${last_price:,.2f}', delta)
                else:
                    create_metric_card(f'{ticker} Price', 'N/A', 'N/A')

        st.write("")
        st.header("Raw Portfolio Data")
        st.dataframe(df, use_container_width=True)

    # Footer
    add_footer()


if __name__ == "__main__":
    main()
