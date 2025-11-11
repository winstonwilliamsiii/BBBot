#compute_indicators.py

# compute_indicators.py

import pandas as pd
from indicators import calculate_rsi, calculate_macd

# Simulate input data (replace with volume mount or API call)
closes = [100 + i for i in range(50)]  # Dummy close prices

rsi = calculate_rsi(closes)
macd = calculate_macd(closes)

df = pd.DataFrame({
    'close': closes[-len(rsi):],
    'RSI': rsi,
    'MACD': macd['macdLine'],
    'Signal': macd['signalLine']
})

df.to_csv("/app/data/indicators_output.csv", index=False)
print("RSI/MACD computed and saved.")