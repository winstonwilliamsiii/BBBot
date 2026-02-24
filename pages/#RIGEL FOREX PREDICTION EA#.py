#RIGEL FOREX PREDICTION EA#

# Rigel EA Scaffold – Mean Reversion + ML Prediction

pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD"]
risk_per_trade = 0.01
max_open_trades = 3
session_hours = (9, 16)  # EST trading window

# === ML Prediction Module ===
def ML_Predict(pair, recent_data):
    """
    Hybrid ML pipeline:
    - LSTM: short-term sequential price forecasting
    - XGBoost: feature-driven macro + technical importance
    Returns: "mean_revert", "trend", or "neutral"
    """
    lstm_signal = LSTM_Model.predict(recent_data)
    xgb_signal = XGB_Model.predict(recent_data)

    # Simple ensemble logic
    if lstm_signal == "revert" and xgb_signal == "revert":
        return "mean_revert"
    elif lstm_signal == "trend" or xgb_signal == "trend":
        return "trend"
    else:
        return "neutral"

# === Technical Signal ===
def mean_reversion_signal(pair):
    ema_fast = EMA(pair, 20)
    ema_slow = EMA(pair, 50)
    rsi = RSI(pair, 14)
    bollinger = BollingerBands(pair, 20)

    return ema_fast > ema_slow and rsi < 45 and PriceNearLowerBand(pair, bollinger)

# === Trade Execution ===
def on_tick():
    current_hour = TimeHour(TimeCurrent())
    if session_hours[0] <= current_hour <= session_hours[1]:
        for pair in pairs:
            recent_data = GetRecentData(pair)
            ml_forecast = ML_Predict(pair, recent_data)

            if ml_forecast == "mean_revert" and mean_reversion_signal(pair):
                if enforce_liquidity():
                    sl, tp = (50, 100)
                    lot_size = calculate_position_size(AccountEquity(), pair, sl)
                    PlaceBuyOrder(pair, lot_size, SL=sl, TP=tp)