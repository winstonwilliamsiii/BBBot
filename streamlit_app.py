import streamlit as st
import pandas as pd
import math
from pathlib import Path

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Bentley Budget Bot',
    page_icon=':earth_americas:',  # This is an emoji shortcode. Could be a URL too.
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_gdp_data():
    """Grab GDP data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    DATA_FILENAME = Path(__file__).parent/'data/gdp_data.csv'
    raw_gdp_df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 2017
    MAX_YEAR = 2025

    # The data above has columns like:
    # - Country Name
    # - Country Code
    # - [Stuff I don't care about]
    # - GDP for 1960
    # - GDP for 1961
    # - GDP for 1962
    # - ...
    # - GDP for 2022
    #
    # ...but I want this instead:
    # - Country Name
    # - Country Code
    # - Year
    # - GDP
    #
    # So let's pivot all those year-columns into two: Year and GDP
    # Find which year columns actually exist in the data
    available_years = [
        str(y) for y in range(MIN_YEAR, MAX_YEAR + 1)
        if str(y) in raw_gdp_df.columns
    ]

    gdp_long_df = raw_gdp_df.melt(
        ['Country Code'],
        available_years,
        'Year',
        'GDP',
    )

    # Convert years from string to integers
    gdp_long_df['Year'] = pd.to_numeric(gdp_long_df['Year'])

    return gdp_long_df

gdp_data = get_gdp_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
title_md = """
# :earth_americas: Bentley Budget Bot

