import requests
from bs4 import BeautifulSoup
import mlflow
import json

# -------------------------------
# MLFlow Setup
# -------------------------------
mlflow.set_tracking_uri("mysql+pymysql://user:password@host:3306/mlflow_db")
mlflow.set_experiment("stocktwits_sentiment_ingestion")

# -------------------------------
# Scraper Function
# -------------------------------
def scrape_stocktwits_sentiment(ticker: str):
    """
    Scrape Stocktwits sentiment 1-day score for a given ticker.
    """
    url = f"https://stocktwits.com/symbol/{ticker}/sentiment"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Locate sentiment score element (HTML structure may change over time)
    score_element = soup.find("span", {"class": "sentiment-score"})
    if not score_element:
        raise ValueError("Sentiment score not found on page")

    score = float(score_element.text.strip())
    return {"ticker": ticker, "sentiment_score_1d": score}

# -------------------------------
# MLFlow Logging
# -------------------------------
def log_sentiment_to_mlflow(ticker: str, data: dict):
    """
    Log sentiment score into MLFlow.
    """
    with mlflow.start_run(run_name=f"Stocktwits_{ticker}_Sentiment"):
        mlflow.log_param("source", "Stocktwits")
        mlflow.log_param("ticker", ticker)
        mlflow.log_metric("sentiment_score_1d", data["sentiment_score_1d"])

        # Save raw data artifact
        with open("sentiment_data.json", "w") as f:
            json.dump(data, f)
        mlflow.log_artifact("sentiment_data.json")

# -------------------------------
# Example Run
# -------------------------------
if __name__ == "__main__":
    ticker = "AMZN"
    data = scrape_stocktwits_sentiment(ticker)
    log_sentiment_to_mlflow(ticker, data)
    print(f"Logged sentiment for {ticker}: {data}")