# Bentley Bot — Master Bot Index

Complete reference for all trading bots in the Bentley platform.

---

## Bot Roster

| Bot | ID | Fund | Strategy | Asset Class | Status |
|-----|----|------|----------|-------------|--------|
| [Titan](#titan) | 1 | Mansa Tech | CNN + Tech Fundamentals | US Equities (Mag7/Tech) | Active |
| [Vega](#vega) | 2 | Mansa Retail | MTF-ML Breakout | US Equities (Retail) | Active |
| [Draco](#draco) | 3 | Mansa Money Bag | Sentiment Analyzer (ARIMA + NLP) | US Equities (Broad) | Active |
| [Altair](#altair) | 4 | Mansa AI | News Trading (AI Momentum) | US Equities (AI/Tech) | Scaffold |
| [Procryon](#procryon) | 5 | Mansa Crypto / Prop | KNN Spread Clustering + FNN Execution | Crypto CFDs / FX CFDs (MT5) | Active |
| [Hydra](#hydra) | 6 | Mansa Health | Healthcare Sector Momentum | US Equities (Healthcare) | Active |
| [Triton](#triton) | 7 | Mansa Transportation | ARIMA + LSTM Swing Trading | US Equities (Transport) | Active |
| [Dione](#dione) | 8 | Mansa Options | Put-Call Parity Arbitrage | Equity Options | Scaffold |
| [Orion](#orion) | ~9 | Mansa Minerals | Gold/Minerals RSI Scanner + FFNN | Commodities / ETFs (MT5) | Active |
| [Dogon](#dogon) | ~10 | Mansa ETF | XGBoost GBT + LSTM Ensemble | ETFs | Active |
| [Rigel](#rigel) | ~11 | Mansa Forex | Mean Reversion (EMA + RSI + BB) | Forex (7 pairs) | Active |
| [Rhea](#rhea) | 12 | Mansa ADI | ADI Intra-Day / Swing | US Equities | Scaffold |
| [Jupicita](#jupicita) | 13 | Mansa Smalls | Pairs Trading (Z-score) | Small-cap Equities | Scaffold |
| [Cephei](#cephei) | — | Mansa Cephei | Volatility Arbitrage | Options / Vol Products | Planned |

---

## Titan

- **Fund**: Mansa Tech | **Strategy**: Tech Fundamentals Screening + CNN Sequence Model
- **Universe**: Mag7 + large-cap tech (screener: `titan_tech_fundamentals.csv`)
- **Algorithm**: Fundamental screening (min_volume=5M, max_PE=40, min_ROE=15%, max_D/E=0.8) → CNN v2 (`TitanRiskModel/Production`)
- **Position size**: $5,000 | **Broker**: Alpaca | **Persistence**: MySQL
- **Docs**: [TITAN_README.md](root/TITAN_README.md) | [TITAN_BOT_QUICK_REFERENCE.md](root/TITAN_BOT_QUICK_REFERENCE.md)
- **Source**: `scripts/mansa_titan_bot.py` | **Config**: `bentley-bot/config/bots/titan.yml`

---

## Vega

- **Fund**: Mansa Retail | **Strategy**: MTF-ML Breakout Detection
- **Universe**: Retail_Breakouts screener (`vega_retail_breakout.csv`)
- **Algorithm**: Resistance breakout detection with ATR + volume confirmation; 1% risk per trade; ARIMA forecast (5-step)
- **Position size**: $1,500 | **Timeframe**: 15m | **Broker**: IBKR primary, Alpaca fallback
- **Risk**: breakout_buffer=1%, max_gap=8%, max_open=4, max_daily_loss=1.5%
- **Docs**: [VEGA_README.md](root/VEGA_README.md)
- **Source**: `vega_bot.py` | **Config**: `bentley-bot/config/bots/vega.yml`

---

## Draco

- **Fund**: Mansa Money Bag | **Strategy**: Multi-Factor Sentiment Analysis
- **Universe**: Sentiment_Leaders screener (`draco_sentiment_signals.csv`)
- **Algorithm**: Fundamentals (yfinance) + RSI technical + TextBlob NLP sentiment + ARIMA forecast → composite signal
- **Position size**: $2,000 | **Timeframe**: 1H | **Broker**: Alpaca primary, IBKR secondary
- **Risk**: min_sentiment_score=0.65, max_open=5, max_daily_loss=1.5%
- **Docs**: [DRACO_README.md](root/DRACO_README.md)
- **Source**: `draco_bot.py` | **Config**: `bentley-bot/config/bots/draco.yml`

---

## Altair

- **Fund**: Mansa AI | **Strategy**: News-Driven AI Momentum
- **Universe**: AI_News_Momentum screener | **Timeframe**: 30m
- **Algorithm**: NLP headline sentiment scoring (min_news_score=0.70) + price momentum confirmation; max hold 24h
- **Position size**: $1,800 | **Broker**: Alpaca
- **Status**: Scaffold — NLP pipeline and momentum layer not yet implemented
- **Docs**: [ALTAIR_README.md](root/ALTAIR_README.md)
- **Source**: `bentley-bot/bots/altair.py` | **Config**: `bentley-bot/config/bots/altair.yml`

---

## Procryon

- **Fund**: Mansa Crypto / Prop | **Strategy**: KNN Spread Clustering + MLP FNN Execution Optimization
- **Universe**: 10 crypto CFDs (BTC, ETH, LTC, XRP, BCH, ADA, SOL, DOT, LINK, AVAX) via MT5
- **Algorithm**: KNN (k=3) clusters bid-ask spread regime → MLP FNN (5 execution features, threshold=0.55) decides execute/skip
- **Position size**: $1,200 | **Timeframe**: 5m | **Broker**: FTMO (primary), AXI (secondary) via MT5
- **Risk**: max_spread=45bps, max_slippage=20bps, max_open=3, max_daily_loss=1%
- **Docs**: [PROCRYON_README.md](root/PROCRYON_README.md)
- **Source**: `procryon_bot.py` | **Config**: `bentley-bot/config/bots/procryon.yml`

---

## Hydra

- **Fund**: Mansa Health | **Strategy**: Healthcare Sector Momentum
- **Universe**: XLV, UNH, ELV, CI, CVS, HCA, ISRG, LLY, ABBV (9 stocks)
- **Algorithm**: 20-day momentum score (buy threshold=0.15) + SMA-50/200 crossover filter; TextBlob Stocktwits sentiment modifier
- **Position size**: $2,200 | **Timeframe**: 1D | **Broker**: Alpaca primary, IBKR (client_id=6) fallback
- **Integrations**: Airbyte (Stocktwits), Airflow DAG `hydra_mansa_health`, MLflow `Hydra_Mansa_Health`
- **Docs**: [HYDRA_QUICK_START.md](setup-guides/HYDRA_QUICK_START.md)
- **Source**: `hydra_bot.py` | **Config**: `bentley-bot/config/bots/hydra.yml`

---

## Triton

- **Fund**: Mansa Transportation | **Strategy**: ARIMA + LSTM Swing Trading
- **Universe**: IYT, UNP, CSX, NSC, UPS, FDX, DAL, UBER (8 transport stocks)
- **Algorithm**: ARIMA trend + LSTM sequence prediction + technicals + fundamentals + TextBlob sentiment; buy_threshold=+0.18, sell_threshold=-0.18
- **Position size**: configurable | **Timeframe**: 1D | **Broker**: Alpaca primary, IBKR (client_id=7) fallback
- **Docs**: [TRITON_README.md](root/TRITON_README.md) | [TRITON_QUICK_START.md](setup-guides/TRITON_QUICK_START.md)
- **Source**: `triton_bot.py` | **Config**: `bentley-bot/config/bots/triton.yml`

---

## Dione

- **Fund**: Mansa Options | **Strategy**: Put-Call Parity Arbitrage
- **Universe**: Options_Mispricing basket | **Timeframe**: 15m
- **Algorithm**: Computes theoretical put-call parity (C - P = S - Ke^(-rT)); enters when observed spread deviates > 2.5% from theory
- **Position size**: $2,500 | **Max contracts**: 5 | **Broker**: IBKR primary, Alpaca secondary
- **Status**: Scaffold — options chain integration and multi-leg order logic not yet implemented
- **Docs**: [DIONE_README.md](root/DIONE_README.md)
- **Source**: `bentley-bot/bots/dione.py` | **Config**: `bentley-bot/config/bots/dione.yml`

---

## Orion

- **Fund**: Mansa Minerals | **Strategy**: Gold/Minerals RSI Scanner + FFNN
- **Universe**: GDX primary + minerals/commodity ETF basket (YAML-configured)
- **Algorithm**: RSI-14 scan per symbol (YAML thresholds: oversold/overbought); highest-ranked symbol selected; FFNN trained on GDX for monitoring
- **Timeframe**: 1D | **Broker**: MT5 | **Config-driven**: volume_lots, stop_loss_pct, take_profit_pct all from YAML
- **Docs**: [ORION_README.md](root/ORION_README.md)
- **Source**: `scripts/orion_bot.py` | **Config**: `bentley-bot/config/bots/orion.yml`

---

## Dogon

- **Fund**: Mansa ETF | **Strategy**: ETF Allocation via XGBoost GBT + LSTM Ensemble
- **Algorithm**: 5-feature vectors (1d/5d/10d returns, 10d volatility, RSI-14) → XGBoost GBT + LSTM dual inference → ensemble BUY/HOLD signal
- **Data**: 90-day history via yfinance (Alpaca fallback) | **Broker**: Alpaca
- **Requires**: pre-trained model artifacts in `models/dogon/` (run `train_dogon_models.py` first)
- **Docs**: [DOGON_README.md](root/DOGON_README.md)
- **Source**: `scripts/dogon_bot.py` | **Training**: `scripts/train_dogon_models.py` | **Config**: `bentley-bot/config/bots/dogon.yml`

---

## Rigel

- **Fund**: Mansa Forex | **Strategy**: Mean Reversion Multi-Pair Forex
- **Universe**: EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, NZD/USD, USD/CAD (7 pairs)
- **Algorithm**: EMA(20/50) crossover + RSI-14 (oversold=45/overbought=55) + Bollinger Bands(20,2) + ATR-14; mean reversion entry at RSI extremes near BB bands
- **Risk**: 1% per trade, 50pip SL (long) / 30pip SL (short), max 3 positions, 25% liquidity buffer, max_daily_loss=5%
- **ML**: LSTM + XGBoost hybrid, 70% confidence threshold
- **Docs**: [RIGEL_README.md](root/RIGEL_README.md) | [RIGEL_QUICK_START.md](RIGEL_QUICK_START.md) | [RIGEL_ML_DEPLOYMENT.md](RIGEL_ML_DEPLOYMENT.md)
- **Source**: `scripts/rigel_forex_bot.py` | **Config**: `bentley-bot/config/bots/rigel.yml`

---

## Rhea

- **Fund**: Mansa ADI | **Strategy**: ADI Intra-Day / Swing Trading
- **Universe**: ADI_Swing_Basket | **Timeframe**: 30m
- **Algorithm**: Accumulation/Distribution Index with price-vs-ADI divergence detection; bullish divergence → BUY, bearish divergence → SELL; max hold=5 days
- **Position size**: $1,800 | **Broker**: Alpaca
- **Status**: Scaffold — ADI computation and divergence logic not yet implemented
- **Docs**: [RHEA_README.md](root/RHEA_README.md)
- **Source**: `bentley-bot/bots/rhea.py` | **Config**: `bentley-bot/config/bots/rhea.yml`

---

## Jupicita

- **Fund**: Mansa Smalls | **Strategy**: Statistical Pairs Trading
- **Universe**: Small_Cap_Pairs basket (co-integrated small-cap equity pairs) | **Timeframe**: 1H
- **Algorithm**: Engle-Granger co-integration → OLS hedge ratio β → Z-score of spread; entry at ±2.5σ, exit at 0, stop at ±4.0σ
- **Position size**: $1,400 | **Broker**: Alpaca primary, IBKR secondary
- **Status**: Scaffold — co-integration scanner, hedge ratio, and dual-leg order logic not yet implemented
- **Docs**: [JUPICITA_README.md](root/JUPICITA_README.md)
- **Source**: `bentley-bot/bots/jupicita.py` | **Config**: `bentley-bot/config/bots/jupicita.yml`

---

## Cephei

- **Fund**: Mansa Cephei | **Strategy**: Volatility Arbitrage (Planned)
- **Algorithm**: IV vs. RV edge (IV - RV); short vol when IV > RV, long vol when IV < RV; Black-Scholes IV inversion + GARCH/EWMA realized vol
- **Status**: Planned — no bot file or YAML config exists yet; registered in `Main.py` only
- **Docs**: [CEPHEI_README.md](root/CEPHEI_README.md)

---

## Documentation Map

| Bot | Full Strategy Ref | Quick Start |
|-----|------------------|------------|
| Titan | [TITAN_README.md](root/TITAN_README.md) | [TITAN_BOT_QUICK_REFERENCE.md](root/TITAN_BOT_QUICK_REFERENCE.md) |
| Vega | [VEGA_README.md](root/VEGA_README.md) | — |
| Draco | [DRACO_README.md](root/DRACO_README.md) | — |
| Altair | [ALTAIR_README.md](root/ALTAIR_README.md) | — |
| Procryon | [PROCRYON_README.md](root/PROCRYON_README.md) | — |
| Hydra | — | [HYDRA_QUICK_START.md](setup-guides/HYDRA_QUICK_START.md) |
| Triton | [TRITON_README.md](root/TRITON_README.md) | [TRITON_QUICK_START.md](setup-guides/TRITON_QUICK_START.md) |
| Dione | [DIONE_README.md](root/DIONE_README.md) | — |
| Orion | [ORION_README.md](root/ORION_README.md) | — |
| Dogon | [DOGON_README.md](root/DOGON_README.md) | — |
| Rigel | [RIGEL_README.md](root/RIGEL_README.md) | — |
| Rhea | [RHEA_README.md](root/RHEA_README.md) | — |
| Jupicita | [JUPICITA_README.md](root/JUPICITA_README.md) | — |
| Cephei | [CEPHEI_README.md](root/CEPHEI_README.md) | — |

---

## Bot Status Legend

| Status | Meaning |
|--------|---------|
| **Active** | Full implementation, runs in paper or live mode |
| **Scaffold** | Core framework in place; strategy logic implementation in progress |
| **Planned** | Registered in bot registry; no implementation file or config yet |
