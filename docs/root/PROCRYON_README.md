# Procryon Bot — Strategy & Technical Reference

## Overview

| Field | Value |
|-------|-------|
| **Bot ID** | 5 |
| **Fund** | Prop Trading Fund (Mansa Crypto) |
| **Strategy** | MT5 Spread Arbitrage — KNN Clustering + FNN Execution Optimization |
| **Primary Execution** | MetaTrader 5 (FTMO) |
| **Secondary Execution** | MetaTrader 5 (AXI) |
| **Asset Class** | Crypto CFDs and FX CFDs via MT5 |
| **Timeframe** | 5m |
| **Universe** | MT5_FX_CFD_Crypto_CFD |
| **Default Symbol** | BTCUSD |

---

## Strategy: KNN Spread Regime Clustering + FNN Execution Optimization

Procryon operates across crypto and FX CFD markets via MetaTrader 5. The strategy uses two ML models in sequence:

1. **KNN Classifier** — clusters the current bid-ask spread into one of three regimes (tight / normal / wide), identifying favorable execution windows.
2. **MLP FNN (Multi-Layer Perceptron Feed-Forward Network)** — evaluates five execution quality features and decides whether to submit an order or wait.

### Stage 1: Spread Regime Classification (KNN)

```
Features (3):
  - bid_ask_spread_bps    — current spread in basis points
  - spread_zscore         — normalized spread vs. recent history
  - spread_volatility     — rolling volatility of spread

K = 3 nearest neighbors
Regimes: 0 = TIGHT (favorable), 1 = NORMAL, 2 = WIDE (avoid)
```

Orders are only considered when KNN classifies spread as `TIGHT` or `NORMAL`.

### Stage 2: Execution Decision (MLP FNN)

```
Features (5):
  - latency_ms            — current API/network latency
  - liquidity_depth       — book depth at best bid/ask
  - fee_bps               — applicable trading fee in bps
  - slippage_bps          — estimated slippage from recent fills
  - venue_confidence      — broker venue confidence score (0–1)

Decision: EXECUTE if FNN output probability >= 0.55 (execution_threshold)
          SKIP otherwise
```

Both models use `StandardScaler` normalization. Pre-trained artifacts loaded from `models/procryon/`.

---

## Trade Parameters

```yaml
strategy:
  timeframe: 5m
  position_size: 1200
  universe: MT5_FX_CFD_Crypto_CFD
  execution_threshold: 0.55

risk:
  max_spread_bps: 45
  max_slippage_bps: 20
  max_daily_loss_pct: 1.0
  max_open_positions: 3

execution:
  primary_client: mt5 (FTMO)
  secondary_client: mt5 (AXI)
  mode: paper
  order_type: market
```

---

## Crypto Universe

| Symbol | Asset |
|--------|-------|
| BTCUSD | Bitcoin |
| ETHUSD | Ethereum |
| LTCUSD | Litecoin |
| XRPUSD | Ripple |
| BCHUSD | Bitcoin Cash |
| ADAUSD | Cardano |
| SOLUSD | Solana |
| DOTUSD | Polkadot |
| LINKUSD | Chainlink |
| AVAXUSD | Avalanche |

---

## Algorithms Used

| Algorithm | Library | Role |
|-----------|---------|------|
| **K-Nearest Neighbors (K=3)** | `scikit-learn` | Spread regime clustering |
| **MLP Classifier** | `scikit-learn` | Execution quality decision |
| **StandardScaler** | `scikit-learn` | Feature normalization |
| **MetaTrader 5 API** | `MetaTrader5` | Order execution via MT5 bridge |

---

## ML Model Artifacts

| Artifact | Path | Purpose |
|----------|------|---------|
| KNN model | `models/procryon/knn_spread_model.pkl` | Spread regime classifier |
| FNN model | `models/procryon/mlp_execution_model.pkl` | Execution decision model |
| Scaler (KNN) | `models/procryon/knn_scaler.pkl` | Feature normalization |
| Scaler (FNN) | `models/procryon/mlp_scaler.pkl` | Feature normalization |

Models are trained using `scripts/train_procryon_models.py`.

---

## MLflow Integration

- Experiment: `Procryon_Crypto_Execution`
- Logs: spread regime, execution decision, fill quality, slippage realized
- Enables: execution quality trending and model refresh triggers

---

## MT5 Bridge Integration

Procryon communicates with MT5 via a local FastAPI bridge:
- Bridge URL: `http://localhost:8002`
- MT5 API hosts MetaTrader 5 for FTMO (primary) and AXI (secondary) prop firm accounts

---

## FastAPI Routes (Control Center)

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/procryon/health` | MT5 bridge and model readiness |
| GET | `/procryon/status` | Current spread regime and execution state |
| POST | `/procryon/analyze` | Analyze spread and execution quality |
| POST | `/procryon/execute` | Submit order via MT5 |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `PROCRYON_ENABLE_TRADING` | `false` | Set `true` to enable live execution |
| `PROCRYON_TRADING_MODE` | `paper` | `paper` or `live` |
| `PROCRYON_EXECUTION_THRESHOLD` | `0.55` | FNN execution confidence threshold |
| `MT5_API_URL` | `http://localhost:8002` | MT5 bridge URL |
| `PROCRYON_MODEL_DIR` | `models/procryon` | Path to trained model artifacts |
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | MLflow server |

---

## Main Files

| File | Purpose |
|------|---------|
| `procryon_bot.py` | Core FastAPI app and strategy logic |
| `bentley-bot/config/bots/procryon.yml` | Bot profile and risk config |
| `bentley-bot/bots/procryon.py` | Legacy stub |
| `scripts/train_procryon_models.py` | KNN + FNN training script |
| `models/procryon/` | Trained model artifacts |

---

## Prop Firm Constraints

| Firm | Max Daily Loss | Max Drawdown | Notes |
|------|---------------|-------------|-------|
| FTMO | Varies by challenge | Varies | Primary broker |
| AXI | Varies by account | Varies | Fallback broker |

Ensure `max_daily_loss_pct: 1.0` stays within prop firm evaluation limits at all times.
