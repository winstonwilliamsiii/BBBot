#hydra_bot

# hydra_bot.py
import alpaca_trade_api as alpaca
import ib_insync as ibkr
import pandas as pd
import numpy as np
import requests
from textblob import TextBlob
import yfinance as yf

class HydraBot:
    def __init__(self, alpaca_keys, ibkr_keys):
        # Broker connections
        self.alpaca = alpaca.REST(alpaca_keys['key_id'], alpaca_keys['secret'], alpaca_keys['base_url'])
        self.ib = ibkr.IB()
        self.ib.connect(ibkr_keys['host'], ibkr_keys['port'], clientId=ibkr_keys['client_id'])

    # --- Momentum Strategy ---
    def momentum_signal(self, ticker, lookback=20):
        data = yf.download(ticker, period="6mo", interval="1d")
        data['returns'] = data['Close'].pct_change()
        data['momentum'] = data['returns'].rolling(lookback).mean()
        return data['momentum'].iloc[-1] > 0  # Buy if momentum positive

    # --- Fundamental Analysis ---
    def fundamental_score(self, ticker):
        info = yf.Ticker(ticker).info
        pe_ratio = info.get('forwardPE', None)
        roe = info.get('returnOnEquity', None)
        return (roe or 0) - (pe_ratio or 0)  # crude scoring

    # --- Technical Analysis ---
    def technical_signal(self, ticker):
        data = yf.download(ticker, period="3mo", interval="1d")
        data['SMA50'] = data['Close'].rolling(50).mean()
        data['SMA200'] = data['Close'].rolling(200).mean()
        return data['SMA50'].iloc[-1] > data['SMA200'].iloc[-1]  # Golden Cross

    # --- Sentiment Analysis ---
    def sentiment_score(self, news_headlines):
        scores = [TextBlob(h).sentiment.polarity for h in news_headlines]
        return np.mean(scores)

    # --- Decision Engine ---
    def trade_decision(self, ticker, headlines):
        momentum = self.momentum_signal(ticker)
        fundamental = self.fundamental_score(ticker)
        technical = self.technical_signal(ticker)
        sentiment = self.sentiment_score(headlines)

        score = (momentum * 1) + (fundamental * 0.5) + (technical * 1) + (sentiment * 0.5)
        return "BUY" if score > 0 else "SELL"

    # --- Execution ---
    def execute_trade(self, broker, ticker, action, qty=10):
        if broker == "alpaca":
            if action == "BUY":
                self.alpaca.submit_order(symbol=ticker, qty=qty, side='buy', type='market', time_in_force='gtc')
            else:
                self.alpaca.submit_order(symbol=ticker, qty=qty, side='sell', type='market', time_in_force='gtc')
        elif broker == "ibkr":
            contract = ibkr.Stock(ticker, 'SMART', 'USD')
            order = ibkr.MarketOrder(action.lower(), qty)
            self.ib.placeOrder(contract, order)