symbol = knime.workflow_variable("symbol")
quantity = float(knime.workflow_variable("quantity"))
trigger = knime.workflow_variable("trigger")

# Example logic
if trigger == "BUY":
    result = f"Buying {quantity} of {symbol}"
elif trigger == "SELL":
    result = f"Selling {quantity} of {symbol}"
else:
    result = "No action"

output_table = pd.DataFrame({"action": [result]})