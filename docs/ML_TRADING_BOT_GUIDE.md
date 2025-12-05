# ML Trading Bot Setup Guide

## 🤖 Overview
Automated trading bot for **WeBull Equities & ETFs** using:
- **Mean Reversion Strategy**: Bollinger Bands + RSI signals
- **Random Forest Regression**: ML predictions with MACD/RSI features

## 📁 Project Structure

```
bbbot1_pipeline/
├── trading_strategies.py    # Core strategies (Mean Reversion + Random Forest)
└── broker_api.py             # WeBull API integration (existing)

airflow/dags/
└── ml_trading_bot_webull.py  # Automated trading DAG

pages/
└── 04_🤖_Trading_Bot.py       # Streamlit monitoring dashboard
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install scikit-learn yfinance sqlalchemy pymysql
```

### 2. Test Strategies Locally
```python
from bbbot1_pipeline.trading_strategies import StrategyComparison
import yfinance as yf

# Download test data
df = yf.download('AAPL', start='2023-01-01', end='2024-12-01')

# Compare strategies
comparison = StrategyComparison(initial_capital=10000)
results = comparison.compare_strategies(df, 'AAPL')
```

### 3. Setup MySQL Tables
```sql
-- Market data storage
CREATE TABLE market_data_latest (
    date DATE,
    ticker VARCHAR(10),
    Open FLOAT,
    High FLOAT,
    Low FLOAT,
    Close FLOAT,
    Volume BIGINT,
    PRIMARY KEY (date, ticker)
);

-- Trading signals
CREATE TABLE trading_signals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10),
    signal INT,  -- 1=BUY, -1=SELL, 0=HOLD
    price FLOAT,
    timestamp DATETIME,
    strategy VARCHAR(50)
);

-- Trades history
CREATE TABLE trades_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10),
    action VARCHAR(10),  -- BUY or SELL
    shares INT,
    price FLOAT,
    value FLOAT,
    timestamp DATETIME,
    status VARCHAR(20),  -- SIMULATED or EXECUTED
    order_id VARCHAR(50),
    strategy VARCHAR(50)
);

-- Performance metrics
CREATE TABLE performance_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE,
    total_trades INT,
    buy_trades INT,
    sell_trades INT,
    total_value FLOAT,
    strategy VARCHAR(50)
);

-- Bot status
CREATE TABLE bot_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    status VARCHAR(20),
    strategy VARCHAR(50),
    timestamp DATETIME
);

-- Daily reports
CREATE TABLE daily_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATETIME,
    report TEXT,
    signals_count INT,
    strategy VARCHAR(50)
);
```

### 4. Configure WeBull API
Edit `bbbot1_pipeline/broker_api.py` with your WeBull credentials:
```python
# Ensure WebullClient is properly configured
webull = WebullClient()
webull.login(username="your_username", password="your_password")
```

### 5. Deploy Airflow DAG
```bash
# Copy DAG to Airflow
cp airflow/dags/ml_trading_bot_webull.py $AIRFLOW_HOME/dags/

# Enable DAG in Airflow UI
# Schedule: Runs at 9 AM and 3 PM on weekdays (market hours)
```

### 6. Launch Streamlit Dashboard
```bash
streamlit run streamlit_app.py
# Navigate to "🤖 Trading Bot" page
```

## ⚙️ Configuration

Edit `TRADING_CONFIG` in `ml_trading_bot_webull.py`:

```python
TRADING_CONFIG = {
    'tickers': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'SPY'],  # Your watchlist
    'initial_capital': 10000,
    'position_size': 0.2,       # 20% per position
    'max_daily_trades': 5,
    'stop_loss_pct': 0.02,      # 2% stop loss
    'take_profit_pct': 0.05,    # 5% take profit
    'strategy': 'mean_reversion',  # or 'random_forest'
    'simulation_mode': True     # Set False for live trading
}
```

## 📊 Strategy Details

### Mean Reversion Strategy
- **Entry Signal**: Price touches lower Bollinger Band + RSI < 30
- **Exit Signal**: Price touches upper Bollinger Band + RSI > 70
- **Parameters**: 
  - Bollinger Bands: 20-period, 2 std dev
  - RSI: 14-period

### Random Forest Regression
- **Features**: MACD, RSI, moving averages, lagged returns, volume
- **Prediction**: Next day return
- **Signal Generation**: 
  - BUY if predicted return > 0.1%
  - SELL if predicted return < -0.1%
- **Model**: 100 trees, max depth 10

