import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import date, timedelta

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Bentley Dashboard',
    page_icon=':chart_with_upwards_trend:',
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_yfinance_data(tickers, start_date, end_date):
    """Grab Yahoo Finance data.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """
    # yfinance returns a wide-format dataframe, so we'll process it.
    raw_df = yf.download(tickers, start=start_date, end=end_date)

    if raw_df.empty:
        return pd.DataFrame()

    # We only need the 'Close' price for this dashboard
    close_prices = raw_df['Close']

    # Melt the dataframe to have Ticker, Date, and Price
    long_df = close_prices.reset_index().melt(id_vars='Date', var_name='Ticker', value_name='Price')
    long_df['Date'] = pd.to_datetime(long_df['Date'])

    return long_df

# -----------------------------------------------------------------------------
# Draw the actual page

# Define the color scheme based on your request
COLOR_SCHEME = {
    "background": "#FFFFFF",
    "text": "#020617",
    "primary": "#0F172A",
    "primary_foreground": "#F8FAFC",
    "secondary": "#F1F5F9",
    "card_background": "#FFFFFF"
}

# Apply custom CSS for background and text colors
st.markdown(f"""
<style>
    .stApp {{
        background-color: {COLOR_SCHEME['background']};
        color: {COLOR_SCHEME['text']};
    }}
</style>
""", unsafe_allow_html=True)

# Set the title that appears at the top of the page.
st.markdown(f"""
    <h1 style='text-align: center; color: {COLOR_SCHEME['text']}; 
    margin-bottom: 1rem; font-size: 3rem;'>
    Bentley Dashboard
    </h1>
    """, unsafe_allow_html=True)

st.markdown("<p style='text-align: center;'>An ideal dashboard tool for viewing your financial portfolios.</p>", unsafe_allow_html=True)

# Add some spacing
st.write("")
st.write("")

# --- Sidebar for user inputs ---
st.sidebar.header("Portfolio Selection")

portfolio_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']

selected_tickers = st.sidebar.multiselect(
    'Which stocks would you like to view?',
    portfolio_tickers,
    ['AAPL', 'MSFT', 'GOOGL'])

today = date.today()
five_years_ago = today - timedelta(days=5*365)

from_date, to_date = st.sidebar.date_input(
    "Select date range:",
    value=[five_years_ago, today],
    min_value=date(2000, 1, 1),
    max_value=today
)

if not selected_tickers:
    st.warning("Please select at least one ticker from the sidebar.")
    st.stop()

if from_date > to_date:
    st.error("Error: Start date must be before end date.")
    st.stop()

portfolio_data = get_yfinance_data(selected_tickers, from_date, to_date)

# Filter the data
filtered_df = portfolio_data.copy()

# Calculate daily percentage change
filtered_df['Daily Change %'] = filtered_df.groupby('Ticker')['Price'].pct_change() * 100


st.header('Portfolio Performance Over Time', divider='blue')

st.line_chart(
    filtered_df,
    x='Date',
    y='Price',
    color='Ticker'
)

st.write("")
st.write("")

st.header(f'Metrics for {to_date.strftime("%Y-%m-%d")}', divider='blue')

cols = st.columns(4)

for i, ticker in enumerate(selected_tickers):
    col = cols[i % len(cols)]

    with col:
        ticker_data = filtered_df[filtered_df['Ticker'] == ticker]
        if not ticker_data.empty:
            first_price = ticker_data['Price'].iloc[0]
            last_price = ticker_data['Price'].iloc[-1]

            if pd.notna(first_price) and first_price > 0:
                growth_pct = ((last_price - first_price) / first_price) * 100
                delta = f'{growth_pct:.2f}%'
            else:
                delta = 'n/a'

            st.metric(
                label=f'{ticker} Price',
                value=f'${last_price:,.2f}',
                delta=delta,
            )
        else:
            st.metric(label=f'{ticker} Price', value='N/A', delta='N/A')

st.write("")
st.write("")

st.header("Raw Portfolio Data", divider='blue')
st.dataframe(filtered_df, use_container_width=True)
