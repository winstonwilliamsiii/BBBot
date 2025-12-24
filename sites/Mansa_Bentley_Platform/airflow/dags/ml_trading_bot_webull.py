"""
ML Trading Bot DAG for WeBull Equities & ETFs
Runs automated trading with Mean Reversion vs Random Forest strategies
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from bbbot1_pipeline.trading_strategies import (
    MeanReversionStrategy,
    RandomForestStrategy,
    StrategyComparison
)

try:
    from bbbot1_pipeline.broker_api import WebullClient
    WEBULL_AVAILABLE = True
except ImportError:
    WEBULL_AVAILABLE = False
    print("⚠️ WebullClient not available - running in simulation mode")

import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine


# Configuration
TRADING_CONFIG = {
    'tickers': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'SPY'],  # Equities & ETF
    'initial_capital': 10000,
    'position_size': 0.2,  # 20% per position
    'max_daily_trades': 5,
    'stop_loss_pct': 0.02,  # 2% stop loss
    'take_profit_pct': 0.05,  # 5% take profit
    'strategy': 'mean_reversion',  # 'mean_reversion' or 'random_forest'
    'simulation_mode': not WEBULL_AVAILABLE
}

# MySQL connection
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3307,
    'user': 'root',
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': 'bentleybot'
}


def get_db_engine():
    """Create MySQL database engine"""
    connection_string = (
        f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@"
        f"{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
    )
    return create_engine(connection_string)


def fetch_market_data(**context):
    """Fetch latest market data for trading"""
    print(f"Fetching market data for {len(TRADING_CONFIG['tickers'])} tickers...")
    
    market_data = {}
    for ticker in TRADING_CONFIG['tickers']:
        try:
            # Fetch 6 months of data for training
            df = yf.download(
                ticker, 
                start=(datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'),
                end=datetime.now().strftime('%Y-%m-%d'),
                progress=False
            )
            
            if not df.empty:
                market_data[ticker] = df
                print(f"✅ {ticker}: {len(df)} bars fetched")
            else:
                print(f"⚠️ {ticker}: No data available")
        
        except Exception as e:
            print(f"❌ {ticker}: Error fetching data - {e}")
    
    # Store in XCom
    context['ti'].xcom_push(key='market_data_count', value=len(market_data))
    
    # Save to database
    engine = get_db_engine()
    for ticker, df in market_data.items():
        df['ticker'] = ticker
        df.to_sql(
            'market_data_latest',
            engine,
            if_exists='append',
            index=True,
            index_label='date'
        )
    
    return f"Fetched data for {len(market_data)} tickers"


def generate_trading_signals(**context):
    """Generate buy/sell signals using selected strategy"""
    strategy_name = TRADING_CONFIG['strategy']
    print(f"\nGenerating signals using {strategy_name} strategy...")
    
    # Load market data
    engine = get_db_engine()
    all_signals = []
    
    for ticker in TRADING_CONFIG['tickers']:
        try:
            # Load data from database
            query = f"""
                SELECT date, Open, High, Low, Close, Volume
                FROM market_data_latest
                WHERE ticker = '{ticker}'
                ORDER BY date DESC
                LIMIT 180
            """
            df = pd.read_sql(query, engine, parse_dates=['date'], index_col='date')
            df = df.sort_index()
            
            if len(df) < 50:
                print(f"⚠️ {ticker}: Insufficient data ({len(df)} bars)")
                continue
            
            # Initialize strategy
            if strategy_name == 'mean_reversion':
                strategy = MeanReversionStrategy()
                signals = strategy.generate_signals(df)
            
            elif strategy_name == 'random_forest':
                strategy = RandomForestStrategy()
                strategy.train(df)
                signals = strategy.generate_signals(df)
            
            else:
                raise ValueError(f"Unknown strategy: {strategy_name}")
            
            # Get latest signal
            latest_signal = signals.iloc[-1]
            
            if latest_signal['signal'] != 0:
                signal_data = {
                    'ticker': ticker,
                    'signal': int(latest_signal['signal']),
                    'price': float(latest_signal['price']),
                    'timestamp': datetime.now(),
                    'strategy': strategy_name
                }
                all_signals.append(signal_data)
                
                signal_type = "BUY" if latest_signal['signal'] == 1 else "SELL"
                print(f"📊 {ticker}: {signal_type} signal at ${latest_signal['price']:.2f}")
        
        except Exception as e:
            print(f"❌ {ticker}: Error generating signals - {e}")
    
    # Store signals in XCom
    context['ti'].xcom_push(key='trading_signals', value=all_signals)
    
    # Save to database
    if all_signals:
        signals_df = pd.DataFrame(all_signals)
        signals_df.to_sql(
            'trading_signals',
            engine,
            if_exists='append',
            index=False
        )
    
    return f"Generated {len(all_signals)} trading signals"


def execute_trades(**context):
    """Execute trades via WeBull API"""
    signals = context['ti'].xcom_pull(key='trading_signals', task_ids='generate_signals')
    
    if not signals:
        print("No trading signals to execute")
        return "No trades executed"
    
    print(f"\nExecuting {len(signals)} trades...")
    
    if TRADING_CONFIG['simulation_mode']:
        print("⚠️ Running in SIMULATION MODE - no actual trades")
        return _simulate_trades(signals, context)
    
    else:
        print("🔴 LIVE TRADING MODE - executing real trades")
        return _execute_live_trades(signals, context)


def _simulate_trades(signals, context):
    """Simulate trades without actual execution"""
    executed_trades = []
    
    for signal in signals:
        # Calculate position size
        position_value = TRADING_CONFIG['initial_capital'] * TRADING_CONFIG['position_size']
        shares = int(position_value / signal['price'])
        
        trade = {
            'ticker': signal['ticker'],
            'action': 'BUY' if signal['signal'] == 1 else 'SELL',
            'shares': shares,
            'price': signal['price'],
            'value': shares * signal['price'],
            'timestamp': datetime.now(),
            'status': 'SIMULATED',
            'strategy': signal['strategy']
        }
        
        executed_trades.append(trade)
        print(f"✅ SIMULATED: {trade['action']} {shares} shares of {signal['ticker']} at ${signal['price']:.2f}")
    
    # Save to database
    engine = get_db_engine()
    trades_df = pd.DataFrame(executed_trades)
    trades_df.to_sql('trades_history', engine, if_exists='append', index=False)
    
    return f"Simulated {len(executed_trades)} trades"


def _execute_live_trades(signals, context):
    """Execute real trades via WeBull API"""
    webull = WebullClient()
    
    # Check if logged in
    if not webull.is_logged_in():
        print("❌ Not logged into WeBull - aborting trades")
        return "Trade execution failed - not logged in"
    
    executed_trades = []
    
    for signal in signals:
        try:
            # Calculate position size
            account_value = webull.get_account_value()
            position_value = account_value * TRADING_CONFIG['position_size']
            shares = int(position_value / signal['price'])
            
            # Execute trade
            action = 'BUY' if signal['signal'] == 1 else 'SELL'
            
            order_result = webull.execute_trade(
                ticker=signal['ticker'],
                action=action,
                quantity=shares,
                order_type='MARKET'
            )
            
            if order_result['status'] == 'success':
                trade = {
                    'ticker': signal['ticker'],
                    'action': action,
                    'shares': shares,
                    'price': signal['price'],
                    'value': shares * signal['price'],
                    'timestamp': datetime.now(),
                    'status': 'EXECUTED',
                    'order_id': order_result.get('order_id'),
                    'strategy': signal['strategy']
                }
                
                executed_trades.append(trade)
                print(f"✅ EXECUTED: {action} {shares} shares of {signal['ticker']} at ${signal['price']:.2f}")
            
            else:
                print(f"❌ FAILED: {signal['ticker']} - {order_result.get('message')}")
        
        except Exception as e:
            print(f"❌ ERROR executing {signal['ticker']}: {e}")
    
    # Save to database
    if executed_trades:
        engine = get_db_engine()
        trades_df = pd.DataFrame(executed_trades)
        trades_df.to_sql('trades_history', engine, if_exists='append', index=False)
    
    return f"Executed {len(executed_trades)} real trades"


def calculate_performance(**context):
    """Calculate portfolio performance metrics"""
    print("\nCalculating portfolio performance...")
    
    engine = get_db_engine()
    
    # Load trades history
    query = """
        SELECT * FROM trades_history
        WHERE DATE(timestamp) = CURDATE()
        ORDER BY timestamp DESC
    """
    
    try:
        trades_df = pd.read_sql(query, engine)
        
        if trades_df.empty:
            print("No trades today")
            return "No performance to calculate"
        
        # Calculate metrics
        total_trades = len(trades_df)
        buy_trades = len(trades_df[trades_df['action'] == 'BUY'])
        sell_trades = len(trades_df[trades_df['action'] == 'SELL'])
        total_value = trades_df['value'].sum()
        
        performance = {
            'date': datetime.now().date(),
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'total_value': total_value,
            'strategy': TRADING_CONFIG['strategy']
        }
        
        # Save performance metrics
        perf_df = pd.DataFrame([performance])
        perf_df.to_sql('performance_metrics', engine, if_exists='append', index=False)
        
        print(f"📊 Performance Summary:")
        print(f"   Total Trades: {total_trades}")
        print(f"   Buy Orders: {buy_trades}")
        print(f"   Sell Orders: {sell_trades}")
        print(f"   Total Value: ${total_value:,.2f}")
        
        return f"Calculated performance for {total_trades} trades"
    
    except Exception as e:
        print(f"❌ Error calculating performance: {e}")
        return "Performance calculation failed"


def send_daily_report(**context):
    """Send daily trading report"""
    print("\n📧 Generating daily trading report...")
    
    # Get XCom data from previous tasks
    market_data_count = context['ti'].xcom_pull(key='market_data_count', task_ids='fetch_market_data')
    signals = context['ti'].xcom_pull(key='trading_signals', task_ids='generate_signals')
    
    report = f"""
    ╔═══════════════════════════════════════════════════════╗
    ║         BENTLEY BOT - DAILY TRADING REPORT           ║
    ╚═══════════════════════════════════════════════════════╝
    
    📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    🤖 Strategy: {TRADING_CONFIG['strategy'].replace('_', ' ').title()}
    🔴 Mode: {'SIMULATION' if TRADING_CONFIG['simulation_mode'] else 'LIVE TRADING'}
    
    📊 Market Data:
       - Tickers monitored: {len(TRADING_CONFIG['tickers'])}
       - Data fetched: {market_data_count} tickers
    
    📈 Trading Signals:
       - Total signals: {len(signals) if signals else 0}
       - Buy signals: {len([s for s in signals if s['signal'] == 1]) if signals else 0}
       - Sell signals: {len([s for s in signals if s['signal'] == -1]) if signals else 0}
    
    💰 Configuration:
       - Initial capital: ${TRADING_CONFIG['initial_capital']:,}
       - Position size: {TRADING_CONFIG['position_size'] * 100}%
       - Stop loss: {TRADING_CONFIG['stop_loss_pct'] * 100}%
       - Take profit: {TRADING_CONFIG['take_profit_pct'] * 100}%
    
    ═══════════════════════════════════════════════════════════
    """
    
    print(report)
    
    # TODO: Send via email or Slack webhook
    # For now, just log to database
    engine = get_db_engine()
    report_data = pd.DataFrame([{
        'date': datetime.now(),
        'report': report,
        'signals_count': len(signals) if signals else 0,
        'strategy': TRADING_CONFIG['strategy']
    }])
    report_data.to_sql('daily_reports', engine, if_exists='append', index=False)
    
    return "Daily report generated"


# DAG Definition
default_args = {
    'owner': 'bentleybot',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'ml_trading_bot_webull',
    default_args=default_args,
    description='Automated ML trading bot for WeBull equities & ETFs',
    schedule_interval='0 9,15 * * 1-5',  # 9 AM and 3 PM on weekdays (market hours)
    start_date=days_ago(1),
    catchup=False,
    tags=['trading', 'ml', 'webull', 'automated']
)

# Task definitions
fetch_data = PythonOperator(
    task_id='fetch_market_data',
    python_callable=fetch_market_data,
    dag=dag
)

generate_signals = PythonOperator(
    task_id='generate_signals',
    python_callable=generate_trading_signals,
    dag=dag
)

execute = PythonOperator(
    task_id='execute_trades',
    python_callable=execute_trades,
    dag=dag
)

calculate_perf = PythonOperator(
    task_id='calculate_performance',
    python_callable=calculate_performance,
    dag=dag
)

send_report = PythonOperator(
    task_id='send_daily_report',
    python_callable=send_daily_report,
    dag=dag
)

# Task dependencies
fetch_data >> generate_signals >> execute >> calculate_perf >> send_report
