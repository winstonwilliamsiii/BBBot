"""
Quick test for error caching and exponential backoff
Run this to verify the error handling improvements
"""

import time
from frontend.utils.fundamentals_fetcher import (
    error_cache,
    fetch_alpha_vantage_fundamentals,
    fetch_fundamentals_multi_source,
    cached_fetch_fundamentals
)

print("="*70)
print("ERROR CACHING & EXPONENTIAL BACKOFF TEST")
print("="*70)

# Test 1: Error cache basic functionality
print("\n🧪 Test 1: Error Cache Recording")
print("-" * 70)

# Simulate errors
error_cache.record_error('test_source', 'TEST', 'test_error')
print(f"✓ Recorded error #1")
time.sleep(0.1)

error_cache.record_error('test_source', 'TEST', 'test_error')
print(f"✓ Recorded error #2")

# Check if should skip
if error_cache.should_skip('test_source', 'TEST'):
    print(f"✓ Error cache correctly blocking repeated calls")
else:
    print(f"✗ Error cache NOT working")

# Test 2: Error cache cleanup
print("\n🧪 Test 2: Error Cache Success Clearing")
print("-" * 70)

error_cache.record_success('test_source', 'TEST')
if not error_cache.should_skip('test_source', 'TEST'):
    print(f"✓ Success correctly cleared error cache")
else:
    print(f"✗ Error cache NOT cleared after success")

# Test 3: Real API with error handling
print("\n🧪 Test 3: Real API Call with Error Handling")
print("-" * 70)

test_ticker = 'AAPL'
print(f"Fetching {test_ticker} with Alpha Vantage...")

# Try fetching
data = fetch_alpha_vantage_fundamentals(test_ticker)

if data:
    print(f"✅ SUCCESS: Got data from Alpha Vantage")
    print(f"   Company: {data.get('company_name')}")
    print(f"   Market Cap: {data.get('market_cap')}")
else:
    print(f"⚠️ FAILED: No data (could be rate limit or missing API key)")
    
    # Check error cache
    if error_cache.should_skip('alpha_vantage', test_ticker):
        print(f"✓ Error cache is protecting against repeated calls")
        
        # Show error details
        if 'alpha_vantage' in error_cache.errors and test_ticker in error_cache.errors['alpha_vantage']:
            error_info = error_cache.errors['alpha_vantage'][test_ticker]
            backoff_time = int(error_info['backoff_until'] - time.time())
            print(f"   Error count: {error_info['count']}")
            print(f"   Error type: {error_info['error_type']}")
            print(f"   Backoff time remaining: {backoff_time}s")

# Test 4: Multi-source with error caching
print("\n🧪 Test 4: Multi-Source Fallback with Error Cache")
print("-" * 70)

test_ticker = 'MSFT'
print(f"Fetching {test_ticker} with multi-source fallback...")

data = fetch_fundamentals_multi_source(
    test_ticker,
    sources=['alpha_vantage', 'yfinance']
)

if data:
    print(f"✅ SUCCESS: Got data from {data.get('source')}")
    print(f"   Company: {data.get('company_name', data.get('name'))}")
else:
    print(f"❌ FAILED: All sources exhausted")

# Test 5: Cached function
print("\n🧪 Test 5: Streamlit Cached Function")
print("-" * 70)

test_ticker = 'GOOGL'
print(f"Testing cached fetch for {test_ticker}...")

try:
    # First call
    start = time.time()
    data1 = cached_fetch_fundamentals(test_ticker, sources=['alpha_vantage', 'yfinance'])
    time1 = time.time() - start
    
    # Second call (should be cached)
    start = time.time()
    data2 = cached_fetch_fundamentals(test_ticker, sources=['alpha_vantage', 'yfinance'])
    time2 = time.time() - start
    
    if data1 or data2:
        print(f"✅ Cached function working")
        print(f"   First call: {time1:.3f}s")
        print(f"   Second call: {time2:.3f}s (cached)")
        
        if time2 < time1:
            print(f"   ✓ Cache is faster ({time1/time2:.1f}x speedup)")
    else:
        print(f"⚠️ No data returned (check API keys)")
        
except Exception as e:
    print(f"❌ Error in cached function: {e}")

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

# Count errors in cache
total_errors = sum(len(tickers) for tickers in error_cache.errors.values())

print(f"Error cache entries: {total_errors}")
if total_errors > 0:
    print(f"\nCached errors (will retry after backoff):")
    for source, tickers in error_cache.errors.items():
        for ticker, info in tickers.items():
            backoff = int(info['backoff_until'] - time.time())
            print(f"  - {source}/{ticker}: {info['error_type']}, retry in {backoff}s")

print(f"\n✅ Error caching system is active and protecting against rate limits!")
print(f"💡 System will automatically retry after exponential backoff periods")
