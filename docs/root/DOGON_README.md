# Dogon Bot README

## Overview
Dogon Bot (`scripts/dogon_bot.py`) is the **Mansa ETF fund** bot. It applies a two-model ML ensemble (XGBoost GBT + LSTM) to a universe of ETFs, generating allocation signals based on technical features computed from recent price history.

Core capabilities:
- Fetches market data via Yahoo Finance with Alpaca fallback
- Builds technical feature vectors (returns, volatility, RSI)
- Runs inference using trained Dogon models (XGBoost + LSTM)
- Uses training metadata from Dogon model output directory

---

## Strategy: ETF Allocation with XGBoost GBT + LSTM Ensemble

### Fund
Mansa ETF — Bot ID: ~10

### Signal Generation

For each ETF in the universe, Dogon computes a 5-feature vector from the past 90 days of daily OHLCV data:

| Feature | Computation |
|---------|-------------|
| `return_1d` | 1-day price return |
| `return_5d` | 5-day price return |
| `return_10d` | 10-day price return |
| `volatility_10d` | Rolling 10-day return standard deviation |
| `rsi_14` | Relative Strength Index (14-period) |

### Model 1: XGBoost GBT Classifier

- **Library**: `xgboost`
- **Type**: Gradient Boosted Trees classifier
- **Input**: 5-feature vector per symbol
- **Output**: Binary signal (1 = BUY, 0 = HOLD) + confidence score
- **Artifact**: `models/dogon/dogon_xgb_model.pkl`

### Model 2: LSTM Sequence Model

- **Library**: TensorFlow / Keras
- **Type**: Long Short-Term Memory recurrent neural network
- **Input**: Sequence window of feature vectors (sliding window over 90 days)
- **Output**: Signal probability
- **Artifact**: `models/dogon/dogon_lstm_model.h5` (or `.keras`)

### Ensemble Decision

Both models are run per symbol. The combined signal is:
```
final_signal = (xgb_confidence + lstm_confidence) / 2
if final_signal >= threshold → ALLOCATE to ETF
else → SKIP
```

Threshold is loaded from `models/dogon/dogon_training_summary.json`.

### ETF Universe

ETFs are configured in `bentley-bot/config/bots/dogon.yml`. Common inclusions include broad-market, sector, and factor ETFs.

---

## Main Files
- Runtime: `scripts/dogon_bot.py`
- Training: `scripts/train_dogon_models.py`
- Training deps: `requirements-dogon-training.txt`

## Prerequisites
Dogon runtime expects training artifacts at:
- `models/dogon/`

At minimum, runtime checks for:
- `models/dogon/dogon_training_summary.json`

If missing, run training first.

## Environment Variables
Common variables used by Dogon runtime/training:
- `ALPACA_API_KEY` or `APCA_API_KEY_ID`
- `ALPACA_SECRET_KEY` or `APCA_API_SECRET_KEY` or `ALPACA_API_SECRET`
- `ALPACA_DATA_URL` (default: `https://data.alpaca.markets`)
- `ALPACA_DATA_FEED` (default: `iex`)
- `MLFLOW_TRACKING_URI` (default: `http://localhost:5000`)
- `DOGON_MLFLOW_EXPERIMENT` (default: `Dogon-ETF-Models`)

## Run Dogon Runtime
From repo root:

```powershell
python scripts/dogon_bot.py
```

## Train Dogon Models
Recommended: use an isolated training environment.

```powershell
python -m venv .venv-dogon
.\.venv-dogon\Scripts\Activate.ps1
pip install -r requirements-dogon-training.txt
python scripts/train_dogon_models.py
```

After training, run the runtime again:

```powershell
python scripts/dogon_bot.py
```

## Notes On Isolation
This repo standard is to keep heavy ML training dependencies isolated from live runtime dependencies.

Use:
- Dedicated venv (for example `.venv-dogon`)
- `requirements-dogon-training.txt`

## Troubleshooting
- `Training summary missing`: run `scripts/train_dogon_models.py` first.
- `No data returned`: verify internet access and symbol availability.
- Alpaca fallback errors: verify API credentials and data URL/feed settings.
