#Streamlit MLFlow_Regression Performance
docker-compose -f docker/docker-compose.yml up -d

docker-compose -f docker/docker-compose.yml down

docker-compose -f docker/docker-compose.yml logs -f

docker-compose -f docker/docker-compose.yml down -v

docker-compose -f docker/docker-compose.yml up --build -d
import streamlit as st
from mlflow.tracking import MlflowClient

client = MlflowClient()

st.title("ROI Prediction Models")

runs = client.search_runs(experiment_ids=["fundamentals_ratio_analysis"], order_by=["metrics.r2_score DESC"])
for run in runs[:10]:
    st.write("Ticker:", run.data.params.get("ticker"))
    st.write("R²:", run.data.metrics.get("r2_score"))
    st.write("MSE:", run.data.metrics.get("mse"))
    st.write("Features:", run.data.params.get("features"))