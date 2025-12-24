#MLFlow logging of experiments, metrics, parameters, and artifacts
mlflow>=2.4.1
import mlflow

# Configure MLFlow tracking
mlflow.set_tracking_uri("mysql+pymysql://user:password@localhost:3306/mlflow_db")
mlflow.set_experiment("fundamentals_ratio_analysis")

import json

def log_fundamental_ratios(ticker: str, report_date: str, ratios: dict, source: str = "AlphaVantage+YFinance"):
    """
    Log fundamental ratio analysis into MLFlow.
    """
    run_name = f"{ticker}_{report_date}_ratios"
    with mlflow.start_run(run_name=run_name):
        # Parameters
        mlflow.log_param("ticker", ticker)
        mlflow.log_param("report_date", report_date)
        mlflow.log_param("source", source)

        # Metrics (ratios)
        for key, value in ratios.items():
            if value is not None:
                mlflow.log_metric(key, float(value))

        # Save raw ratios as artifact
        with open("ratios.json", "w") as f:
            json.dump(ratios, f)
        mlflow.log_artifact("ratios.json")
        
        import streamlit as st
from mlflow.tracking import MlflowClient

client = MlflowClient()
runs = client.search_runs(experiment_ids=["fundamentals_ratio_analysis"], order_by=["metrics.pe_ratio DESC"])

st.title("MLFlow Logged Ratios")
for run in runs[:10]:
    st.write(run.data.params["ticker"], run.data.metrics)