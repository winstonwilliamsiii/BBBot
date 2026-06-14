"""
Quick test to verify all data sources work correctly
"""

import os
from frontend.utils.fundamentals_fetcher import (
    fetch_alpha_vantage_fundamentals,
    fetch_tiingo_fundamentals,
    fetch_yfinance_fundamentals,
    fetch_fundamentals_multi_source
)

print("="*70)
print("FUNDAMENTALS FETCH TEST - All Sources")
print("="*70)

test_ticker = 'AAPL'

# Test 1: Alpha Vantage
print(f"\n1️⃣ Testing Alpha Vantage for {test_ticker}")
print("-" * 70)
av_data = fetch_alpha_vantage_fundamentals(test_ticker)
if av_data:
    print(f"✅ SUCCESS")
    print(f"   Company: {av_data.get('company_name')}")
    print(f"   Market Cap: ${av_data.get('market_cap', 0):,.0f}")
    print(f"   PE Ratio: {av_data.get('pe_ratio')}")
    print(f"   Sector: {av_data.get('sector')}")
else:
    print(f"❌ FAILED - Check API key or rate limits")

# Test 2: Tiingo
print(f"\n2️⃣ Testing Tiingo for {test_ticker}")
print("-" * 70)
tiingo_data = fetch_tiingo_fundamentals(test_ticker)
if tiingo_data:
    print(f"✅ SUCCESS")
    print(f"   Company: {tiingo_data.get('company_name')}")
    print(f"   Exchange: {tiingo_data.get('exchange')}")
    print(f"   Has fundamentals: {'Yes' if tiingo_data.get('market_cap') else 'Limited (metadata only)'}")
    if tiingo_data.get('market_cap'):
        print(f"   Market Cap: ${tiingo_data.get('market_cap', 0):,.0f}")
        print(f"   PE Ratio: {tiingo_data.get('pe_ratio')}")
else:
    print(f"❌ FAILED - Check API key or subscription")

# Test 3: yfinance
print(f"\n3️⃣ Testing yfinance for {test_ticker}")
print("-" * 70)
yf_data = fetch_yfinance_fundamentals(test_ticker)
if yf_data:
    print(f"✅ SUCCESS")
    print(f"   Company: {yf_data.get('name')}")
    print(f"   Market Cap: ${yf_data.get('market_cap', 0):,.0f}")
    print(f"   PE Ratio: {yf_data.get('pe_ratio')}")
else:
    print(f"❌ FAILED - yfinance may not be installed")

# Test 4: Multi-source with priority
print(f"\n4️⃣ Testing Multi-Source (Alpha Vantage → yfinance)")
print("-" * 70)
multi_data = fetch_fundamentals_multi_source(test_ticker, sources=['alpha_vantage', 'yfinance'])
if multi_data:
    print(f"✅ SUCCESS from: {multi_data.get('source').upper()}")
    print(f"   Company: {multi_data.get('company_name', multi_data.get('name'))}")
else:
    print(f"❌ FAILED - All sources exhausted")

# Test 5: Auto mode (default priority)
print(f"\n5️⃣ Testing Auto Mode (default priority)")
print("-" * 70)
auto_data = fetch_fundamentals_multi_source(test_ticker)
if auto_data:
    print(f"✅ SUCCESS from: {auto_data.get('source').upper()}")
else:
    print(f"❌ FAILED")

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

sources_working = []
sources_failed = []

if av_data:
    sources_working.append("Alpha Vantage")
else:
    sources_failed.append("Alpha Vantage")

if tiingo_data:
    sources_working.append(f"Tiingo ({'Full' if tiingo_data.get('market_cap') else 'Metadata only'})")
else:
    sources_failed.append("Tiingo")

if yf_data:
    sources_working.append("yfinance")
else:
    sources_failed.append("yfinance")

print(f"\n✅ Working ({len(sources_working)}):")
for source in sources_working:
    print(f"   • {source}")

if sources_failed:
    print(f"\n❌ Failed ({len(sources_failed)}):")
    for source in sources_failed:
        print(f"   • {source}")

print(f"\n💡 Recommendation: Use 'Auto' mode for best reliability")
print(f"   Primary: {sources_working[0] if sources_working else 'None'}")
print(f"   Fallback: {sources_working[1:] if len(sources_working) > 1 else 'None'}")
