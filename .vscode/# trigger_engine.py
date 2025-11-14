## trigger_engine.py

def evaluate_triggers(df, ruleset):
    """
    Apply trigger rules to a DataFrame of indicators.
    ruleset: list of dicts like:
        {
            "indicator": "RSI",
            "condition": "<",
            "threshold": 30,
            "action": "BUY",
            "asset": "BTCUSDT"
        }
    """
    df['trigger_action'] = None
    for rule in ruleset:
        indicator = rule['indicator']
        condition = rule['condition']
        threshold = rule['threshold']
        action = rule['action']

        if condition == '<':
            mask = df[indicator] < threshold
        elif condition == '>':
            mask = df[indicator] > threshold
        elif condition == '<=':
            mask = df[indicator] <= threshold
        elif condition == '>=':
            mask = df[indicator] >= threshold
        else:
            continue

        df.loc[mask, 'trigger_action'] = action
    return df