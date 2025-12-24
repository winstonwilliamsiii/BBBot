#Tingo Crypto and News Data_Fetch

import os
from tiingo import TiingoClient

# Configure the client - Use environment variable for security
config = {'api_key': os.getenv('TIINGO_API_KEY', '')}

if not config['api_key']:
    raise ValueError(
        "TIINGO_API_KEY environment variable not set. "
        "Please add it to your .env file"
    )

client = TiingoClient(config)
# Fetch metadata for a stock ticker
metadata = client.get_ticker_metadata('AAPL')
print(metadata)
