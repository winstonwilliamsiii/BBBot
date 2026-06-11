#MLFLOW_TRAINING DASHBOARD

# streamlit_app/mlflow_training.py
import streamlit as st
import mlflow
import pandas as pd

def render():
    st.title("🧠 MLflow Training Dashboard")

    st.subheader("Active Experiments")
    experiments = mlflow.search_experiments()
    exp_df = pd.DataFrame([{"Name": e.name, "ID": e.experiment_id} for e in experiments])
    st.dataframe(exp_df)

    selected_exp = st.selectbox("Select Experiment", exp_df["ID"])

    if selected_exp:
        st.subheader("Experiment Runs")
        runs = mlflow.search_runs(experiment_ids=[selected_exp])
        st.dataframe(runs[["run_id", "metrics.accuracy", "metrics.sharpe", "status"]])

        run_id = st.selectbox("Select Run", runs["run_id"])
        if run_id:
            st.subheader("Run Details")
            st.json(mlflow.get_run(run_id).data.metrics)

            st.subheader("Parameters")
            st.json(mlflow.get_run(run_id).data.params)