# Vega Bot — Strategy & Technical Reference

## Overview

| Field | Value |
|-------|-------|
| **Bot ID** | 2 |
| **Fund** | Mansa Retail |
| **Strategy** | Vega Mansa Retail MTF-ML (Multi-Timeframe Machine Learning Breakout) |
| **Primary Broker** | IBKR (paper port 7497 / live port 7496) |
| **Fallback Broker** | Alpaca (paper) |
| **Asset Class** | Equities / Retail sector |
| **Timeframe** | 15m (intraday breakout) |
| **Universe** | Retail_Breakouts screener (`vega_retail_breakout.csv`) |

---

## Strategy: Multi-Timeframe Breakout (MTF-ML)

Vega identifies price breakout events above a key resistance level, confirmed by volume and ATR-based filters, then executes directional trades with tight risk controls.

### Signal Generation Logic

1. **Breakout Level Detection** — Identifies a resistance level from recent price history. If not provided, computed dynamically from Yahoo Finance OHLCV data.
2. **Volume Confirmation** — Current volume must exceed a threshold (default 1,000,000 daily). Spikes below threshold are rejected.
3. **ATR Filter** — Average True Range gates the trade entry to avoid low-volatility false breakouts.
4. **Direction** — Defaults to `auto` (inferred from price action). Can be forced to `long` or `short`.
5. **News Sentiment** — Optional headlines scored via TextBlob polarity; bearish headlines can veto bullish breakouts.
6. **Forecast** — 5-step forward projection (configurable) logged to MLflow for drift monitoring.

### Entry Criteria

- Price must close above identified breakout level
- Volume confirmation required (>1M shares/day)
- Breakout buffer: 1.0% above the level (avoids false breakouts)
- Max gap from breakout level: 8.0% (avoids chasing extended moves)
- Max daily loss guard: 1.5% of account

### Position Sizing & Risk

| Parameter | Value |
|-----------|-------|
| **Default position size** | $1,500 |
| **Risk per trade** | 1% of equity (`risk_pct=0.01`) |
| **Max risk_pct allowed** | 5% |
| **Stop loss** | Computed from entry and risk_pct |
| **Take profit** | Computed to maintain minimum R:R |
| **Max open positions** | 4 |

---

## Algorithms Used

### Breakout Detection
- Resistance level computed from recent high (configurable lookback)
- Entry confirmed when price exceeds level + buffer %

### TextBlob Sentiment Scoring
- News headlines scored for polarity: `[-1.0, +1.0]`
- Negative polarity above a threshold vetoes long entries
- Fallback keyword-based scoring when TextBlob unavailable

### ARIMA Forecast (via MLflow)
- Short-term price forecast logged to MLflow experiment `vega_bot_analysis`
- Used for dashboard visibility and trend bias, not hard trade gating

---

## Trade Parameters

```yaml
strategy:
  timeframe: 15m
  position_size: 1500
  breakout_buffer_pct: 1.0
  max_gap_pct: 8.0

risk:
  min_volume: 1000000
  max_daily_loss_pct: 1.5
  max_open_positions: 4
  risk_pct: 0.01          # 1% per trade
  max_risk_pct: 0.05      # 5% ceiling

execution:
  ibkr_port_paper: 7497
  ibkr_port_live: 7496
  alpaca_fallback: true
  order_type: market
```

---

## FastAPI Routes

Served via `Main.py` on port **5001**.

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/vega/health` | Health check — broker and MLflow readiness |
| GET | `/vega/status` | Status snapshot with last analysis |
| POST | `/vega/signal` | Detect breakout signal for a ticker |
| POST | `/vega/execute` | Submit a breakout trade |
| POST | `/vega/trade` | Direct buy/sell with qty |
| POST | `/vega/log-trade` | Audit log a closed trade to MySQL |
| GET | `/vega/history` | Fetch recent trade history |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `VEGA_ENABLE_TRADING` | `false` | Set `true` to enable order submission |
| `VEGA_TRADING_MODE` | `paper` | `paper` or `live` |
| `IBKR_HOST` | `127.0.0.1` | TWS/Gateway host |
| `IBKR_PORT` | `7497` | Paper=7497, Live=7496 |
| `IBKR_CLIENT_ID` | `1` | IBKR client slot |
| `ALPACA_API_KEY` | — | Alpaca fallback key |
| `ALPACA_SECRET_KEY` | — | Alpaca fallback secret |
| `VEGA_MLFLOW_EXPERIMENT` | `vega_bot_analysis` | MLflow experiment name |
| `VEGA_FORECAST_STEPS` | `5` | Forward forecast steps |
| `VEGA_HISTORY_PERIOD` | `6mo` | Historical data window |
| `VEGA_HISTORY_INTERVAL` | `1d` | Bar interval |

---

## Main Files

| File | Purpose |
|------|---------|
| `vega_bot.py` | Core FastAPI app and strategy logic |
| `scripts/vega_bot.py` | Script runner / CLI entry point |
| `bentley-bot/config/bots/vega.yml` | Bot profile and risk config |
| `tests/test_vega_bot.py` | Unit tests |

---

## MLflow Integration

- Experiment: `vega_bot_analysis`
- Logs: breakout signal results, forecast steps, trade outcomes
- Enables: performance trending, signal accuracy monitoring

---

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| IBKR connection refused | Ensure TWS/IB Gateway is running on configured port |
| "yfinance unavailable" | Install `yfinance` or provide price data via request body |
| MLflow unreachable | Set `VEGA_ENABLE_MLFLOW_LOGGING=false` to skip gracefully |
| Trading not executing | Set `VEGA_ENABLE_TRADING=true` after validating paper mode |
