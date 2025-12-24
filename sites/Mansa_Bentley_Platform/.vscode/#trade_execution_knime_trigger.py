#trade_execution_knime_trigger

# KNIME-compatible Python node: Execute trades from trigger column

from broker_api import execute_trade  # Ensure this module is accessible in KNIME's Python environment

# === Input: KNIME passes input_table as a DataFrame ===
df = input_table.copy()

# === Parameters ===
broker = 'binance'  # or 'webull', 'ibkr'
symbol = 'BTCUSDT'
quantity = 0.01

# === Trade Execution ===
latest = df.iloc[-1]
action = latest.get('trigger')

if action in ['BUY', 'SELL']:
    execute_trade(broker=broker, symbol=symbol, side=action, quantity=quantity)
    df['trade_status'] = f"{action} executed for {symbol}"
else:
    df['trade_status'] = "No trade triggered"

# === Output: KNIME expects output_table ===
output_table = df