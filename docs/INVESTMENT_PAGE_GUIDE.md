# Investment Analysis Page - MLFlow Integration Guide

## 🎉 What Was Created

### 1. **Fixed MLFlow Tracker** (`bbbot1_pipeline/mlflow_tracker.py`)
Your original file had several issues that have been corrected:

**Original Issues:**
- ❌ Mixing requirements (`mlflow>=2.4.1`) with code
- ❌ Incomplete function definitions
- ❌ Mixed Streamlit code with MLFlow logging
- ❌ No proper class structure
- ❌ Missing error handling

**✅ Fixes Applied:**
- ✅ Created proper `BentleyBotMLFlowTracker` class
- ✅ Separated concerns (logging vs UI)
- ✅ Added comprehensive error handling
- ✅ Implemented proper tracking URI configuration
- ✅ Added convenience functions for quick logging
- ✅ Included artifact logging (JSON files)
- ✅ Added methods to retrieve and query runs

### 2. **New Investment Analysis Page** (`pages/01_📈_Investment_Analysis.py`)
A complete Streamlit page with 4 interactive tabs:

#### Tab 1: 📊 Portfolio Overview
- Real-time portfolio data from yfinance
- Performance metrics (value, returns, volume)
- Interactive Plotly charts
- MLFlow logging of data ingestion operations
- Individual ticker performance table

#### Tab 2: 🔬 MLFlow Experiments
- View all logged experiments
- Filter by ticker
- Ratio analysis trends over time
- Interactive metric selection and plotting
- Run details with parameters and metrics

#### Tab 3: 📈 Technical Analysis
- Candlestick charts with moving averages (MA20, MA50, MA200)
- Volume analysis
- Interactive date range selection
- Professional trading visualization

#### Tab 4: 💰 Fundamental Ratios
- Live fundamental data from yfinance
- P/E, P/B, ROE, ROA, Debt/Equity ratios
- Automatic MLFlow logging of ratios
- Full company info JSON viewer

## 🚀 How to Use

### Access the Investment Page

1. **Navigate to the app**: http://localhost:8501
2. **Click "📈 Investment Analysis"** in the sidebar
   - Streamlit automatically creates navigation for files in `pages/` directory

### Using the Dashboard

#### Sidebar Controls
```
⚙️ Analysis Configuration
├── Select Tickers: Choose stocks to analyze
├── Analysis Period: Set date range
└── 🔬 Enable MLFlow Logging: Toggle experiment tracking
```

#### Portfolio Overview Tab
1. Select your tickers (default: IONQ, QBTS, SOUN, RGTI)
2. Adjust date range if needed
3. Enable MLFlow logging to track the analysis
4. View:
   - Portfolio metrics (value, assets, volume, return)
   - Price performance chart
   - Individual ticker performance table

#### MLFlow Experiments Tab
1. View all logged experiments in a table
2. Select a ticker for detailed ratio analysis
3. Choose a metric to plot trends over time
4. Monitor data ingestion performance

#### Technical Analysis Tab
1. Select a ticker from dropdown
2. View candlestick chart with moving averages
3. Analyze volume patterns
4. Identify support/resistance levels

#### Fundamental Ratios Tab
1. Select a ticker
2. View key fundamental metrics
3. Enable logging to save to MLFlow
4. Expand "View All Available Data" for full company info

## 📊 MLFlow Integration Details

### What Gets Logged

**Portfolio Performance:**
```python
{
    "source": "yfinance",
    "tickers": ["IONQ", "QBTS", "SOUN", "RGTI"],
    "rows_fetched": 1000,
    "response_time_seconds": 2.5,
    "success": True
}
```

**Fundamental Ratios:**
```python
{
    "ticker": "IONQ",
    "report_date": "2024-12-02",
    "pe_ratio": 25.3,
    "price_to_book": 3.2,
    "roe": 0.18,
    "debt_to_equity": 0.45
}
```

### Viewing MLFlow UI (Optional)

If you want to view the full MLFlow UI:

```bash
# Navigate to MLFlow data directory
cd data/mlflow

# Start MLFlow UI
mlflow ui --port 5000

# Open in browser
# http://localhost:5000
```

## 🔧 Configuration

### Ticker Configuration
Edit `bbbot1_pipeline/tickers_config.yaml` to change default tickers:

```yaml
tickers:
  quantum:
    - IONQ
    - QBTS
    - SOUN
    - RGTI
  
  major_tech:
    - AMZN
    - MSFT
    - GOOGL
```

### MLFlow Storage
By default, experiments are stored in:
```
data/mlflow/
```

To use MySQL backend instead:
```python
tracker = get_tracker(
    tracking_uri="mysql+pymysql://root:root@localhost:3307/mlflow_db"
)
```

## 🎨 Features Showcase

### Interactive Charts
- **Plotly Integration**: All charts are interactive (zoom, pan, hover)
- **Candlestick Charts**: Professional trading visualization
- **Moving Averages**: MA20, MA50, MA200 overlaid on price
- **Volume Analysis**: Bar charts with hover details

### Real-Time Data
- **Live Market Data**: Direct integration with Yahoo Finance
- **Current Prices**: Fetches latest available prices
- **Fundamentals**: Real-time P/E, market cap, and ratios

### Experiment Tracking
- **Automatic Logging**: Optionally log every analysis
- **Run History**: View all past experiments
- **Metric Trends**: Plot how metrics change over time
- **Artifact Storage**: Save raw data as JSON files

## 🐛 Debugging Tips

### If MLFlow logging fails:
```python
# Check if tracker is initialized
from bbbot1_pipeline.mlflow_tracker import get_tracker
tracker = get_tracker()
print(tracker.experiment_name)
```

### If yfinance data is missing:
```python
# Test direct yfinance access
import yfinance as yf
ticker = yf.Ticker("IONQ")
print(ticker.info)
```

### If page doesn't appear:
- Restart Streamlit: `Ctrl+C` then re-run
- Check `pages/` directory exists
- Ensure filename starts with number: `01_📈_Investment_Analysis.py`

## 📈 Next Steps

### Enhance the Dashboard
1. Add more technical indicators (RSI, MACD, Bollinger Bands)
2. Implement portfolio optimization algorithms
3. Add alerts and notifications
4. Create custom watchlists
5. Integrate with Airflow for scheduled analysis

### Extend MLFlow Logging
1. Log model predictions
2. Track portfolio rebalancing decisions
3. Log backtesting results
4. Compare strategy performance

### Database Integration
1. Store historical data in MySQL
2. Use Snowflake for analytics
3. Sync with Airbyte for automated updates

## 🎉 Summary

**Before:**
- ❌ Broken MLFlow file with syntax errors
- ❌ No investment page in Streamlit
- ❌ No way to view logged experiments

**After:**
- ✅ Professional MLFlow tracker with full functionality
- ✅ Complete Investment Analysis page with 4 tabs
- ✅ Real-time market data integration
- ✅ Interactive Plotly visualizations
- ✅ Automatic experiment logging
- ✅ Working application running at http://localhost:8501

**Access Now:** Click "📈 Investment Analysis" in the Streamlit sidebar!
