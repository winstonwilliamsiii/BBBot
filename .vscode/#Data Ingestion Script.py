#Data Ingestion Script

# data_ingestion.py

import requests
import pandas as pd

def fetch_market_data(source='binance', symbol='BTCUSDT', interval='15m', limit=100):
    if source == 'binance':
        return fetch_binance_ohlcv(symbol, interval, limit)
    elif source == 'webull':
        return fetch_webull_ohlcv(symbol, interval, limit)
    elif source == 'ibkr':
        return fetch_ibkr_ohlcv(symbol, interval, limit)
    else:
        raise ValueError(f"Unsupported source: {source}")

def fetch_binance_ohlcv(symbol, interval, limit):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'num_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    df = df.astype({'open': float, 'high': float, 'low': float, 'close': float, 'volume': float})
    return df

def fetch_webull_ohlcv(symbol, interval, limit):
    print(f"[WeBull] Fetching OHLCV for {symbol} at {interval}")
    # TODO: Add Webull API logic
    return pd.DataFrame()

def fetch_ibkr_ohlcv(symbol, interval, limit):
    print(f"[IBKR] Fetching OHLCV for {symbol} at {interval}")
    # TODO: Add IBKR API logic
    return pd.DataFrame()