## 🔄 DAG Workflow

```
1. Fetch Market Data (9 AM, 3 PM)
   ↓
2. Generate Trading Signals (Mean Reversion OR Random Forest)
   ↓
3. Execute Trades (Simulated or Live via WeBull)
   ↓
4. Calculate Performance Metrics
   ↓
5. Send Daily Report
```

## 📈 Monitoring Dashboard

Access via Streamlit: **pages/04_🤖_Trading_Bot.py**

Features:
- ✅ Real-time bot status (Active/Inactive)
- ✅ Daily trade metrics (Total, Buy, Sell, Volume)
- ✅ Strategy performance comparison
- ✅ Active trading signals (Buy/Sell)
- ✅ Trade history with CSV export
- ✅ Manual bot controls (Start/Stop)

## 🛡️ Safety Features

1. **Simulation Mode**: Test strategies without real money
2. **Position Sizing**: Max 20% per position (configurable)
3. **Stop Loss**: Automatic 2% stop loss
4. **Take Profit**: Automatic 5% take profit
5. **Daily Limits**: Max 5 trades per day
6. **MLFlow Tracking**: All experiments logged for analysis

## 🧪 Testing Your Strategies

```python
# Test Mean Reversion
from bbbot1_pipeline.trading_strategies import MeanReversionStrategy
import yfinance as yf

df = yf.download('AAPL', start='2023-01-01')
strategy = MeanReversionStrategy()
results = strategy.backtest(df, initial_capital=10000)

print(f"Total Return: {results['total_return']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")

# Test Random Forest
from bbbot1_pipeline.trading_strategies import RandomForestStrategy

rf_strategy = RandomForestStrategy()
train_results = rf_strategy.train(df)
backtest_results = rf_strategy.backtest(df)

print(f"R² Score: {train_results['r2']:.4f}")
print(f"Total Return: {backtest_results['total_return']:.2%}")
```

## 🔗 Integration with Existing Infrastructure

- **Airflow**: Orchestrates automated trading schedule
- **dbt**: Transforms market data into features
- **MLFlow**: Tracks strategy experiments and model performance
- **MySQL**: Stores trades, signals, and metrics
- **Streamlit**: Real-time monitoring and manual controls

## 📝 Next Steps

1. ✅ **Test in Simulation Mode**: Run for 1-2 weeks to validate strategies
2. ✅ **Review Performance**: Check Sharpe ratio, drawdown, win rate
3. ✅ **Optimize Parameters**: Tune Bollinger Bands, RSI thresholds
4. ✅ **Train Better Models**: Experiment with more features in Random Forest
5. ✅ **Enable Live Trading**: Set `simulation_mode: False` when ready
6. ✅ **Add Risk Management**: Implement portfolio-level stop losses
7. ✅ **Expand Universe**: Add more tickers to watchlist

## ⚠️ Important Notes

- **Paper Trading First**: Always test in simulation mode before live trading
- **Market Hours**: DAG runs at 9 AM and 3 PM EST (market open/close)
- **WeBull Only**: Bot currently supports WeBull equities/ETFs only
- **Capital Requirement**: Ensure sufficient buying power in WeBull account
- **API Limits**: Yahoo Finance may rate limit on high-frequency requests

## 🐛 Troubleshooting

### "Database connection failed"
```bash
# Check MySQL is running on port 3307
docker ps | grep mysql

# Verify credentials
echo $MYSQL_PASSWORD
```

### "WebullClient not available"
```bash
# Install WeBull dependencies
pip install webull

# Check broker_api.py has WebullClient class
```

### "No trading signals generated"
- Verify market data is fetched (check `market_data_latest` table)
- Ensure sufficient historical data (50+ bars minimum)
- Check strategy parameters (RSI/Bollinger thresholds)

### "Airflow DAG not running"
```bash
# Check DAG is in correct folder
ls $AIRFLOW_HOME/dags/ | grep ml_trading_bot

# Unpause DAG
airflow dags unpause ml_trading_bot_webull

# Trigger manually
airflow dags trigger ml_trading_bot_webull
```

## 📚 Resources

- [Mean Reversion Strategy Guide](https://www.investopedia.com/terms/m/meanreversion.asp)
- [Random Forest for Trading](https://towardsdatascience.com/random-forest-in-python)
- [WeBull API Documentation](https://github.com/tedchou12/webull)
- [Streamlit Documentation](https://docs.streamlit.io)

---

**Built for Bentley Budget Bot** 🤖  
*Automated trading with ML precision*
