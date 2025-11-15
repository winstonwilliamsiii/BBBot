# KNIME-compatible Python node: RSI, MACD, Trigger

import pandas as pd

# === Input: KNIME passes input_table as a DataFrame ===
closes = input_table['close'].tolist()

# === RSI Calculation ===
def calculate_rsi(closes, period=14):
    rsi = [None] * period
    for i in range(period, len(closes)):
        gains = losses = 0
        for j in range(i - period + 1, i + 1):
            delta = closes[j] - closes[j - 1]
            if delta > 0:
                gains += delta
            else:
                losses -= delta
        rs = gains / (losses or 1e-10)
        rsi.append(100 - 100 / (1 + rs))
    return rsi

# === MACD Calculation ===
def ema(values, period):
    k = 2 / (period + 1)
    ema_vals = [values[0]]
    for i in range(1, len(values)):
        ema_vals.append(values[i] * k + ema_vals[i - 1] * (1 - k))
    return ema_vals

def calculate_macd(closes, short=12, long=26, signal=9):
    ema_short = ema(closes, short)
    ema_long = ema(closes, long)
    macd_line = [s - l for s, l in zip(ema_short, ema_long)]
    signal_line = ema(macd_line[long - 1:], signal)
    return macd_line[long - 1:], signal_line

# === Trigger Logic ===
def evaluate_triggers(df):
    df['trigger'] = None
    df.loc[(df['RSI'] < 30) & (df['MACD'] > df['Signal']), 'trigger'] = 'BUY'
    df.loc[(df['RSI'] > 70) & (df['MACD'] < df['Signal']), 'trigger'] = 'SELL'
    return df

# === Apply Calculations ===
df = input_table.copy()
df['RSI'] = calculate_rsi(closes)
macd_line, signal_line = calculate_macd(closes)
df['MACD'] = [None] * (len(df) - len(macd_line)) + macd_line
df['Signal'] = [None] * (len(df) - len(signal_line)) + signal_line
df = evaluate_triggers(df)

# === Output: KNIME expects output_table ===
output_table = df