# Cephei Bot — Strategy Reference (Planned)

## Overview

| Field | Value |
|-------|-------|
| **Fund** | Mansa Cephei |
| **Strategy** | Volatility Arbitrage |
| **Asset Class** | Options / Volatility products |
| **Status** | **Planned — Not yet implemented** |

> **Note**: Cephei is registered in the bot registry (`Main.py`) but has no implementation file or config YAML yet. This document records the planned strategy for reference.

---

## Planned Strategy: Volatility Arbitrage

Volatility arbitrage exploits the difference between the **implied volatility (IV)** priced into options contracts and the **realized volatility (RV)** of the underlying asset.

### Core Relationship

$$\text{Vol Edge} = IV - RV$$

Where:
- **IV** = Implied volatility derived from option market prices (via Black-Scholes inversion)
- **RV** = Realized (historical) volatility computed from recent daily/intraday price returns

When $IV > RV$ (volatility risk premium), the strategy sells volatility (e.g., short straddle/strangle, short vega positions).  
When $IV < RV$ (cheap volatility), the strategy buys volatility (e.g., long straddle/vega).

### Potential Instruments

- **Equity options** on individual underlyings
- **VIX products** (VIX futures, VIXY, UVXY) for index volatility
- **Variance swaps** or **vol ETFs** as synthetic proxies

---

## Anticipated Trade Parameters

| Parameter | Estimated Value |
|-----------|----------------|
| **Fund** | Mansa Cephei |
| **Position size** | TBD |
| **Max vega exposure** | TBD |
| **IV/RV threshold** | TBD (e.g., IV premium > 5 vol points) |
| **Max daily loss** | TBD |
| **Broker** | IBKR (options required) |

---

## Planned Algorithms

| Algorithm | Intended Role |
|-----------|--------------|
| **Black-Scholes IV inversion** | Extract implied volatility from option prices |
| **GARCH / EWMA** | Forecast realized volatility |
| **Vol regime classification** | Identify high-vol vs. low-vol regimes |
| **Delta-neutral construction** | Build vega-positive/negative positions with hedged delta |
| **Greeks monitoring** | Manage vega, gamma, theta exposure over the holding period |

---

## Implementation Checklist

When Cephei enters active development, the following must be created:

- [ ] `bentley-bot/bots/cephei.py` — Core bot implementation
- [ ] `bentley-bot/config/bots/cephei.yml` — Bot profile and risk config
- [ ] IV extraction pipeline (IBKR options chain → Black-Scholes IV)
- [ ] RV computation module (GARCH or EWMA on recent returns)
- [ ] Volatility signal generator (vol edge calculator)
- [ ] Multi-leg options order constructor (straddle / strangle / iron condor)
- [ ] Greeks tracker and hedge rebalancer
- [ ] MLflow experiment: `Cephei_Vol_Arb`
- [ ] `start_bot_mode.ps1` support (already in `Main.py` registry)
- [ ] Streamlit Admin Control Center panel (already in registry)

---

## References

- Black-Scholes Equation: Fischer Black & Myron Scholes (1973)
- Volatility Risk Premium literature: Carr & Wu (2009)
- IBKR Options API: [IBKR TWS API Docs](https://interactivebrokers.github.io/tws-api/)
