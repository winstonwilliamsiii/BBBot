# indicators.py

def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return [None] * len(closes)

    rsi = [None] * period
    for i in range(period, len(closes)):
        gains = 0
        losses = 0
        for j in range(i - period + 1, i + 1):
            delta = closes[j] - closes[j - 1]
            if delta > 0:
                gains += delta
            else:
                losses -= delta
        rs = gains / (losses or 1e-10)
        rsi.append(100 - 100 / (1 + rs))
    return rsi

def calculate_macd(closes, short_period=12, long_period=26, signal_period=9):
    def ema(values, period):
        k = 2 / (period + 1)
        ema_vals = [values[0]]
        for i in range(1, len(values)):
            ema_vals.append(values[i] * k + ema_vals[i - 1] * (1 - k))
        return ema_vals

    ema_short = ema(closes, short_period)
    ema_long = ema(closes, long_period)
    macd_line = [s - l for s, l in zip(ema_short, ema_long)]
    signal_line = ema(macd_line[long_period - 1:], signal_period)
    histogram = [m - s for m, s in zip(macd_line[long_period - 1:], signal_line)]

    return {
        "macdLine": macd_line[long_period - 1:],
        "signalLine": signal_line,
        "histogram": histogram
    }