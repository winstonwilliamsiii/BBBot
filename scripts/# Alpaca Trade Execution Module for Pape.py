# Alpaca Trade Execution Module for Paper trading
import os
from alpaca_trade_api import REST, TimeFrame

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

alpaca = REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)

def get_last_price(symbol: str) -> float:
    barset = alpaca.get_bars(symbol, TimeFrame.Minute, limit=1)
    if not barset:
        raise ValueError(f"No market data for {symbol}")
    return float(barset[0].c)

def place_paper_trade(symbol: str, dollar_amount: float, side: str = "buy"):
    """
    Market order sized by dollar amount.
    """
    last_price = get_last_price(symbol)
    qty = round(dollar_amount / last_price, 3)
    if qty <= 0:
        raise ValueError(f"Quantity <= 0 for {symbol}")

    order = alpaca.submit_order(
        symbol=symbol,
        qty=qty,
        side=side,
        type="market",
        time_in_force="day"
    )
    return order

if __name__ == "__main__":
    titan_tickers = ["AAPL", "MSFT", "NVDA"]
    for t in titan_tickers:
        try:
            order = place_paper_trade(t, dollar_amount=5000, side="buy")
            print(f"Placed Titan order: {order}")
        except Exception as e:
            print(f"Error placing order for {t}: {e}")
