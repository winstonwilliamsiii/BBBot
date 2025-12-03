#MLFlow regression model testing and logging
mlflow>=2.4.1
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

def train_and_log_roi_model(df: pd.DataFrame, ticker: str):
    """
    Train regression model to predict ROI from fundamentals and log to MLFlow.
    df: DataFrame with columns [pe_ratio, pb_ratio, ev_ebit, ev_ebitda, roa, noi, roi]
    """
    # Features and target
    X = df[["pe_ratio", "pb_ratio", "ev_ebit", "ev_ebitda", "roa", "noi"]].fillna(0)
    y = df["roi"].fillna(0)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Predictions
    y_pred = model.predict(X_test)

    # Metrics
    r2 = r2_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)

    # Log to MLFlow
    with mlflow.start_run(run_name=f"{ticker}_ROI_regression"):
        mlflow.log_param("ticker", ticker)
        mlflow.log_param("model_type", "LinearRegression")
        mlflow.log_param("features", ["pe_ratio","pb_ratio","ev_ebit","ev_ebitda","roa","noi"])

        mlflow.log_metric("r2_score", r2)
        mlflow.log_metric("mse", mse)

        # Log model
        mlflow.sklearn.log_model(model, artifact_path="roi_model")

        # Save predictions as artifact
        pred_df = pd.DataFrame({"y_true": y_test, "y_pred": y_pred})
        pred_df.to_csv("roi_predictions.csv", index=False)
        mlflow.log_artifact("roi_predictions.csv")