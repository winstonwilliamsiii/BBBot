# Cephei Bot — Strategy Reference

## Overview

| Field | Value |
|-------|-------|
| **Fund** | Mansa Functions Options |
| **Strategy** | Options CFD Trading |
| **Asset Class** | Options / CFD |
| **Status** | **Active — `cephei_bot.py` operational** |

> **Note**: Cephei_Bot (`cephei_bot.py`) is operational. It provides FastAPI endpoints (`/analyze`, `/optuna_tune`, `/health`) with Siamese NN signal generation, LightGBM regime classification, GARCH vol forecasting, and IBKR CFD options execution hooks. IBKR API URL: `https://api.ibkr.com/v1/cfd/options`.

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

## Planned ML Architecture

### Signal Layer

| Component | Intended Role |
|-----------|--------------|
| **Black-Scholes IV Inversion** | Extract implied volatility from option prices |
| **GARCH / EWMA Forecast** | Estimate realized volatility from historical returns |
| **Siamese Network** | Compare IV vs. RV features and output a volatility mispricing score |

### Filter Layer

| Component | Intended Role |
|-----------|--------------|
| **LightGBM Regime Classifier** | Classify high-volatility vs. low-volatility market states |
| **Sentiment Module** | Incorporate macro news, order flow, and analyst chatter into the signal stack |
| **Trade Signal Decision** | Fuse volatility and sentiment inputs into a weighted trade decision |

### Execution Layer

| Component | Intended Role |
|-----------|--------------|
| **Delta-Neutral Spreads** | Deploy straddles or strangles to express vega exposure with hedged delta |
| **Greeks Monitor** | Track vega, gamma, and theta throughout the trade lifecycle |
| **RL Control Agent** | Dynamically manage position sizing, adjustment, and rebalancing |

### Framework Stack

| Layer | Framework | Purpose |
| --- | --- | --- |
| ML Core | PyTorch | VAE-LSTM + Siamese Network |
| Vol Forecast | Statsmodels | GARCH/EWMA |
| Regime Classifier | LightGBM | Fast volatility regime detection |
| Orchestration | FastAPI | Broker-agnostic deployment |
| Logging | MySQL + Railway | Compliance and forensic visibility |

---

## Implementation Checklist

When Cephei enters active development, the following must be created:

- [ ] `bentley-bot/bots/cephei.py` — Core bot implementation
- [ ] `bentley-bot/config/bots/cephei.yml` — Bot profile and risk config
- [ ] IV extraction pipeline (IBKR options chain → Black-Scholes IV)
- [ ] RV forecasting module (GARCH or EWMA on recent returns)
- [ ] Siamese mispricing model (IV vs. RV comparison and score output)
- [ ] LightGBM regime classifier (high-vol vs. low-vol state detection)
- [ ] Sentiment ingestion module (macro news, order flow, analyst chatter)
- [ ] Trade signal fusion engine (weighted volatility + sentiment decision)
- [ ] Multi-leg options order constructor (straddle / strangle / iron condor)
- [ ] Greeks tracker and hedge rebalancer
- [ ] RL control agent for position management and dynamic rebalancing
- [ ] MLflow experiment: `Cephei_Vol_Arb`
- [ ] `start_bot_mode.ps1` support (already in `Main.py` registry)
- [ ] Streamlit Admin Control Center panel (already in registry)

---

## References

- Black-Scholes Equation: Fischer Black & Myron Scholes (1973)
- Volatility Risk Premium literature: Carr & Wu (2009)
- IBKR Options API: [IBKR TWS API Docs](https://interactivebrokers.github.io/tws-api/)
