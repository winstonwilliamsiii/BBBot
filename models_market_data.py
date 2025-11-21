import requests
import json
import mlflow

# -------------------------------
# MLFlow Setup
# -------------------------------
mlflow.set_tracking_uri("mysql+pymysql://user:password@host:3306/mlflow_db")
mlflow.set_experiment("stock_data_ingestion")

# -------------------------------
# API Fetchers
# -------------------------------

def fetch_barchart_data(ticker: str, api_key: str):
    """
    Fetch quote data from Barchart API.
    """
    url = "https://marketdata.websol.barchart.com/getQuote.json"
    params = {"symbols": ticker, "apikey": api_key}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()["results"][0]


def fetch_polygon_data(ticker: str, date: str, api_key: str):
    """
    Fetch open/close data from Polygon.io (Massive).
    """
    url = f"https://api.polygon.io/v1/open-close/{ticker}/{date}"
    params = {"apiKey": api_key}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


def fetch_tiingo_data(ticker: str, start_date: str, end_date: str, token: str):
    """
    Fetch historical data from Tiingo API.
    """
    url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices"
    params = {"startDate": start_date, "endDate": end_date, "token": token}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()[0]  # first record


def fetch_stocktwits_data(ticker: str):
    """
    Fetch sentiment stream from Stocktwits API.
    """
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    # Extract sentiment counts
    messages = data.get("messages", [])
    bullish = sum(1 for m in messages if m.get("entities", {}).get("sentiment", {}).get("basic") == "Bullish")
    bearish = sum(1 for m in messages if m.get("entities", {}).get("sentiment", {}).get("basic") == "Bearish")
    return {"bullish": bullish, "bearish": bearish, "total": len(messages)}

# -------------------------------
# MLFlow Logging
# -------------------------------

def log_to_mlflow(source: str, ticker: str, data: dict):
    """
    Log API response metrics into MLFlow.
    """
    with mlflow.start_run(run_name=f"{source}_{ticker}"):
        mlflow.log_param("source", source)
        mlflow.log_param("ticker", ticker)

        # Log key metrics if available
        if "close" in data:
            mlflow.log_metric("close", data["close"])
        if "volume" in data:
            mlflow.log_metric("volume", data.get("volume", 0))
        if "bullish" in data:
            mlflow.log_metric("bullish_msgs", data["bullish"])
            mlflow.log_metric("bearish_msgs", data["bearish"])

        # Save raw data as artifact
        with open("raw_data.json", "w") as f:
            json.dump(data, f)
        mlflow.log_artifact("raw_data.json")