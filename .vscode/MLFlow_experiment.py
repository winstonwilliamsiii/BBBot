#mlflow_experiment.copy()

# mlflow_experiment.py

import mlflow
import pandas as pd

def log_experiment(df: pd.DataFrame, model_name="BentleyBudgetBot-TriggerModel"):
    mlflow.set_experiment(model_name)
    with mlflow.start_run():
        # Example logic: Buy signal if RSI < 30 and MACD > Signal
        df['prediction'] = (df['RSI'] < 30) & (df['MACD'] > df['Signal'])
        accuracy = df['prediction'].mean()

        mlflow.log_param("model_type", "rule-based")
        mlflow.log_metric("buy_signal_accuracy", accuracy)
        mlflow.log_metric("total_signals", len(df))
        mlflow.log_metric("positive_signals", df['prediction'].sum())

        # Optional: save predictions
        df.to_csv("predictions.csv", index=False)
        mlflow.log_artifact("predictions.csv")

        print(f"Logged MLFlow run with accuracy: {accuracy:.2f}")