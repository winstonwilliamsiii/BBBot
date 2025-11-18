# KNIME-compatible Python node: RSI, MACD, Trigger

# pandas is available in KNIME environment for DataFrame operations
import pandas as pd

# === Input: KNIME passes input_table as a DataFrame ===
# For standalone testing, create a sample input_table
# In KNIME environment, this would be provided automatically
if 'input_table' not in globals():
    input_table = pd.DataFrame({'close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113, 115, 117, 116, 118, 120]})

closes = input_table['close'].tolist()

# === RSI Calculation ===
def calculate_rsi(price_data, period=14):
    rsi = [None] * period
    for i in range(period, len(price_data)):
        gains = losses = 0
        for j in range(i - period + 1, i + 1):
            delta = price_data[j] - price_data[j - 1]
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

def calculate_macd(price_data, short=12, long=26, signal=9):
    ema_short = ema(price_data, short)
    ema_long = ema(price_data, long)
    macd_line = [s - l for s, l in zip(ema_short, ema_long)]
    signal_line = ema(macd_line[long - 1:], signal)
    return macd_line[long - 1:], signal_line

# === Trigger Logic ===
def evaluate_triggers(dataframe):
    dataframe['trigger'] = None
    dataframe.loc[(dataframe['RSI'] < 30) & (dataframe['MACD'] > dataframe['Signal']), 'trigger'] = 'BUY'
    dataframe.loc[(dataframe['RSI'] > 70) & (dataframe['MACD'] < dataframe['Signal']), 'trigger'] = 'SELL'
    return dataframe

# === Apply Calculations ===
df = input_table.copy()
df['RSI'] = calculate_rsi(closes)
macd_line, signal_line = calculate_macd(closes)
df['MACD'] = [None] * (len(df) - len(macd_line)) + macd_line
df['Signal'] = [None] * (len(df) - len(signal_line)) + signal_line
df = evaluate_triggers(df)

# === Output: KNIME expects output_table ===
output_table = df