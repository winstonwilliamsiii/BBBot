#RIGEL FOREX ALPACA ADAPTABLE TO MT5

# Rigel EA Scaffold – Mean Reversion Strategy
# Adaptable to MT5 EA / Alpaca Paper Trading

# === Parameters ===
pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD"]
long_strategy = True   # toggle long/short
risk_per_trade = 0.01  # 1% of account equity
max_open_trades = 3    # liquidity discipline
session_hours = (9, 16)  # EST trading window

# === Indicators ===
def mean_reversion_signal(pair):
    ema_fast = EMA(pair, 20)
    ema_slow = EMA(pair, 50)
    rsi = RSI(pair, 14)
    bollinger = BollingerBands(pair, 20)

    if long_strategy:
        return ema_fast > ema_slow and rsi < 45 and PriceNearLowerBand(pair, bollinger)
    else:
        return ema_fast < ema_slow and rsi > 55 and PriceNearUpperBand(pair, bollinger)

# === Risk Management ===
def calculate_position_size(account_equity, pair, stop_loss_pips):
    risk_amount = account_equity * risk_per_trade
    pip_value = GetPipValue(pair)
    lot_size = risk_amount / (stop_loss_pips * pip_value)
    return min(lot_size, MaxLotAllowed(pair))

def enforce_liquidity():
    if CountOpenTrades() >= max_open_trades:
        return False
    return True

# === Trade Execution ===
def on_tick():
    current_hour = TimeHour(TimeCurrent())
    if session_hours[0] <= current_hour <= session_hours[1]:
        for pair in pairs:
            if mean_reversion_signal(pair) and enforce_liquidity():
                sl, tp = (50, 100) if long_strategy else (30, 60)
                lot_size = calculate_position_size(AccountEquity(), pair, sl)
                if long_strategy:
                    PlaceBuyOrder(pair, lot_size, SL=sl, TP=tp)
                else:
                    PlaceSellOrder(pair, lot_size, SL=sl, TP=tp)
                # ML integration placeholder (kept as comments for scaffold only)
                # ml_signal = MLModelPredict(pair)
                # if ml_signal == "BUY":
                #     PlaceBuyOrder(pair, lot_size, SL=sl, TP=tp)
                # elif ml_signal == "SELL":
                #     PlaceSellOrder(pair, lot_size, SL=sl, TP=tp)
        