#streamlit_integration_mlflow 
import pandas as pd
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()
experiment_id = client.get_experiment_by_name("BentleyBudgetBot-Trading").experiment_id
runs = client.search_runs(experiment_ids=[experiment_id])

df = pd.DataFrame([run.data.metrics for run in runs])
st.title("BentleyBudgetBot MLFlow Metrics")
st.dataframe(df)