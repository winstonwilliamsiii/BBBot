# Dogon Bot README

## Overview
Dogon Bot (`scripts/dogon_bot.py`) is an ETF allocation runtime that loads trained models and produces allocation signals.

Core capabilities:
- Fetches market data via Yahoo Finance with Alpaca fallback
- Builds technical feature vectors (returns, volatility, RSI)
- Runs inference using trained Dogon models
- Uses training metadata from Dogon model output directory

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
