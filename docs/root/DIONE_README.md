# Dione Bot — Strategy & Technical Reference

## Overview

| Field | Value |
|-------|-------|
| **Bot ID** | 8 |
| **Fund** | Mansa Options |
| **Strategy** | Put-Call Parity Arbitrage |
| **Primary Broker** | IBKR |
| **Secondary Broker** | Alpaca |
| **Asset Class** | Options (Equity Options) |
| **Timeframe** | 15m |
| **Universe** | Options_Mispricing basket |
| **Status** | Implementation in progress (scaffold in `bentley-bot/bots/dione.py`) |

---

## Strategy: Put-Call Parity Arbitrage

Dione exploits pricing inefficiencies in equity options markets using the Put-Call Parity relationship. When the relationship is violated by more than a configurable spread threshold, Dione enters an arbitrage position to capture the mispricing as it reverts.

### Put-Call Parity Relationship

For European-style options:

$$C - P = S - K \cdot e^{-rT}$$

Where:
- $C$ = call option price
- $P$ = put option price
- $S$ = current underlying spot price
- $K$ = strike price
- $r$ = risk-free rate
- $T$ = time to expiry (years)

A violation occurs when the observed call-put spread deviates from the theoretical value by more than `max_option_spread` (2.5%).

### Signal Generation Logic

1. **Options Chain Scan** — For each symbol in the Options_Mispricing universe, fetch the options chain for the nearest ATM strike.
2. **Parity Calculation** — Compute the theoretical put-call spread using current spot price, strike, risk-free rate, and time-to-expiry.
3. **Mispricing Detection** — Compare observed spread to theoretical. If deviation > 2.5%, flag as a mispricing opportunity.
4. **Entry** — Enter a synthetic position to profit from reversion (e.g., buy call + sell put + short underlying, or reverse).
5. **Exit** — Close when mispricing reverts to within 0.5% of theoretical parity, or at max daily loss.

---

## Trade Parameters

```yaml
strategy:
  timeframe: 15m
  position_size: 2500
  label: Dione_Options_Mispricing

risk:
  max_contracts: 5
  max_option_spread: 2.5       # percent deviation to trigger entry
  max_daily_loss_pct: 1.25
  max_open_positions: 4

execution:
  primary_client: ibkr_client
  secondary_client: alpaca_client
  mode: paper
  order_type: market
```

---

## Position Sizing & Risk Controls

| Parameter | Value |
|-----------|-------|
| **Position size** | $2,500 per position |
| **Max contracts** | 5 per underlying |
| **Max option spread** | 2.5% deviation from parity |
| **Max open positions** | 4 |
| **Max daily loss** | 1.25% of account |

---

## Algorithms Used

| Algorithm | Role |
|-----------|------|
| **Put-Call Parity (Black-Scholes)** | Theoretical pricing baseline |
| **Mispricing Scanner** | Compares observed to theoretical spread |
| **ATM Strike Selection** | Picks nearest at-the-money strike per expiry |
| **Mean Reversion Timer** | Tracks holding duration and forced exit trigger |

---

## Broker Requirements

IBKR is the **required primary broker** for this bot because:
- IBKR provides live options chains via the TWS API
- Spread pricing on options is more accurate via IBKR data feeds
- Alpaca options support is limited (secondary/paper only)

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DIONE_ENABLE_TRADING` | `false` | Set `true` to enable order submission |
| `DIONE_TRADING_MODE` | `paper` | `paper` or `live` |
| `DIONE_MAX_OPTION_SPREAD` | `2.5` | Max spread % to trigger arbitrage |
| `DIONE_MAX_CONTRACTS` | `5` | Max contracts per leg |
| `IBKR_HOST` | `127.0.0.1` | IBKR TWS host |
| `IBKR_PORT` | `7497` | Paper=7497, Live=7496 |
| `ALPACA_API_KEY` | — | Alpaca fallback key |
| `ALPACA_SECRET_KEY` | — | Alpaca fallback secret |
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | MLflow server |

---

## Main Files

| File | Purpose |
|------|---------|
| `bentley-bot/bots/dione.py` | Bot implementation (scaffold) |
| `bentley-bot/config/bots/dione.yml` | Bot profile and risk config |

---

## Implementation Notes

Dione is implemented as a scaffold bot. The core bot registry, health check, and execution interface are in place. The remaining implementation work involves:

1. **Options chain fetching** — Connect IBKR TWS API to pull live options chains
2. **Parity calculation** — Implement the full Black-Scholes put-call parity check
3. **Synthetic position logic** — Build the multi-leg order constructor for arbitrage entries
4. **Greeks monitoring** — Delta-neutral position management (optional enhancement)
5. **MLflow logging** — Log parity deviations and trade outcomes

---

## Notification

Discord notification triggers on:
- `FVFI` signal (Fundamental Value Fair Interest)
- `ROVL` signal (Risk-Objective Validation Level)
