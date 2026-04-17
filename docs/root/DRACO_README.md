# Draco Bot — Strategy & Technical Reference

## Overview

| Field | Value |
|-------|-------|
| **Bot ID** | 3 |
| **Fund** | Mansa Money Bag |
| **Strategy** | Sentiment Analyzer |
| **Primary Broker** | Alpaca |
| **Secondary Broker** | IBKR |
| **Asset Class** | Equities (broad market sentiment leaders) |
| **Timeframe** | 1H |
| **Universe** | Sentiment_Leaders screener (`draco_sentiment_signals.csv`) |

---

## Strategy: Multi-Factor Sentiment Analysis

Draco combines fundamental analysis, technical indicators, NLP sentiment scoring from news headlines, and ARIMA time-series forecasting to produce a composite trade signal. All factors are weighted and logged to MLflow.

### Signal Generation Pipeline

1. **Fundamentals Pull** — Fetches P/E, EPS, market cap, 52-week range from Yahoo Finance fast-info.
2. **Technical Analysis** — Computes RSI (14-period) and momentum from historical OHLCV data.
3. **Sentiment Scoring** — Headlines scored via TextBlob polarity (`-1.0` to `+1.0`). Fallback keyword dictionary used when TextBlob unavailable.
4. **ARIMA Forecast** — Fits an ARIMA model to recent close prices and projects `forecast_steps` periods forward. Forecast direction (up/down/neutral) used as a signal component.
5. **Composite Signal** — The four factors are combined with configurable weights to produce a final BUY / SELL / HOLD signal.

### Sentiment Scoring Detail

```
positive keywords: beat, bullish, growth, improves, launch, outperform, strong, surge, upgrade
negative keywords: bearish, cut, decline, downgrade, investigation, miss, recall, weak
```

Sentiment score = `(positive_hits - negative_hits) / max(word_count, 4)` clamped to `[-1.0, 1.0]`.

Minimum required sentiment score for a BUY signal: **0.65**

### ARIMA Configuration

- Model order: auto-fit to recent price history
- Forecast horizon: 5 steps (default, configurable via `DRACO_FORECAST_STEPS`)
- History window: 1 year (`DRACO_HISTORY_PERIOD=1y`), daily bars (`DRACO_HISTORY_INTERVAL=1d`)

---

## Trade Parameters

```yaml
strategy:
  timeframe: 1H
  position_size: 2000
  label: Draco_Sentiment_Analyzer

risk:
  min_sentiment_score: 0.65
  max_position_size: 2000
  max_daily_loss_pct: 1.5
  max_open_positions: 5

execution:
  primary_client: alpaca_client
  secondary_client: ibkr_client
  mode: paper
  order_type: market
```

---

## Algorithms Used

| Algorithm | Role |
|-----------|------|
| **TextBlob NLP** | Headline polarity scoring |
| **Keyword fallback** | Polarity scoring when TextBlob unavailable |
| **ARIMA** (`statsmodels`) | Short-term price forecasting |
| **RSI (14-period)** | Momentum/overbought-oversold filtering |
| **Yahoo Finance fast_info** | Fundamental data ingestion |

---

## FastAPI Routes

Served via `Main.py` on port **5001**.

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/draco/health` | Dependency and broker health check |
| GET | `/draco/status` | Current config and last analysis |
| POST | `/draco/analyze` | Run full multi-factor analysis for a ticker |
| POST | `/draco/trade` | Submit a buy/sell order |

### Example: Analyze a ticker

```powershell
Invoke-WebRequest http://localhost:5001/draco/analyze `
  -Method POST -ContentType "application/json" `
  -Body '{"ticker":"AMZN","news_headlines":["Amazon beats Q4 estimates, upgrades guidance"]}'
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DRACO_ENABLE_TRADING` | `false` | Set `true` to enable order submission |
| `DRACO_ENABLE_MLFLOW_LOGGING` | `true` | Toggle MLflow run logging |
| `DRACO_MLFLOW_EXPERIMENT` | `draco_bot_analysis` | MLflow experiment name |
| `DRACO_FORECAST_STEPS` | `5` | ARIMA forward steps |
| `DRACO_HISTORY_PERIOD` | `1y` | Historical data lookback |
| `DRACO_HISTORY_INTERVAL` | `1d` | Bar interval |
| `ALPACA_API_KEY` | — | Alpaca API key |
| `ALPACA_SECRET_KEY` | — | Alpaca API secret |
| `IBKR_HOST` | `127.0.0.1` | IBKR TWS host |
| `IBKR_PORT` | `7497` | IBKR TWS port (paper) |
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | MLflow server |

---

## Main Files

| File | Purpose |
|------|---------|
| `draco_bot.py` | Core FastAPI app and strategy logic |
| `bentley-bot/config/bots/draco.yml` | Bot profile and risk config |
| `bentley-bot/bots/draco.py` | Legacy stub |

---

## MLflow Integration

- Experiment: `draco_bot_analysis`
- Logs: sentiment scores, ARIMA forecast direction, composite signal, trade outcomes
- Metrics tracked: sentiment_score, rsi_value, forecast_direction, signal_confidence

---

## Dependency Matrix

| Package | Purpose | Required? |
|---------|---------|-----------|
| `yfinance` | Market data and fundamentals | Yes |
| `pandas` | Data manipulation | Yes |
| `statsmodels` | ARIMA forecasting | Yes |
| `textblob` | NLP sentiment | Optional (keyword fallback) |
| `mlflow` | Run tracking | Optional |
| `alpaca_trade_api` | Order execution | Conditional |
| `ib_insync` | IBKR execution | Conditional |

---

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| `statsmodels` unavailable | Install via `pip install statsmodels` |
| ARIMA convergence warning | Normal for short series; increase `DRACO_HISTORY_PERIOD` |
| Low sentiment scores | Check headline quality; minimum threshold is 0.65 |
| MLflow 503 | Set `DRACO_ENABLE_MLFLOW_LOGGING=false` to skip |
