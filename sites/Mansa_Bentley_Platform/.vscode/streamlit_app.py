import streamlit as st
import pandas as pd
import math
from pathlib import Path
import yfinance as yf  # For Yahoo Finance data
import requests
from datetime import datetime, timedelta

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Bentley Budget Bot Dashboard',
    page_icon=':earth_americas:', # This is an emoji shortcode. Could be a URL too.
    layout="wide"
)

# Custom CSS for dashboard colors
st.markdown("""
<style>
    /* Main background */
    .main > div {
        background-color: #F5F5F5;
    }
    
    /* Header styling */
    .main h1 {
        color: #103766;
        border-bottom: 3px solid #288cfa;
        padding-bottom: 10px;
    }
    
    /* Subheader */
    .main h2, .main h3 {
        color: #103766;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #288cfa;
    }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #288cfa;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(40, 140, 250, 0.1);
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #288cfa;
        color: white;
        border: none;
        border-radius: 5px;
    }
    
    .stButton > button:hover {
        background-color: #103766;
    }
    
    /* Selectbox and multiselect */
    .stSelectbox > div > div {
        border-color: #288cfa;
    }
    
    .stMultiSelect > div > div {
        border-color: #288cfa;
    }
    
    /* Slider */
    .stSlider > div > div > div > div {
        background-color: #288cfa;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_gdp_data():
    """Grab Cost data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    DATA_FILENAME = Path(__file__).parent/'data/gdp_data.csv'
    raw_gdp_df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 2012
    MAX_YEAR = 2025

    # The data above has columns like:
    # - Country Name
    # - Country Code
    # - [Stuff I don't care about]
    # - Cost for 2012
    # - Cost for 2013
    # - Cost for 2014
    # - ...
    # - Cost for 2025
    #
    # ...but I want this instead:
    # - Country Name
    # - Country Code
    # - Year
    # - Cost
    #
    # So let's pivot all those year-columns into two: Year and Cost
    gdp_df = raw_gdp_df.melt(
        ['Country Code'],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        'Year',
        'GDP',
    )

    # Convert years from string to integers
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])

    return gdp_df

