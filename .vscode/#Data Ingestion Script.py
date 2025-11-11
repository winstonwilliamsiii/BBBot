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
    return pd.DataFrame(bdcsdf)
                     
 def fetch_webull_ohlcv(symbol, interval='15m', limit=100):
    print(f"[WeBull] Fetching OHLCV for {symbol} at {interval}")
    
    # Placeholder: Webull does not offer a public OHLCV API
    # You can use webull-python (community SDK) or scrape from their web app
    # Example: pip install webull
    try:
        from webull import webull
        wb = webull()
        wb.login('your_email', 'Cartagena57!@')  # Use 2FA if needed
        candles = wb.get_bars(stock=symbol, interval=interval, count=limit)
        df = pd.DataFrame(candles)
        df.rename(columns={'close': 'closePrice'}, inplace=True)
        df['timestamp'] = pd.to_datetime(df['time'])
        df = df[['timestamp', 'open', 'high', 'low', 'closePrice', 'volume']]
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        return df.astype(float)
    except Exception as e:
        print(f"Webull error: {e}")
        return pd.DataFrame()
    
    def fetch_ibkr_ohlcv(symbol, interval='15 mins', limit=100):
    print(f"[IBKR] Fetching OHLCV for {symbol} at {interval}")
    # Requires IB API + TWS or Gateway running
    # Example: pip install ib_insync
    try:
        from ib_insync import IB, Stock
        ib = IB()
        ib.connect('127.0.0.1', 7497, clientId=1)  # TWS default port
        contract = Stock(symbol, 'SMART', 'USD')
        bars = ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr='1 D',
            barSizeSetting=interval,
            whatToShow='TRADES',
            useRTH=True
        )
        df = util.df(bars)
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        df.rename(columns={'date': 'timestamp'}, inplace=True)
        return df
    except Exception as e:
        print(f"IBKR error: {e}")
        return pd.DataFrame()