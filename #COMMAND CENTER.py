#COMMAND CENTER
# streamlit_app/app.py
import streamlit as st

st.set_page_config(page_title="Bentley Bot", layout="wide")

st.sidebar.title("🚀 Bentley Bot Navigation")

pages = {
    "Admin Dashboard": "admin",
    "MLflow Training": "mlflow_training",
    "Multi‑Broker Execution": "multi_broker",
    "Prop Firm Execution": "prop_execution",
    "Investor Dashboard": "investor",
}

choice = st.sidebar.radio("Go to:", list(pages.keys()))

if choice == "Admin Dashboard":
    import admin
    admin.render()

elif choice == "MLflow Training":
    import mlflow_training
    mlflow_training.render()

elif choice == "Multi‑Broker Execution":
    import multi_broker
    multi_broker.render()

elif choice == "Prop Firm Execution":
    import prop_execution
    prop_execution.render()

elif choice == "Investor Dashboard":
    import investor
    investor.render()
    
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