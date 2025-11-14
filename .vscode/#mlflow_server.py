#mlflow_server.py
import mlflow

mlflow.set_tracking_uri("mysql+pymysql://user:password@mysql-host:3306/mlflow_db")
mlflow.set_experiment("BentleyBudgetBot-Trading")