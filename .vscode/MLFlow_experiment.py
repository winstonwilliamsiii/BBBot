# MLFlow experiment tracking for Bentley Budget Bot

# mlflow_experiment.py

try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    mlflow = None

import pandas as pd


def log_experiment(df: pd.DataFrame, 
                   model_name="BentleyBudgetBot-TriggerModel"):
    """Log experiment results to MLFlow if available."""
    if not MLFLOW_AVAILABLE:
        print("MLFlow not available. Skipping experiment logging.")
        return
    
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


def log_simple_metrics(metrics_dict: dict, run_name: str = None):
    """Log simple metrics without complex model tracking."""
    if not MLFLOW_AVAILABLE:
        print("MLFlow not available. Printing metrics instead:")
        for key, value in metrics_dict.items():
            print(f"  {key}: {value}")
        return
    
    with mlflow.start_run(run_name=run_name):
        for key, value in metrics_dict.items():
            if isinstance(value, (int, float)):
                mlflow.log_metric(key, value)
            else:
                mlflow.log_param(key, str(value))
        print(f"Logged metrics to MLFlow: {list(metrics_dict.keys())}")