@st.cache_data(ttl='1h')  # Cache for 1 hour
def get_yahoo_portfolio_data(symbols):
    """Fetch real-time portfolio data from Yahoo Finance."""
    try:
        portfolio_data = []
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                portfolio_data.append({
                    'Symbol': symbol,
                    'Company': info.get('longName', symbol),
                    'Current Price': current_price,
                    'Market Cap': info.get('marketCap', 'N/A'),
                    'PE Ratio': info.get('trailingPE', 'N/A'),
                    'Sector': info.get('sector', 'N/A')
                })
        
        return pd.DataFrame(portfolio_data)
    except Exception as e:
        st.error(f"Error fetching Yahoo Finance data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl='1h')
def get_stock_chart_data(symbol, period="1y"):
    """Get historical stock data for charting."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        hist.reset_index(inplace=True)
        return hist
    except Exception as e:
        st.error(f"Error fetching chart data for {symbol}: {str(e)}")
        return pd.DataFrame()

gdp_df = get_gdp_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page with custom styling.
st.markdown("""
<div style="text-align: center; padding: 2rem 0;">
    <h1 style="color: #103766; font-size: 3rem; margin-bottom: 0;">
        🌍 Bentley Budget Bot Dashboard
    </h1>
    <div style="width: 100px; height: 4px; background: linear-gradient(90deg, #288cfa, #103766); margin: 1rem auto;"></div>
    <p style="color: #103766; font-size: 1.2rem; margin-top: 1rem;">
        Browse Cost data from the <a href="https://data.worldbank.org/" style="color: #288cfa;">World Bank Open Data</a> website. 
        As you'll notice, the data only goes to 2022 right now, and datapoints for certain years are often missing.
        But it's otherwise a great (and did I mention <em>free</em>?) source of data.
    </p>
</div>
""", unsafe_allow_html=True)

# Add some spacing
st.markdown("<br>", unsafe_allow_html=True)

# Create a colored container for controls
with st.container():
    st.markdown("""
    <div style="background-color: white; padding: 2rem; border-radius: 10px; 
                border: 2px solid #288cfa; margin: 1rem 0;">
        <h3 style="color: #103766; margin-top: 0;">📊 Data Controls</h3>
    """, unsafe_allow_html=True)
    
    min_value = gdp_df['Year'].min()
    max_value = gdp_df['Year'].max()

    from_year, to_year = st.slider(
        'Which years are you interested in?',
        min_value=min_value,
        max_value=max_value,
        value=[min_value, max_value])

    countries = gdp_df['Country Code'].unique()

    if not len(countries):
        st.warning("Select at least one country")

    selected_countries = st.multiselect(
        'Which countries would you like to view?',
        countries,
        ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'])
    
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Filter the data
filtered_gdp_df = gdp_df[
    (gdp_df['Country Code'].isin(selected_countries))
    & (gdp_df['Year'] <= to_year)
    & (from_year <= gdp_df['Year'])
]

# Chart section with custom styling
st.markdown("""
<div style="background-color: white; padding: 2rem; border-radius: 10px; 
            border: 2px solid #103766; margin: 1rem 0;">
    <h2 style="color: #103766; margin-top: 0;">📈 Cost over time</h2>
""", unsafe_allow_html=True)

st.line_chart(
    filtered_gdp_df,
    x='Year',
    y='GDP',
    color='Country Code',
)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

first_year = gdp_df[gdp_df['Year'] == from_year]
last_year = gdp_df[gdp_df['Year'] == to_year]

# Metrics section with custom styling
st.markdown(f"""
<div style="background-color: white; padding: 2rem; border-radius: 10px; 
            border: 2px solid #288cfa; margin: 1rem 0;">
    <h2 style="color: #103766; margin-top: 0;">💰 Cost in {to_year}</h2>
""", unsafe_allow_html=True)

cols = st.columns(4)

for i, country in enumerate(selected_countries):
    col = cols[i % len(cols)]

    with col:
        first_gdp = first_year[first_year['Country Code'] == country]['GDP'].iat[0] / 1000000000
        last_gdp = last_year[last_year['Country Code'] == country]['GDP'].iat[0] / 1000000000

        if math.isnan(first_gdp):
            growth = 'n/a'
            delta_color = 'off'
        else:
            growth = f'{last_gdp / first_gdp:,.2f}x'
            delta_color = 'normal'

        # Custom styled metric card
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #F5F5F5, white); 
                    border: 2px solid #288cfa; border-radius: 10px; 
                    padding: 1rem; margin: 0.5rem 0; text-align: center;">
            <h4 style="color: #103766; margin: 0;">{country} Cost</h4>
            <h2 style="color: #288cfa; margin: 0.5rem 0;">{last_gdp:,.0f}B</h2>
            <p style="color: #103766; margin: 0;">Growth: {growth}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Add Yahoo Portfolio Section
st.markdown("<br><br>", unsafe_allow_html=True)

# Yahoo Portfolio Section
st.markdown("""
<div style="background-color: white; padding: 2rem; border-radius: 10px; 
            border: 2px solid #288cfa; margin: 1rem 0;">
    <h2 style="color: #103766; margin-top: 0;">📈 Yahoo Finance Portfolio</h2>
""", unsafe_allow_html=True)

# Portfolio input
st.markdown("**Enter stock symbols (comma-separated):**")
default_stocks = "AAPL,GOOGL,MSFT,TSLA,AMZN"
stock_input = st.text_input("Stock Symbols", value=default_stocks, 
                           help="Enter stock symbols separated by commas (e.g., AAPL,GOOGL,MSFT)")

if stock_input:
    symbols = [symbol.strip().upper() for symbol in stock_input.split(',')]
    
    # Fetch portfolio data
    with st.spinner('Fetching Yahoo Finance data...'):
        portfolio_df = get_yahoo_portfolio_data(symbols)
    
    if not portfolio_df.empty:
        # Display portfolio table
        st.markdown("### 💼 Portfolio Overview")
        st.dataframe(portfolio_df, use_container_width=True)
        
        # Portfolio metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_stocks = len(portfolio_df)
            st.metric("Total Stocks", total_stocks)
        
        with col2:
            avg_pe = portfolio_df['PE Ratio'].replace('N/A', None).dropna().astype(float).mean()
            st.metric("Avg P/E Ratio", f"{avg_pe:.2f}" if not pd.isna(avg_pe) else "N/A")
        
        with col3:
            sectors = portfolio_df['Sector'].value_counts()
            top_sector = sectors.index[0] if not sectors.empty else "N/A"
            st.metric("Top Sector", top_sector)
        
        with col4:
            total_value = portfolio_df['Current Price'].sum()
            st.metric("Portfolio Value", f"${total_value:,.2f}")
        
        # Stock chart section
        st.markdown("### 📊 Stock Price Charts")
        selected_stock = st.selectbox("Select a stock to view chart:", symbols)
        
        if selected_stock:
            chart_data = get_stock_chart_data(selected_stock)
            if not chart_data.empty:
                st.line_chart(chart_data.set_index('Date')['Close'])
            else:
                st.warning(f"No chart data available for {selected_stock}")
    else:
        st.warning("Unable to fetch portfolio data. Please check your internet connection and stock symbols.")

st.markdown("</div>", unsafe_allow_html=True)
        
