# Cygnus Bot - Strategy and Technical Reference

## Overview

| Field | Value |
|-------|-------|
| **Bot ID** | 15 |
| **Fund** | Mansa Short Fund |
| **Strategy** | Relative Value Arbitrage (Short Bias and Long Bias) |
| **ML Model** | Siamese Neural Network (pattern similarity) |
| **Primary Broker** | IBKR |
| **Secondary Broker** | Alpaca |
| **Asset Class** | Equity pairs / relative-value baskets |
| **Timeframe** | 1H |
| **Universe** | Pairs_Relative_Value |
| **Status** | Implemented in `cygnus_bot.py` |

---

## Fund Classification

Cygnus is the dedicated shorting fund bot.

- **Cygnus_Bot**: Mansa Short Fund (relative value short/long bias)
- **Dione_Bot**: Options fund strategy (put-call parity)
- **Cephei_Bot**: Options/volatility arbitrage strategy

This classification should be used consistently across docs, dashboard labels, and API metadata.

---

## Strategy: Relative Value Arbitrage

Cygnus compares two related instruments and trades temporary dislocations in their spread.

$$
Spread_t = P_{x,t} - \beta \cdot P_{y,t}
$$

$$
Z_t = \frac{Spread_t - \mu(Spread)}{\sigma(Spread)}
$$

Core decision logic blends:
- Bollinger bandwidth on spread
- SMI crossover convergence
- Engle-Granger cointegration p-value
- RSI divergence
- NLP sentiment score from headlines
- Siamese similarity proxy

### Entry Heuristics

| Signal | Typical Action |
|--------|----------------|
| Z-score >= +1.5 with positive composite | Short bias (SELL) |
| Z-score <= -1.5 with negative composite | Long bias (BUY) |
| No strong dislocation | HOLD |

Cointegration (when available) is used as a statistical gate to reduce low-quality pair signals.

---

## API Surface

Defined in `cygnus_bot.py`:

- `GET /cygnus/health`
- `POST /cygnus/analyze`
- `POST /cygnus/locates`
- `POST /cygnus/margin`
- `POST /cygnus/trade`
- `POST /cygnus/train`
- `GET /cygnus/predict`

---

## Integrations

### Discord (Trade Notifications)

Cygnus publishes trade notifications through the shared notifier:
- `frontend/utils/discord_notify.py`

### MySQL (Trades and Performance)

Cygnus writes to:
- `trades_history`
- `performance_metrics`

Schema support migration:
- `migrations/20260506_add_cygnus_bot_schema.sql`

### MLflow

Experiment tracking:
- Experiment: `Cygnus_Mansa_Short_Fund`
- Tracking URI from `MLFLOW_TRACKING_URI` fallback resolution

---

## Configuration Files

- `bentley-bot/config/bots/cygnus.yml`
- `bentley-bot/config/cygnus_pairs.csv`
- `config/bots_config.yaml`
- `config/broker_mode_config.py`
- `config/broker_modes.json`

---

## Dependencies

Install Cygnus-specific dependencies using:

- `requirements-cygnus.txt`

Key packages include:
- `statsmodels` for cointegration testing
- `ib_insync` for broker connectivity
- `mlflow` for experiment logging

---

## Notes

- Locates/shortability checks depend on broker connectivity and market permissions.
- If cointegration libraries are unavailable, Cygnus degrades gracefully to heuristic scoring.
- Cygnus is intended for short-fund behavior, not options execution.
