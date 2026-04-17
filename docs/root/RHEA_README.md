# Rhea Bot — Strategy & Technical Reference

## Overview

| Field | Value |
|-------|-------|
| **Bot ID** | 12 |
| **Fund** | Mansa ADI |
| **Strategy** | Accumulation/Distribution Index (ADI) Intra-Day / Swing |
| **Primary Broker** | Alpaca |
| **Asset Class** | Equities |
| **Timeframe** | 30m |
| **Universe** | ADI_Swing_Basket |
| **Status** | Implementation in progress (scaffold in `bentley-bot/bots/rhea.py`) |

---

## Strategy: ADI-Based Intra-Day and Swing Trading

Rhea trades equities using the Accumulation/Distribution Index (ADI) as the primary signal indicator. ADI measures cumulative flow of money into and out of a security by weighting volume by close price position within the day's range. Divergence between price trend and ADI trend generates trade signals.

### Accumulation/Distribution Index Formula

$$ADI_t = ADI_{t-1} + \left(\frac{(C_t - L_t) - (H_t - C_t)}{H_t - L_t}\right) \times V_t$$

Where:
- $C_t$ = Close price
- $L_t$ = Low price
- $H_t$ = High price
- $V_t$ = Volume

The multiplier (money flow multiplier) ranges from `-1` (close at low) to `+1` (close at high).

### Signal Logic

| Signal | Condition |
|--------|-----------|
| **BUY** | Price making lower lows, ADI making higher lows (bullish divergence) |
| **SELL** | Price making higher highs, ADI making lower highs (bearish divergence) |
| **HOLD** | No divergence detected |

Divergence is computed over a configurable lookback window on the 30m timeframe.

### Intra-Day vs. Swing Mode

- **Intra-Day**: Targets same-session reversals; positions opened and closed within the trading day
- **Swing**: Holds for up to `max_holding_days` (5 days) when ADI trend persists across sessions

---

## Trade Parameters

```yaml
strategy:
  timeframe: 30m
  position_size: 1800
  label: Rhea_ADI_Swing

risk:
  max_holding_days: 5
  max_daily_loss_pct: 1.25
  max_open_positions: 5

execution:
  primary_client: alpaca_client
  mode: paper
  order_type: market
```

---

## Position Sizing & Risk Controls

| Parameter | Value |
|-----------|-------|
| **Position size** | $1,800 per trade |
| **Max open positions** | 5 |
| **Max holding period** | 5 days (swing mode) |
| **Max daily loss** | 1.25% of account |

---

## Algorithms Used

| Algorithm | Role |
|-----------|------|
| **Accumulation/Distribution Index** | Primary signal indicator (money flow) |
| **Divergence Detection** | Price-vs-ADI divergence for entry signal |
| **Swing Hold Timer** | Tracks position age; forces exit at max_holding_days |
| **Intra-Day Mode** | Auto-closes all positions at EOD when in intra-day mode |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `RHEA_ENABLE_TRADING` | `false` | Set `true` to enable order submission |
| `RHEA_TRADING_MODE` | `paper` | `paper` or `live` |
| `RHEA_MAX_HOLDING_DAYS` | `5` | Max swing hold duration |
| `RHEA_INTRADAY_MODE` | `false` | Set `true` to enforce same-day close |
| `ALPACA_API_KEY` | — | Alpaca API key |
| `ALPACA_SECRET_KEY` | — | Alpaca API secret |
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | MLflow server |

---

## Main Files

| File | Purpose |
|------|---------|
| `bentley-bot/bots/rhea.py` | Bot implementation (scaffold) |
| `bentley-bot/config/bots/rhea.yml` | Bot profile and risk config |

---

## Implementation Notes

Rhea is implemented as a scaffold bot. The remaining implementation work involves:

1. **ADI calculation** — Real-time OHLCV ingestion and ADI series computation
2. **Divergence detection** — Price-vs-ADI peak/trough comparison algorithm
3. **Mode selector** — Intra-day vs. swing toggle with EOD auto-close logic
4. **Entry/exit logic** — Order submission with divergence-based stop loss
5. **MLflow logging** — Log ADI values, divergence scores, and trade outcomes

---

## Notification

Discord notification triggers on:
- `FVFI` signal (Fundamental Value Fair Interest)
- `ROVL` signal (Risk-Objective Validation Level)