Ideal Dashboard tool for High Earners Not Yet Wealthy "HENRYs." As you'll
notice, the data only goes to 2025 and datapoints for certain years are often missing.
But it's otherwise a great (and did I mention _free_?) source of financial tool
"""
st.markdown(title_md, unsafe_allow_html=True)

# Add some spacing
st.write("")
st.write("")

min_value = gdp_data['Year'].min()
max_value = gdp_data['Year'].max()

from_year, to_year = st.slider(
    'Which years are you interested in?',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value])

countries = gdp_data['Country Code'].unique()

if not len(countries):
    st.warning("Select at least one country")

selected_countries = st.multiselect(
    'Which cost would you like to view?',
    countries,
    ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'])

st.write("")
st.write("")
st.write("")

# Filter the data
filtered_gdp_df = gdp_data[
    (gdp_data['Country Code'].isin(selected_countries))
    & (gdp_data['Year'] <= to_year)
    & (from_year <= gdp_data['Year'])
]

st.header('GDP over time', divider='gray')

st.write("")

st.markdown(
    "<span style='color:#F8F8FF; font-size:1.2em;'>GDP over time</span>",
    unsafe_allow_html=True
)

st.line_chart(
    filtered_gdp_df,
    x='Year',
    y='GDP',
)

st.write("")
st.write("")


first_year = gdp_data[gdp_data['Year'] == from_year]
last_year = gdp_data[gdp_data['Year'] == to_year]

st.header(f'GDP in {to_year}', divider='gray')

st.write("")

st.markdown(
    f"<span style='color:#F8F8FF; font-size:1.2em;'>GDP in {to_year}</span>",
    unsafe_allow_html=True
)

cols = st.columns(4)

for i, country in enumerate(selected_countries):
    col = cols[i % len(cols)]

    with col:
        # Extract GDP series for the country and convert to billions
        first_series = first_year.loc[
            first_year['Country Code'] == country, 'GDP'
        ]
        last_series = last_year.loc[
            last_year['Country Code'] == country, 'GDP'
        ]

        first_gdp = first_series.iat[0] / 1_000_000_000
        last_gdp = last_series.iat[0] / 1_000_000_000

        if math.isnan(first_gdp):
            growth = 'n/a'
            delta_color = 'off'
        else:
            growth = f'{last_gdp / first_gdp:,.2f}x'
            delta_color = 'normal'

        st.metric(
            label=f'{country} GDP',
            value=f'{last_gdp:,.0f}B',
            delta=growth,
            delta_color=delta_color
        )

st.set_page_config(
    page_title="Bentley Budget Bot",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
                /* Color scheme variables */
        :root {
          --lavender: #E6E6FA;
          --mint-mist: #AAF0D1;
          --soft-gold: #FAFAD2;
          --pearl-white: #FFFFFF;
          --graphite: #383838;
          
          /* Semantic color assignments */
          --primary-color: var(--lavender);
          --secondary-color: var(--mint-mist);
          --accent-color: var(--soft-gold);
          --background-color: var(--pearl-white);
          --text-color: var(--graphite);
          --text-light: var(--pearl-white);
        }
        
        /* Base styling */
        body {
          background-color: var(--background-color);
          color: var(--text-color);
          font-family: Arial, sans-serif;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
          color: var(--graphite);
        }
        
        /* Primary elements */
        .primary {
          background-color: var(--primary-color);
          color: var(--text-color);
        }
        
        /* Secondary elements */
        .secondary {
          background-color: var(--secondary-color);
          color: var(--text-color);
        }
        
        /* Accent elements */
        .accent {
          background-color: var(--accent-color);
          color: var(--text-color);
        }
        
        /* Buttons */
        .btn-primary {
          background-color: var(--lavender);
          border-color: var(--lavender);
          color: var(--text-color);
        }
        
        .btn-primary:hover {
          background-color: var(--mint-mist);
          border-color: var(--mint-mist);
        }
        
        .btn-secondary {
          background-color: var(--mint-mist);
          border-color: var(--mint-mist);
          color: var(--text-color);
        }
        
        .btn-secondary:hover {
          background-color: var(--soft-gold);
          border-color: var(--soft-gold);
        }
        
        /* Navigation */
        .navbar {
          background-color: var(--graphite);
          color: var(--pearl-white);
        }
        
        .navbar a {
          color: var(--pearl-white);
        }
        
        .navbar a:hover {
          color: var(--lavender);
        }
        
        /* Cards/Containers */
        .card {
          background-color: var(--pearl-white);
          border: 1px solid var(--lavender);
          color: var(--text-color);
        }
        
        .card-header {
          background-color: var(--lavender);
          color: var(--text-color);
        }
        
        /* Links */
        a {
          color: var(--graphite);
        }
        
        a:hover {
          color: var(--mint-mist);
        }
        
        /* Form elements */
        .form-control {
          border-color: var(--lavender);
        }
        
        .form-control:focus {
          border-color: var(--mint-mist);
          box-shadow: 0 0 0 0.2rem rgba(170, 240, 209, 0.25);
        }
        
        /* Alerts/Messages */
        .alert-success {
          background-color: var(--mint-mist);
          border-color: var(--mint-mist);
          color: var(--text-color);
        }
        
        .alert-warning {
          background-color: var(--soft-gold);
          border-color: var(--soft-gold);
          color: var(--text-color);
        }
        
        .alert-info {
          background-color: var(--lavender);
          border-color: var(--lavender);
          color: var(--text-color);
        }:root {
            --primary-color: #6A0DAD;
            --secondary-color: #228B22;
            --background-color: #2F4F4F;
            --accent-color: #E6FFED;
            --text-color: #E0E0E0;        /* Changed from #1C1C1C to light grey */
            --subtext-color: #AA82C5;
            --highlight-color: #FFD700;
            --border-color: #C0C0C0;
            --off-white: #F8F8FF;         /* Added off-white color */
        }

        .block-container {
            background-color: var(--background-color);
            color: var(--text-color);
        }

        h1, h2, h3 {
            color: var(--primary-color);
        }

        .stButton > button {
            background-color: var(--secondary-color);
            color: white;
        }

        .stDataFrame, .stTable {
            border-color: var(--border-color);
            color: var(--text-color); /* Ensure table text is light grey */
        }

        .metric {
            color: var(--off-white);
        }

        .stMetric > div > div {
            color: var(--off-white) !important;
        }

        .stMetric label {
            color: var(--off-white) !important;
        }

        .stMetric [data-testid="metric-value"] {
            color: var(--off-white) !important;
        }

        .stMetric [data-testid="metric-delta"] {
            color: var(--off-white) !important;
        }
    </style>
""", unsafe_allow_html=True)


