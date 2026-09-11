"""One-off connectivity test for Alpaca, yfinance, and AlphaVantage data sources.

Run with: .venv\\Scripts\\python.exe scripts\\test_data_apis.py
Does not modify any files; only prints pass/fail + a sample data point per source.
"""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

SYMBOL = "AAPL"


def test_alpaca() -> None:
    print("\n=== Alpaca ===")
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    base_url = os.getenv("ALPACA_BASE_URL")
    if not api_key or not secret_key:
        print("FAIL: ALPACA_API_KEY/ALPACA_SECRET_KEY missing")
        return
    try:
        import alpaca_trade_api as tradeapi

        api = tradeapi.REST(api_key, secret_key, base_url=base_url or "https://paper-api.alpaca.markets")
        account = api.get_account()
        print(f"OK: account status={account.status}, buying_power={account.buying_power}")
        from datetime import datetime, timedelta, timezone

        end = datetime.now(timezone.utc) - timedelta(minutes=20)
        start = end - timedelta(days=30)
        for feed in ("iex", "sip", None):
            try:
                kwargs = {"feed": feed} if feed else {}
                bars = api.get_bars(
                    SYMBOL,
                    "1Day",
                    start=start.strftime("%Y-%m-%d"),
                    end=end.strftime("%Y-%m-%d"),
                    limit=5,
                    **kwargs,
                )
                bars_list = list(bars)
            except Exception as feed_exc:  # noqa: BLE001
                print(f"  feed={feed!r} raised {feed_exc!r}")
                continue
            if bars_list:
                b = bars_list[-1]
                print(f"OK: feed={feed!r} {SYMBOL} last bar close={b.c} volume={b.v} ts={b.t}")
                break
            print(f"  feed={feed!r} returned no bars")
        else:
            print("WARN: no bars returned from any feed")
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc!r}")


def test_yfinance() -> None:
    print("\n=== yfinance ===")
    try:
        import yfinance as yf

        df = yf.download(SYMBOL, period="10d", interval="1d", progress=False, auto_adjust=False)
        if df is None or df.empty:
            print("FAIL: empty dataframe returned")
            return
        last_close = df["Close"].dropna().iloc[-1]
        if hasattr(last_close, "item"):
            last_close = last_close.item()
        print(f"OK: {SYMBOL} last close={last_close}")
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc!r}")


def test_alphavantage() -> None:
    print("\n=== AlphaVantage ===")
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("FAIL: ALPHA_VANTAGE_API_KEY missing")
        return
    try:
        import requests

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": SYMBOL,
            "apikey": api_key,
            "outputsize": "compact",
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if "Note" in data:
            print(f"WARN (rate limited): {data['Note'][:200]}")
            return
        if "Information" in data:
            print(f"WARN: {data['Information'][:200]}")
            return
        series = data.get("Time Series (Daily)")
        if not series:
            print(f"FAIL: unexpected response keys={list(data.keys())}")
            return
        latest_date = sorted(series.keys())[-1]
        latest = series[latest_date]
        print(f"OK: {SYMBOL} {latest_date} close={latest.get('4. close')} volume={latest.get('5. volume')}")
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc!r}")


if __name__ == "__main__":
    print(f"Python: {sys.version}")
    test_alpaca()
    test_yfinance()
    test_alphavantage()
