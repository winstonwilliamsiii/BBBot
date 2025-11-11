
#MACD Code 
function ema(values, period) {
  const k = 2 / (period + 1);
  const emaArray = [values[0]];
  for (let i = 1; i < values.length; i++) {
    emaArray.push(values[i] * k + emaArray[i - 1] * (1 - k));
  }
  return emaArray;
}

function calculateMACD(closes, shortPeriod = 12, longPeriod = 26, signalPeriod = 9) {
  const emaShort = ema(closes, shortPeriod);
  const emaLong = ema(closes, longPeriod);
  const macdLine = emaShort.map((val, i) => val - (emaLong[i] || 0));
  const signalLine = ema(macdLine.slice(longPeriod - 1), signalPeriod);
  const histogram = macdLine.slice(longPeriod - 1).map((val, i) => val - signalLine[i]);

  return {
    macdLine: macdLine.slice(longPeriod - 1),
    signalLine,
    histogram
  };
}