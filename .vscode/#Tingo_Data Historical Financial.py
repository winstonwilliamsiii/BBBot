#Tingo_Data Historical Financial Data Fetcher

import pandas_datareader as pdr
import os
# Set your Tiingo API key
api_key = os.environ.get('TIINGO_API_KEY')
# Fetch historical data for Apple Inc. (AAPL)
df = pdr.get_data_tiingo('AAPL', api_key=api_key)
# Display the last few rows of the data
print(df.tail())