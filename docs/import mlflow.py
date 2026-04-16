import mlflow
from sklearn.preprocessing import StandardScaler

from scripts.sentiment_utils import notify_discord

import alpaca_trade_api as tradeapi
import os

api = tradeapi.REST(
    os.environ["ALPACA_API_KEY"],
    os.environ["ALPACA_SECRET_KEY"],
    base_url=os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
)

# --- ML Prediction Model (placeholder) ---
# In practice, load a trained model from MLflow
def load_model():
    model_uri = "models:/TitanRiskModel/Production"
    model = mlflow.sklearn.load_model(model_uri)
    return model


def load_model_scaler():
    """Load the pre-fitted scaler stored alongside the registered model."""
    scaler_uri = "models:/TitanRiskScaler/Production"
    scaler = mlflow.sklearn.load_model(scaler_uri)
    return scaler, scaler_uri

def titan_predict(symbol, features):
    """
    Predict trade viability using ML model.
    Features could include RSI, volatility, sentiment score, etc.
    """
    model = load_model()
    scaler, _ = load_model_scaler()  # load pre-fitted scaler alongside the model
    features_scaled = scaler.transform([features])
    prediction = model.predict(features_scaled)[0]
    probability = model.predict_proba(features_scaled)[0][1]

    try:
        mlflow.log_metric("titan_prediction_probability", probability)
    except mlflow.exceptions.MlflowException:
        pass  # no active run; metric logging is best-effort

    return prediction, probability
def titan_guard_with_ml(symbol, features, buffer_threshold=0.2):
    account = api.get_account()
    cash = float(account.cash)
    equity = float(account.equity)

    # Liquidity check
    if cash / equity < buffer_threshold:
        notify_discord("Titan blocked trade: liquidity buffer breached.")
        return False

    # ML prediction check
    prediction, prob = titan_predict(symbol, features)
    if prediction == 0:
        notify_discord(f"Titan blocked trade: ML model flagged risk (p={prob:.2f})")
        return False

    return True
