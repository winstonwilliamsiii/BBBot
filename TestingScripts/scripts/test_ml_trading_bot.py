"""
Quick Test Script for ML Trading Bot
Tests both Mean Reversion and Random Forest strategies
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bbbot1_pipeline.trading_strategies import (
    MeanReversionStrategy,
    RandomForestStrategy,
    StrategyComparison
)
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def test_strategies():
    """Test both trading strategies with sample data"""
    
    print("="*70)
    print("ML TRADING BOT - STRATEGY TEST")
    print("="*70)
    
    # Test tickers
    tickers = ['AAPL', 'MSFT', 'SPY']
    
    # Download historical data
    print(f"\n📥 Downloading data for {', '.join(tickers)}...")
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    for ticker in tickers:
        try:
            print(f"\n{'='*70}")
            print(f"Testing {ticker}")
            print(f"{'='*70}")
            
            # Download data
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if df.empty:
                print(f"❌ No data for {ticker}")
                continue
            
            print(f"✅ Downloaded {len(df)} bars of data")
            
            # Test Mean Reversion
            print(f"\n📊 Testing Mean Reversion Strategy...")
            mr_strategy = MeanReversionStrategy()
            mr_results = mr_strategy.backtest(df, initial_capital=10000)
            
            print(f"   Total Return: {mr_results['total_return']:.2%}")
            print(f"   Sharpe Ratio: {mr_results['sharpe_ratio']:.3f}")
            print(f"   Final Value: ${mr_results['final_value']:,.2f}")
            
            # Count signals
            buy_signals = len(mr_results['signals'][mr_results['signals']['signal'] == 1])
            sell_signals = len(mr_results['signals'][mr_results['signals']['signal'] == -1])
            print(f"   Buy Signals: {buy_signals}")
            print(f"   Sell Signals: {sell_signals}")
            
            # Test Random Forest
            print(f"\n🤖 Testing Random Forest Strategy...")
            rf_strategy = RandomForestStrategy()
            
            # Train model
            train_results = rf_strategy.train(df)
            print(f"   R² Score: {train_results['r2']:.4f}")
            print(f"   MSE: {train_results['mse']:.6f}")
            
            # Top 3 features
            print(f"   Top 3 Features:")
            for i, row in train_results['feature_importance'].head(3).iterrows():
                print(f"      {row['feature']}: {row['importance']:.4f}")
            
            # Backtest
            rf_results = rf_strategy.backtest(df)
            print(f"   Total Return: {rf_results['total_return']:.2%}")
            print(f"   Sharpe Ratio: {rf_results['sharpe_ratio']:.3f}")
            print(f"   Final Value: ${rf_results['final_value']:,.2f}")
            
            # Count signals
            rf_buy_signals = len(rf_results['signals'][rf_results['signals']['signal'] == 1])
            rf_sell_signals = len(rf_results['signals'][rf_results['signals']['signal'] == -1])
            print(f"   Buy Signals: {rf_buy_signals}")
            print(f"   Sell Signals: {rf_sell_signals}")
            
            # Winner
            if mr_results['total_return'] > rf_results['total_return']:
                winner = "Mean Reversion"
                margin = mr_results['total_return'] - rf_results['total_return']
            else:
                winner = "Random Forest"
                margin = rf_results['total_return'] - mr_results['total_return']
            
            print(f"\n🏆 Winner for {ticker}: {winner} (+{margin:.2%})")
            
        except Exception as e:
            print(f"❌ Error testing {ticker}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print(f"{'='*70}\n")


def test_comparison_framework():
    """Test the StrategyComparison class"""
    
    print("\n" + "="*70)
    print("TESTING STRATEGY COMPARISON FRAMEWORK")
    print("="*70)
    
    # Download data for one ticker
    ticker = 'AAPL'
    print(f"\n📥 Downloading data for {ticker}...")
    
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    
    if df.empty:
        print(f"❌ No data for {ticker}")
        return
    
    print(f"✅ Downloaded {len(df)} bars")
    
    # Run comparison
    comparison = StrategyComparison(initial_capital=10000)
    results = comparison.compare_strategies(df, ticker)
    
    print("\n✅ Comparison framework test complete!")


if __name__ == "__main__":
    print("\n🤖 Bentley Budget Bot - ML Trading Strategy Test\n")
    
    # Test individual strategies
    test_strategies()
    
    # Test comparison framework
    test_comparison_framework()
    
    print("\n✅ All tests complete!")
    print("\nNext steps:")
    print("1. Review the results above")
    print("2. Setup MySQL tables: mysql -u root -p < mysql_config/ml_trading_bot_schema.sql")
    print("3. Deploy Airflow DAG: cp airflow/dags/ml_trading_bot_webull.py $AIRFLOW_HOME/dags/")
    print("4. Launch Streamlit: streamlit run streamlit_app.py")
    print("\nSee docs/ML_TRADING_BOT_GUIDE.md for full setup instructions\n")
