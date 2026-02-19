# Rigel Forex Bot - ML Deployment Guide

Complete guide for training, deploying, and managing LSTM/XGBoost hybrid machine learning models for the Rigel Forex Bot.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Training Models](#training-models  )
3. [Model Deployment](#model-deployment)
4. [Python Bot Integration](#python-bot-integration)
5. [MT5 ML API Server](#mt5-ml-api-server)
6. [Performance Monitoring](#performance-monitoring)
7. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Hybrid ML Prediction System

The Rigel Bot uses a **dual-model ensemble** for forex signal prediction:

```
┌─────────────────────────────────────────────────────────────┐
│                  HYBRID ML PREDICTOR                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────┐        ┌────────────────────┐      │
│  │   LSTM Model       │        │  XGBoost Model     │      │
│  │                    │        │                    │      │
│  │ • Sequential       │        │ • Feature-driven   │      │
│  │ • 60-hour window   │        │ • 11 indicators    │      │
│  │ • Price patterns   │        │ • Classification   │      │
│  └─────────┬──────────┘        └─────────┬──────────┘      │
│            │                              │                 │
│            └──────────┬───────────────────┘                 │
│                       ▼                                     │
│            ┌─────────────────────┐                          │
│            │  Ensemble Logic     │                          │
│            │                     │                          │
│            │  • Model agreement  │                          │
│            │  • Confidence boost │                          │
│            │  • Signal output    │                          │
│            └─────────────────────┘                          │
│                       │                                     │
│                       ▼                                     │
│         "mean_revert" / "trend" / "neutral"                 │
│         Confidence: 50% - 95%                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Model Roles:**
- **LSTM**: Analyzes sequential price movements (last 60 hours) to identify patterns
- **XGBoost**: Classifies market state using 11 technical indicator features
- **Ensemble**: Combines predictions with agreement-based confidence boosting

---

## Training Models

### Prerequisites

Install ML dependencies:
```bash
pip install tensorflow xgboost scikit-learn joblib
```

Set Alpaca API credentials:
```bash
# Windows (PowerShell)
$env:ALPACA_API_KEY = "your_alpaca_key"
$env:ALPACA_API_SECRET = "your_alpaca_secret"

# Linux/Mac
export ALPACA_API_KEY="your_alpaca_key"
export ALPACA_API_SECRET="your_alpaca_secret"
```

### Train Single Pair

Train models for one forex pair (e.g., EUR/USD) using 1 year of hourly data:

```bash
python scripts/train_rigel_models.py --symbol EUR/USD --days 365
```

**Output:**
```
models/rigel/EURUSD_lstm_model.h5     # LSTM sequential model
models/rigel/EURUSD_xgb_model.pkl     # XGBoost classifier
models/rigel/EURUSD_scaler.pkl        # Price normalizer
```

### Train All Configured Pairs

Train models for all 7 forex pairs:

```bash
python scripts/train_rigel_models.py --all-pairs --days 365
```

This creates models for:
- EUR/USD, GBP/USD, USD/JPY, USD/CHF
- AUD/USD, NZD/USD, USD/CAD

**Training time:** ~10-15 minutes per pair (depends on hardware)

### Advanced Training Options

```bash
# Train with 6 months data and 100 LSTM epochs
python scripts/train_rigel_models.py \
  --symbol GBP/USD \
  --days 180 \
  --lstm-epochs 100 \
  --xgb-estimators 200
```

**Parameters:**
- `--days`: Historical data period (default: 365)
- `--lstm-epochs`: LSTM training epochs (default: 50, higher = longer training)
- `--xgb-estimators`: XGBoost tree count (default: 100)

---

## Model Deployment

### File Structure

After training, verify model files:

```
BentleyBudgetBot/
├── models/
│   └── rigel/
│       ├── EURUSD_lstm_model.h5       # 60-hour LSTM sequential
│       ├── EURUSD_xgb_model.pkl       # XGBoost 11-feature classifier
│       ├── EURUSD_scaler.pkl          # Min-max scaler for LSTM
│       ├── GBPUSD_lstm_model.h5
│       ├── GBPUSD_xgb_model.pkl
│       ├── GBPUSD_scaler.pkl
│       └── ... (other pairs)
├── scripts/
│   ├── rigel_forex_bot.py             # Main bot (loads models)
│   └── train_rigel_models.py          # Training script
└── docs/
    └── RIGEL_ML_DEPLOYMENT.md         # This guide
```

### Model Naming Convention

Models use **clean symbol names** (no slashes):
- EUR/USD → `EURUSD_*.{h5,pkl}`
- GBP/USD → `GBPUSD_*.{h5,pkl}`
- USD/JPY → `USDJPY_*.{h5,pkl}`

The bot automatically converts `EUR/USD` to `EURUSD` when loading models.

---

## Python Bot Integration

### Enable ML Predictions

Edit `config_env.py` or `.env`:

```python
# Basic config
ALPACA_API_KEY = "your_alpaca_key"
ALPACA_API_SECRET = "your_alpaca_secret"

# Enable ML predictions
ENABLE_ML = True
ML_MODELS_DIR = "models/rigel"
```

**Default behavior:**
- `ENABLE_ML=False`: Bot uses **only technical indicators** (EMA, RSI, Bollinger Bands)
- `ENABLE_ML=True`: Bot uses **technical indicators + ML hybrid predictions**

### Run Bot with ML

```bash
python scripts/rigel_forex_bot.py
```

**Console output with ML enabled:**
```
18:45:23 [INFO] ======================================================================
18:45:23 [INFO] STARTING RIGEL FOREX BOT
18:45:23 [INFO] ======================================================================
18:45:23 [INFO] ML Predictor enabled
18:45:23 [INFO] Loading LSTM model: models/rigel/EURUSD_lstm_model.h5
18:45:23 [INFO] Loading XGBoost model: models/rigel/EURUSD_xgb_model.pkl
18:45:23 [INFO] ML models loaded successfully for EUR/USD
18:45:25 [INFO] Account: test123456 | Portfolio: $10,000.00 | Cash: $5,000.00
18:45:25 [INFO] Risk Metrics: 0/3 positions | Liquidity: 50.0% | Available: $3,750.00
18:45:26 [INFO] EUR/USD: LSTM=mean_revert, XGBoost=mean_revert (confidence: 0.80)
18:45:26 [INFO] Signal generated: BUY EUR/USD @ 1.08005 (confidence: 0.85)
```

### ML Confidence Boosting

When **both models agree** on the signal, confidence increases:

| Scenario | LSTM | XGBoost | Ensemble | Confidence |
|----------|------|---------|----------|------------|
| Strong agreement | mean_revert | mean_revert | mean_revert | **0.80-0.95** |
| Partial agreement | mean_revert | neutral | mean_revert | **0.65-0.75** |
| Disagreement | mean_revert | trend | neutral | **0.50-0.60** |
| Both neutral | neutral | neutral | neutral | **0.50** |

Technical signals require **minimum 70% confidence** to execute.

---

## MT5 ML API Server

The MT5 Expert Advisor can call a **Python ML API** for predictions.

### Create ML API Server

Create `scripts/rigel_ml_api.py`:

```python
from flask import Flask, request, jsonify
from rigel_forex_bot import MLPredictor, ForexConfig
import logging

app = Flask(__name__)
config = ForexConfig()
predictor = MLPredictor(enabled=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    """
    ML prediction endpoint for MT5 EA
    
    Request JSON:
    {
      "symbol": "EUR/USD",
      "indicators": {
        "price": 1.08005,
        "ema_fast": 1.08100,
        "ema_slow": 1.08000,
        "rsi": 42.5,
        "bb_upper": 1.08500,
        "bb_middle": 1.08000,
        "bb_lower": 1.07500
      },
      "recent_prices": [1.0801, 1.0802, ..., 1.0805]
    }
    
    Response JSON:
    {
      "prediction": "mean_revert",
      "confidence": 0.85,
      "lstm": "mean_revert",
      "xgboost": "mean_revert"
    }
    """
    try:
        data = request.json
        symbol = data['symbol']
        indicators = data['indicators']
        recent_prices = data.get('recent_prices', [])
        
        # Get ML prediction
        prediction = predictor.predict(symbol, indicators, recent_prices)
        confidence = predictor.get_confidence(prediction)
        
        # Get individual model predictions for debugging
        lstm_signal = predictor._lstm_predict(symbol, recent_prices)
        xgb_signal = predictor._xgb_predict(symbol, indicators)
        
        logger.info(f"Prediction for {symbol}: {prediction} (conf: {confidence:.2f})")
        
        return jsonify({
            'prediction': prediction.value,
            'confidence': confidence,
            'lstm': lstm_signal,
            'xgboost': xgb_signal,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'ml_enabled': predictor.enabled})

if __name__ == '__main__':
    logger.info("Starting Rigel ML API Server on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000)
```

### Run ML API Server

```bash
pip install flask
python scripts/rigel_ml_api.py
```

**Output:**
```
Starting Rigel ML API Server on http://0.0.0.0:5000
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.100:5000
```

### MT5 EA Integration

Update `mt5/RigelForexEA.mq5` WebRequest section:

```cpp
//+------------------------------------------------------------------+
//| Get ML prediction from Python API                                |
//+------------------------------------------------------------------+
string GetMLPrediction(string symbol, double price, double ema_fast, 
                       double ema_slow, double rsi, double bb_upper,
                       double bb_middle, double bb_lower)
{
   string api_url = "http://localhost:5000/predict";
   string headers = "Content-Type: application/json\r\n";
   
   // Build JSON request
   string json_request = StringFormat(
      "{\"symbol\":\"%s\",\"indicators\":{\"price\":%.5f,\"ema_fast\":%.5f,"
      "\"ema_slow\":%.5f,\"rsi\":%.2f,\"bb_upper\":%.5f,\"bb_middle\":%.5f,"
      "\"bb_lower\":%.5f}}",
      symbol, price, ema_fast, ema_slow, rsi, bb_upper, bb_middle, bb_lower
   );
   
   // Send HTTP POST request
   char post_data[];
   char result_data[];
   string result_headers;
   
   StringToCharArray(json_request, post_data, 0, StringLen(json_request));
   
   int timeout = 5000; // 5 seconds
   int res = WebRequest(
      "POST",
      api_url,
      headers,
      timeout,
      post_data,
      result_data,
      result_headers
   );
   
   if(res == -1)
   {
      Print("WebRequest error: ", GetLastError());
      return "neutral"; // Fallback to neutral
   }
   
   // Parse JSON response
   string response = CharArrayToString(result_data);
   
   // Extract prediction field (simple parsing)
   int start = StringFind(response, "\"prediction\":\"") + 14;
   int end = StringFind(response, "\"", start);
   string prediction = StringSubstr(response, start, end - start);
   
   Print("ML Prediction for ", symbol, ": ", prediction);
   return prediction;
}
```

**Enable WebRequest in MT5:**
1. Tools → Options → Expert Advisors
2. Check "Allow WebRequest for listed URL:"
3. Add: `http://localhost:5000`

---

## Performance Monitoring

### Compare ML vs Non-ML Performance

Run bot in **A/B test mode** to compare:

```bash
# Terminal 1: Non-ML bot
ENABLE_ML=False python scripts/rigel_forex_bot.py

# Terminal 2: ML-enabled bot
ENABLE_ML=True python scripts/rigel_forex_bot.py
```

**Track metrics:**
- Win rate: % of profitable trades
- Average profit per trade
- Sharpe ratio
- Maximum drawdown

### Model Retraining Schedule

Retrain models periodically to adapt to market changes:

- **Weekly**: Retrain with last 30 days data for fast adaptation
- **Monthly**: Retrain with last 180 days for medium-term patterns
- **Quarterly**: Retrain with last 365 days for long-term stability

```bash
# Weekly fast retrain
python scripts/train_rigel_models.py --all-pairs --days 30 --lstm-epochs 25

# Monthly retrain
python scripts/train_rigel_models.py --all-pairs --days 180 --lstm-epochs 50

# Quarterly full retrain
python scripts/train_rigel_models.py --all-pairs --days 365 --lstm-epochs 100
```

### Backtesting with ML

Backtest ML predictions on historical data:

```python
from scripts.rigel_forex_bot import RigelForexBot, ForexConfig
from scripts.train_rigel_models import RigelModelTrainer

# Initialize
config = ForexConfig()
trainer = RigelModelTrainer(api_key, api_secret)

# Fetch test data (1 month)
test_df = trainer.fetch_training_data("EUR/USD", days=30)
test_df = trainer.prepare_features(test_df)

# Run backtest
bot = RigelForexBot(config)
signals = []

for i in range(100, len(test_df)):
    indicators = {
        'price': test_df.iloc[i]['close'],
        'ema_fast': test_df.iloc[i]['ema_fast'],
        'ema_slow': test_df.iloc[i]['ema_slow'],
        'rsi': test_df.iloc[i]['rsi'],
        'bb_upper': test_df.iloc[i]['bb_upper'],
        'bb_middle': test_df.iloc[i]['bb_middle'],
        'bb_lower': test_df.iloc[i]['bb_lower']
    }
    
    recent_prices = test_df['close'].iloc[i-100:i].tolist()
    
    signal = bot.strategy generate_signal("EUR/USD", indicators, risk_metrics, recent_prices)
    if signal:
        signals.append(signal)

print(f"Backtest generated {len(signals)} signals")
```

---

## Troubleshooting

### Models Not Loading

**Error:**
```
WARNING: LSTM model not found: models/rigel/EURUSD_lstm_model.h5
WARNING: Using technical indicators only
```

**Solution:**
1. Train models: `python scripts/train_rigel_models.py --symbol EUR/USD`
2. Verify files exist: `ls models/rigel/`
3. Check ML dependencies: `pip install tensorflow xgboost`

### Low ML Confidence

**Symptom:** ML predictions always return 50% confidence

**Causes:**
- Models not trained properly (insufficient data)
- Both models returning neutral
- Price history too short (need 60+ bars)

**Solution:**
```bash
# Retrain with more data and epochs
python scripts/train_rigel_models.py \
  --symbol EUR/USD \
  --days 730 \
  --lstm-epochs 100 \
  --xgb-estimators 200
```

### MT5 WebRequest Fails

**Error in MT5 Experts log:**
```
WebRequest error: 4060 (Function not allowed)
```

**Solution:**
1. Tools → Options → Expert Advisors
2. Check "Allow WebRequest for listed URL"
3. Add exact URL: `http://localhost:5000`
4. Restart MT5

### TensorFlow/XGBoost Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'tensorflow'
```

**Solution:**
```bash
# Windows
pip install tensorflow xgboost scikit-learn

# Mac (M1/M2)
pip install tensorflow-macos tensorflow-metal xgboost scikit-learn

# Linux
pip install tensorflow xgboost scikit-learn
```

---

## Model Architecture Details

### LSTM Model Structure

```
Layer (type)                Output Shape              Param #
=================================================================
lstm_1 (LSTM)               (None, 60, 50)           10,400
dropout_1 (Dropout)         (None, 60, 50)           0
lstm_2 (LSTM)               (None, 50)               20,200
dropout_2 (Dropout)         (None, 50)               0
dense_1 (Dense)             (None, 25)               1,275
dense_2 (Dense)             (None, 3)                78
=================================================================
Total params: 31,953
```

**Input:** 60-hour price sequence (normalized)  
**Output:** 3 classes (neutral=0, mean_revert=1, trend=2)

### XGBoost Features

| Feature | Description | Example |
|---------|-------------|---------|
| `close` | Current price | 1.08005 |
| `ema_fast` | 20-period EMA | 1.08100 |
| `ema_slow` | 50-period EMA | 1.08000 |
| `rsi` | 14-period RSI | 42.5 |
| `bb_upper` | Upper Bollinger Band | 1.08500 |
| `bb_middle` | Middle Bollinger Band | 1.08000 |
| `bb_lower` | Lower Bollinger Band | 1.07500 |
| `price_to_ema_fast` | Price / EMA Fast | 0.99912 |
| `price_to_ema_slow` | Price / EMA Slow | 1.00005 |
| `ema_ratio` | EMA Fast / EMA Slow | 1.00093 |
| `bb_position` | (Price - BB Lower) / (BB Upper - BB Lower) | 0.505 |

---

## Next Steps

1. **Train initial models:**
   ```bash
   python scripts/train_rigel_models.py --all-pairs --days 365
   ```

2. **Enable ML in bot:**
   ```python
   # config_env.py
   ENABLE_ML = True
   ```

3. **Run bot with ML:**
   ```bash
   python scripts/rigel_forex_bot.py
   ```

4. **Monitor performance** and retrain monthly

5. **(Optional) Deploy ML API** for MT5 integration

---

**Questions or Issues?**

- Check [RIGEL_DEPLOYMENT_GUIDE.md](RIGEL_DEPLOYMENT_GUIDE.md) for general deployment
- Check [RIGEL_QUICK_START.md](RIGEL_QUICK_START.md) for basic setup
- Review bot logs for detailed error messages
- Ensure all dependencies installed: `pip install -r requirements-rigel.txt`
