# Jupicita Bot — Strategy & Technical Reference

## Overview

| Field | Value |
|-------|-------|
| **Bot ID** | 13 |
| **Fund** | Mansa Smalls |
| **Strategy** | Statistical Pairs Trading (Small Cap) |
| **Primary Broker** | Alpaca |
| **Secondary Broker** | IBKR |
| **Asset Class** | Small-cap equities (pairs) |
| **Timeframe** | 1H |
| **Universe** | Small_Cap_Pairs basket |
| **Status** | Implementation in progress (scaffold in `bentley-bot/bots/jupicita.py`) |

---

## Strategy: Statistical Pairs Trading

Jupicita identifies historically co-integrated small-cap equity pairs and trades the spread between them. When the spread between two correlated assets diverges beyond a Z-score threshold, Jupicita enters a market-neutral position — long the underperforming asset and short the outperforming one — expecting mean reversion.

### Pairs Trading Framework

$$\text{Spread}_t = P_{A,t} - \beta \cdot P_{B,t}$$

$$Z\text{-score}_t = \frac{\text{Spread}_t - \mu_{\text{spread}}}{\sigma_{\text{spread}}}$$

Where:
- $P_{A,t}$, $P_{B,t}$ = prices of the two paired assets at time $t$
- $\beta$ = hedge ratio (computed via OLS regression or Kalman filter)
- $\mu_{\text{spread}}$ = rolling mean of the spread
- $\sigma_{\text{spread}}$ = rolling standard deviation of the spread

### Entry / Exit Rules

| Action | Condition |
|--------|-----------|
| **Enter LONG spread** | Z-score < -2.5 (spread too low — A underpriced vs. B) |
| **Enter SHORT spread** | Z-score > +2.5 (spread too high — A overpriced vs. B) |
| **Exit** | Z-score reverts to 0 (spread mean reverts) |
| **Stop exit** | Z-score extends beyond ±4.0 (spread divergence failure) |

### Co-integration Testing

Pairs are validated for statistical co-integration using the Engle-Granger two-step test before being added to the active universe. Pairs with p-value > 0.05 are removed from rotation.

---

## Trade Parameters

```yaml
strategy:
  timeframe: 1H
  position_size: 1400
  label: Jupicita_Pairs_Trading

risk:
  max_pair_divergence_zscore: 2.5
  max_daily_loss_pct: 1.25
  max_open_positions: 4

execution:
  primary_client: alpaca_client
  secondary_client: ibkr_client
  mode: paper
  order_type: market
```

---

## Position Sizing & Risk Controls

| Parameter | Value |
|-----------|-------|
| **Position size** | $1,400 per pair (split long/short equally) |
| **Max open positions** | 4 pairs simultaneously |
| **Entry Z-score threshold** | ±2.5 |
| **Stop Z-score** | ±4.0 (divergence failure) |
| **Max daily loss** | 1.25% of account |

---

## Algorithms Used

| Algorithm | Role |
|-----------|------|
| **OLS Regression** | Hedge ratio (β) estimation |
| **Z-score normalization** | Spread position measurement |
| **Engle-Granger Test** | Co-integration validation |
| **Mean Reversion Timer** | Tracks spread convergence / forced exit |
| **Rolling Window** | Rolling mean and std for Z-score computation |

---

## Universe: Small Cap Pairs

Pairs are selected from small-cap equities (market cap < $2B) with:
- Minimum 6-month overlapping price history
- Co-integration p-value < 0.05
- Sector or industry correlation (avoids spurious correlations)

Pairs are refreshed periodically using a co-integration scanner.

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `JUPICITA_ENABLE_TRADING` | `false` | Set `true` to enable order submission |
| `JUPICITA_TRADING_MODE` | `paper` | `paper` or `live` |
| `JUPICITA_MAX_ZSCORE` | `2.5` | Entry Z-score threshold |
| `JUPICITA_STOP_ZSCORE` | `4.0` | Stop-loss Z-score divergence limit |
| `ALPACA_API_KEY` | — | Alpaca API key |
| `ALPACA_SECRET_KEY` | — | Alpaca API secret |
| `IBKR_HOST` | `127.0.0.1` | IBKR TWS host |
| `IBKR_PORT` | `7497` | Paper=7497, Live=7496 |
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | MLflow server |

---

## Main Files

| File | Purpose |
|------|---------|
| `bentley-bot/bots/jupicita.py` | Bot implementation (scaffold) |
| `bentley-bot/config/bots/jupicita.yml` | Bot profile and risk config |

---

## Implementation Notes

Jupicita is implemented as a scaffold bot. The remaining implementation work involves:

1. **Co-integration scanner** — Automated pair discovery using Engle-Granger across small-cap universe
2. **Hedge ratio estimation** — OLS or Kalman filter-based dynamic β calculation
3. **Z-score tracker** — Real-time rolling spread and Z-score computation
4. **Dual-leg order management** — Simultaneous long/short order submission and tracking
5. **Pair refresh logic** — Periodic re-validation and rotation of co-integrated pairs
6. **MLflow logging** — Log Z-scores, hedge ratios, spread stats, and pair trade outcomes

---

## Notification

Discord notification triggers on:
- `FVFI` signal (Fundamental Value Fair Interest)
- `ROVL` signal (Risk-Objective Validation Level)
