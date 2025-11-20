#Tingo Crypto and News Data_Fetch

from tiingo import TiingoClient
# Configure the client
config = {'api_key': 'YOUR_API_KEY'}
client = TiingoClient(config)
# Fetch metadata for a stock ticker
metadata = client.get_ticker_metadata('AAPL')
print(metadata)