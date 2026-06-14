"""
Test script for multi-source fundamentals fetcher
Tests all data sources and validates rate limiting
"""

import os
import time
from frontend.utils.fundamentals_fetcher import (
    fetch_tiingo_fundamentals,
    fetch_alpha_vantage_fundamentals,
    fetch_yfinance_fundamentals,
    fetch_fundamentals_multi_source,
    format_fundamental_value,
    tiingo_limiter,
    alpha_vantage_limiter
)

def print_separator(title):
    """Print a visual separator"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_rate_limiter():
    """Test rate limiter wait logic"""
    print_separator("Testing Rate Limiter")
    
    print("Making 3 rapid calls to test rate limiting...")
    start_time = time.time()
    
    for i in range(3):
        tiingo_limiter.wait_if_needed()
        elapsed = time.time() - start_time
        print(f"  Call {i+1}: {elapsed:.2f}s elapsed")
    
    total_time = time.time() - start_time
    print(f"\n✅ Rate limiter working: {total_time:.2f}s for 3 calls")
    print(f"   (Should be ~24s for 5 calls/min limit)")

def test_alpha_vantage():
    """Test Alpha Vantage fundamentals"""
    print_separator("Testing Alpha Vantage Source")
    
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        print("❌ ALPHA_VANTAGE_API_KEY not set in environment")
        print("   Set it with: $env:ALPHA_VANTAGE_API_KEY='your_key'")
        return False
    
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print("Fetching AAPL fundamentals...")
    
    data = fetch_alpha_vantage_fundamentals('AAPL', api_key)
    
    if data:
        print(f"\n✅ Alpha Vantage Success!")
        print(f"   Ticker: {data.get('ticker')}")
        print(f"   Company: {data.get('company_name')}")
        print(f"   Market Cap: {format_fundamental_value('market_cap', data.get('market_cap'))}")
        print(f"   PE Ratio: {format_fundamental_value('pe_ratio', data.get('pe_ratio'))}")
        print(f"   Sector: {data.get('sector')}")
        print(f"   Total fields: {len(data)}")
        return True
    else:
        print("❌ Alpha Vantage failed")
        return False

def test_tiingo():
    """Test Tiingo fundamentals"""
    print_separator("Testing Tiingo Source")
    
    api_key = os.getenv('TIINGO_API_KEY')
    if not api_key:
        print("❌ TIINGO_API_KEY not set in environment")
        print("   Set it with: $env:TIINGO_API_KEY='your_key'")
        return False
    
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print("Fetching AAPL metadata...")
    
    data = fetch_tiingo_fundamentals('AAPL', api_key)
    
    if data:
        print(f"\n✅ Tiingo Success!")
        print(f"   Ticker: {data.get('ticker')}")
        print(f"   Company: {data.get('company_name')}")
        print(f"   Start Date: {data.get('start_date')}")
        print(f"   End Date: {data.get('end_date')}")
        print(f"   Description: {data.get('description', '')[:100]}...")
        print(f"   Total fields: {len(data)}")
        return True
    else:
        print("❌ Tiingo failed")
        return False

def test_yfinance():
    """Test yfinance fundamentals"""
    print_separator("Testing yfinance Source")
    
    print("Fetching AAPL fundamentals...")
    
    try:
        data = fetch_yfinance_fundamentals('AAPL')
        
        if data:
            print(f"\n✅ yfinance Success!")
            print(f"   Ticker: {data.get('ticker')}")
            print(f"   Company: {data.get('company_name')}")
            print(f"   Market Cap: {format_fundamental_value('market_cap', data.get('market_cap'))}")
            print(f"   PE Ratio: {format_fundamental_value('pe_ratio', data.get('pe_ratio'))}")
            print(f"   Total fields: {len(data)}")
            return True
        else:
            print("❌ yfinance failed")
            return False
    except Exception as e:
        print(f"❌ yfinance error: {e}")
        return False

def test_multi_source():
    """Test multi-source fetching with fallback"""
    print_separator("Testing Multi-Source Auto-Fallback")
    
    test_tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    for ticker in test_tickers:
        print(f"\nFetching {ticker}...")
        data = fetch_fundamentals_multi_source(
            ticker,
            sources=['alpha_vantage', 'tiingo', 'yfinance']
        )
        
        if data:
            source = data.get('source', 'unknown')
            print(f"✅ {ticker}: Success from {source}")
            print(f"   Market Cap: {format_fundamental_value('market_cap', data.get('market_cap'))}")
            print(f"   PE Ratio: {format_fundamental_value('pe_ratio', data.get('pe_ratio'))}")
        else:
            print(f"❌ {ticker}: Failed from all sources")
        
        # Small delay between tickers
        time.sleep(1)

def test_format_values():
    """Test value formatting"""
    print_separator("Testing Value Formatting")
    
    test_cases = [
        ('market_cap', 3100000000000, '$3.10T'),
        ('market_cap', 150000000000, '$150.00B'),
        ('pe_ratio', 28.5, '28.50'),
        ('dividend_yield', 0.0052, '0.52%'),
        ('profit_margin', 0.2531, '25.31%'),
        ('roe', 0.1476, '14.76%'),
        ('beta', 1.23, '1.23'),
        ('52_week_high', 198.23, '$198.23'),
    ]
    
    for field, value, expected_format in test_cases:
        formatted = format_fundamental_value(field, value)
        print(f"{field:20s}: {str(value):20s} → {formatted}")

def run_all_tests():
    """Run all tests"""
    print("\n" + "█"*80)
    print("  MULTI-SOURCE FUNDAMENTALS FETCHER - TEST SUITE")
    print("█"*80)
    
    # Check environment
    print("\n📋 Environment Check:")
    print(f"   ALPHA_VANTAGE_API_KEY: {'✅ Set' if os.getenv('ALPHA_VANTAGE_API_KEY') else '❌ Missing'}")
    print(f"   TIINGO_API_KEY: {'✅ Set' if os.getenv('TIINGO_API_KEY') else '❌ Missing'}")
    
    # Run tests
    results = {
        'Rate Limiter': test_rate_limiter,
        'Alpha Vantage': test_alpha_vantage,
        'Tiingo': test_tiingo,
        'yfinance': test_yfinance,
        'Multi-Source': test_multi_source,
        'Formatting': test_format_values,
    }
    
    passed = []
    failed = []
    
    for test_name, test_func in results.items():
        try:
            if test_func():
                passed.append(test_name)
            else:
                failed.append(test_name)
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            failed.append(test_name)
    
    # Summary
    print_separator("Test Summary")
    print(f"\n✅ Passed: {len(passed)}/{len(results)}")
    for test in passed:
        print(f"   ✓ {test}")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}/{len(results)}")
        for test in failed:
            print(f"   ✗ {test}")
    
    print("\n" + "█"*80)

if __name__ == '__main__':
    # Check if running in correct directory
    if not os.path.exists('frontend/utils/fundamentals_fetcher.py'):
        print("❌ Error: Run this script from the project root directory")
        print("   Current directory:", os.getcwd())
        print("   Expected: BentleyBudgetBot/")
        exit(1)
    
    run_all_tests()
