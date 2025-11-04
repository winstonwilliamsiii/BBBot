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
    🤖 BBBot Dashboard
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("<p style='text-align: center;'>An ideal dashboard tool for viewing your financial portfolios.</p>", unsafe_allow_html=True)

    # Sidebar controls
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
    portfolio_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']

    selected_tickers = st.sidebar.multiselect(
        'Which stocks would you like to view?',
        portfolio_tickers,
        ['AAPL', 'MSFT', 'GOOGL']
    )

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

    # Example top-level metric cards (demo)
    col1, col2, col3 = st.columns(3)

    with col1:
        create_metric_card("Active Users", "1,234", "+12%")

    with col2:
        create_metric_card("Messages Today", "5,678", "+8%")

    with col3:
        create_metric_card("Response Time", "0.8s", "-15%")

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
