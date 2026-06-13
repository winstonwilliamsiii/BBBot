#Screener CSV Ingestion Script

import csv
from pathlib import Path

def load_screener_csv(csv_path: str):
    """
    Load TradingView screener CSV and return tickers.
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    tickers = []
    with csv_file.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row.get("Ticker") or row.get("Symbol")
            if ticker:
                tickers.append(ticker.strip())

    return list(sorted(set(tickers)))

if __name__ == "__main__":
    titan_tickers = load_screener_csv("titan_tech_fundamentals.csv")
    vega_tickers = load_screener_csv("vega_fundamentals.csv")

    print("Titan tickers:", titan_tickers)
    print("Vega tickers:", vega_tickers)
