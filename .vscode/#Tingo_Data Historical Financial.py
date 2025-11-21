#Tingo_Data Historical Financial Data Fetcher

import pandas_datareader as pdr
# Set your Tiingo API key
import os
api_key = os.environ.get('TIINGO_API_KEY')
# Fetch historical data for Apple Inc.