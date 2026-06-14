"""
Financial ratio derivation module
Calculates technical and fundamental metrics from stored data
"""

import pandas as pd
from .db import get_mysql_engine, query_latest_prices, query_fundamentals


def calculate_moving_averages(ticker, periods=[20, 50, 200]):
    """
    Calculate moving averages for a ticker
    
    Args:
        ticker (str): Stock ticker symbol
        periods (list): List of periods for moving averages
    
    Returns:
        dict: Dictionary with MA values
    """
    engine = get_mysql_engine()
    
    # Get historical prices
    query = f"""
    SELECT date, close
    FROM stock_prices_yf
    WHERE ticker = '{ticker}'
    ORDER BY date DESC
    LIMIT 250
    """
    
    df = pd.read_sql(query, engine)
    
    if df.empty:
        return {}
    
    # Sort by date ascending for proper MA calculation
    df = df.sort_values('date')
    
    result = {
        'ticker': ticker,
        'latest_close': float(df['close'].iloc[-1]),
        'latest_date': df['date'].iloc[-1]
    }
    
    # Calculate MAs
    for period in periods:
        if len(df) >= period:
            ma = df['close'].rolling(window=period).mean().iloc[-1]
            result[f'MA_{period}'] = float(ma)
        else:
            result[f'MA_{period}'] = None
    
    print(f"✓ Calculated moving averages for {ticker}")
    return result


def calculate_pe_ratio(ticker):
    """
    Calculate Price-to-Earnings ratio
    
    Args:
        ticker (str): Stock ticker symbol
    
    Returns:
        float: P/E ratio or None
    """
    # Get latest price
    prices = query_latest_prices(ticker, days=1)
    if not prices:
        print(f"⚠ No price data for {ticker}")
        return None
    
    latest_price = prices[0]['close']
    
    # Get fundamentals (EPS)
    fundamentals = query_fundamentals(ticker)
    if not fundamentals or not fundamentals.get('eps'):
        print(f"⚠ No fundamental data for {ticker}")
        return None
    
    eps = fundamentals['eps']
    
    if eps and eps > 0:
        pe_ratio = latest_price / eps
        print(f"✓ P/E ratio for {ticker}: {pe_ratio:.2f}")
        return pe_ratio
    else:
        print(f"⚠ Invalid EPS for {ticker}")
        return None


def calculate_daily_returns(ticker, days=30):
    """
    Calculate daily returns for a ticker
    
    Args:
        ticker (str): Stock ticker symbol
        days (int): Number of days to calculate returns for
    
    Returns:
        pd.DataFrame: DataFrame with date, close, and daily_return columns
    """
    engine = get_mysql_engine()
    
    query = f"""
    SELECT date, close
    FROM stock_prices_yf
    WHERE ticker = '{ticker}'
    ORDER BY date DESC
    LIMIT {days + 1}
    """
    
    df = pd.read_sql(query, engine)
    
    if df.empty or len(df) < 2:
        return pd.DataFrame()
    
    # Sort ascending for proper calculation
    df = df.sort_values('date')
    
    # Calculate daily returns
    df['daily_return'] = df['close'].pct_change() * 100
    
    # Remove first row (NaN)
    df = df.dropna()
    
    print(f"✓ Calculated {len(df)} daily returns for {ticker}")
    return df


def calculate_volatility(ticker, days=30):
    """
    Calculate price volatility (standard deviation of returns)
    
    Args:
        ticker (str): Stock ticker symbol
        days (int): Lookback period
    
    Returns:
        float: Volatility as percentage
    """
    df = calculate_daily_returns(ticker, days)
    
    if df.empty:
        return None
    
    volatility = df['daily_return'].std()
    print(f"✓ {days}-day volatility for {ticker}: {volatility:.2f}%")
    return volatility


def generate_ticker_summary(ticker):
    """
    Generate comprehensive summary for a ticker
    
    Args:
        ticker (str): Stock ticker symbol
    
    Returns:
        dict: Complete summary with price, MAs, returns, volatility
    """
    print(f"\n{'='*60}")
    print(f"Generating summary for {ticker}")
    print(f"{'='*60}\n")
    
    summary = {'ticker': ticker}
    
    # Moving averages
    ma_data = calculate_moving_averages(ticker)
    summary.update(ma_data)
    
    # Volatility
    vol_30 = calculate_volatility(ticker, days=30)
    summary['volatility_30d'] = vol_30
    
    # P/E ratio (if fundamentals available)
    try:
        pe = calculate_pe_ratio(ticker)
        summary['pe_ratio'] = pe
    except Exception as e:
        print(f"⚠ Could not calculate P/E: {e}")
        summary['pe_ratio'] = None
    
    return summary


if __name__ == "__main__":
    # Example: Generate summaries for quantum stocks
    tickers = ["RGTI", "QBTS", "IONQ", "SOUN"]
    
    summaries = []
    for ticker in tickers:
        try:
            summary = generate_ticker_summary(ticker)
            summaries.append(summary)
            print()
        except Exception as e:
            print(f"✗ Error processing {ticker}: {e}\n")
    
    # Display summaries
    if summaries:
        df = pd.DataFrame(summaries)
        print("\n" + "="*80)
        print("SUMMARY TABLE")
        print("="*80)
        print(df.to_string(index=False))
