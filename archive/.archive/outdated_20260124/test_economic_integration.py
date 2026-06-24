#!/usr/bin/env python3
"""
Test script for Economic Data Integration
Run this to verify BLS/FRED API configuration and test the module
"""

import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_api_keys():
    """Check if API keys are configured"""
    print_section("📋 API KEY CHECK")
    
    keys = {
        'BLS_API_KEY': 'Bureau of Labor Statistics',
        'FRED_API_KEY': 'Federal Reserve Economic Data',
        'CENSUS_API_KEY': 'Census Bureau (optional)',
        'NEWSAPI_KEY': 'NewsAPI (optional)'
    }
    
    configured = 0
    for key, name in keys.items():
        value = os.getenv(key, '')
        status = "✅ Configured" if value else "❌ Missing"
        print(f"  {status} - {name:40} ({key})")
        if value:
            configured += 1
    
    print(f"\n  Total: {configured}/{len(keys)} configured")
    return configured >= 2  # Need at least BLS and FRED

def check_module_import():
    """Check if economic_data module can be imported"""
    print_section("📦 MODULE IMPORT CHECK")
    
    try:
        from frontend.utils.economic_data import EconomicDataFetcher, get_economic_fetcher
        print("  ✅ Module imported successfully")
        print(f"     - EconomicDataFetcher class: OK")
        print(f"     - get_economic_fetcher function: OK")
        return True
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        print(f"     Make sure 'frontend/utils/economic_data.py' exists")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

def test_bls_connection():
    """Test connection to BLS API"""
    print_section("🔗 BLS API CONNECTION TEST")
    
    bls_key = os.getenv('BLS_API_KEY', '')
    if not bls_key:
        print("  ⏭️  Skipped - API key not configured")
        return None
    
    try:
        import requests
        from datetime import datetime
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            'seriesid': ['LNS14000000'],  # Unemployment rate
            'startyear': str(datetime.now().year - 1),
            'endyear': str(datetime.now().year),
            'registrationkey': bls_key
        }
        
        response = requests.post(
            'https://api.bls.gov/publicAPI/v2/timeseries/data/',
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'REQUEST_SUCCEEDED':
                latest = data['Results']['series'][0]['data'][0]
                unemployment = float(latest['value'])
                print(f"  ✅ Connection successful")
                print(f"     - Latest unemployment rate: {unemployment}%")
                print(f"     - Data from: {latest['year']}-{latest['period']}")
                return True
            else:
                print(f"  ❌ API error: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"  ❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return False

def test_fred_connection():
    """Test connection to FRED API"""
    print_section("🔗 FRED API CONNECTION TEST")
    
    fred_key = os.getenv('FRED_API_KEY', '')
    if not fred_key:
        print("  ⏭️  Skipped - API key not configured")
        return None
    
    try:
        import requests
        
        params = {
            'series_id': 'UNRATE',
            'api_key': fred_key,
            'sort_order': 'desc',
            'limit': 1,
            'file_type': 'json'
        }
        
        response = requests.get(
            'https://api.stlouisfed.org/fred/series/observations',
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'observations' in data and data['observations']:
                latest = data['observations'][0]
                print(f"  ✅ Connection successful")
                print(f"     - Latest unemployment rate: {latest['value']}%")
                print(f"     - Data from: {latest['date']}")
                return True
            else:
                print(f"  ❌ No data returned")
                return False
        else:
            print(f"  ❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return False

def test_economic_fetcher():
    """Test the EconomicDataFetcher class"""
    print_section("🧪 ECONOMIC DATA FETCHER TEST")
    
    try:
        from frontend.utils.economic_data import get_economic_fetcher
        
        fetcher = get_economic_fetcher()
        print("  ✅ Fetcher initialized")
        
        # Test unemployment rate
        print("\n  Testing unemployment rate fetch...")
        unemployment = fetcher.get_unemployment_rate()
        if unemployment:
            print(f"    ✅ Got data: {unemployment['value']}%")
        else:
            print(f"    ⚠️  No data (API may not be configured)")
        
        # Test inflation
        print("\n  Testing inflation fetch...")
        inflation = fetcher.get_inflation_cpi()
        if inflation:
            print(f"    ✅ Got data: {inflation['value']}")
        else:
            print(f"    ⚠️  No data (API may not be configured)")
        
        # Test calendar
        print("\n  Testing economic calendar...")
        calendar = fetcher.get_economic_calendar()
        if calendar:
            print(f"    ✅ Got {len(calendar)} releases")
            for release in calendar[:2]:
                print(f"       • {release['name']}")
        else:
            print(f"    ⚠️  No calendar data")
        
        # Test summary
        print("\n  Testing economic summary...")
        summary = fetcher.get_economic_summary()
        if summary and len(summary) > 0:
            print(f"    ✅ Generated summary ({len(summary)} chars)")
            lines = summary.split('\n')
            for line in lines[:3]:
                print(f"       {line}")
        else:
            print(f"    ⚠️  No summary generated")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chatbot_integration():
    """Test chatbot integration"""
    print_section("🤖 CHATBOT INTEGRATION TEST")
    
    try:
        from frontend.components.bentley_chatbot import BentleyChatBot
        
        chatbot = BentleyChatBot()
        print("  ✅ Chatbot initialized")
        
        # Test economic question
        test_questions = [
            "What's the unemployment rate?",
            "Is there economic data released today?",
            "Show me economic releases"
        ]
        
        for question in test_questions:
            print(f"\n  Testing: '{question}'")
            try:
                response = chatbot._fallback_response(question)
                if response and len(response) > 0:
                    print(f"    ✅ Got response ({len(response)} chars)")
                    # Show first line
                    first_line = response.split('\n')[0]
                    print(f"       {first_line[:60]}...")
                else:
                    print(f"    ⚠️  Empty response")
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "🚀 BENTLEY CHATBOT ECONOMIC DATA TEST" + " "*11 + "║")
    print("╚" + "="*58 + "╝")
    
    results = {
        'API Keys': check_api_keys(),
        'Module Import': check_module_import(),
        'BLS Connection': test_bls_connection(),
        'FRED Connection': test_fred_connection(),
        'Economic Fetcher': test_economic_fetcher(),
        'Chatbot Integration': test_chatbot_integration(),
    }
    
    # Print summary
    print_section("📊 TEST SUMMARY")
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test, result in results.items():
        if result is True:
            status = "✅ PASS"
            passed += 1
        elif result is False:
            status = "❌ FAIL"
            failed += 1
        else:
            status = "⏭️  SKIP"
            skipped += 1
        print(f"  {status:10} - {test}")
    
    print(f"\n  Total: {passed} passed, {failed} failed, {skipped} skipped")
    
    # Final recommendation
    print_section("✅ NEXT STEPS")
    
    if failed > 0:
        print(f"  Fix the {failed} failing test(s) above:")
        print("  1. Check API keys in .env file")
        print("  2. Verify internet connection")
        print("  3. Check that economic_data.py exists")
        print("  4. Review error messages above")
    else:
        print("  ✅ All tests passed!")
        print("  You can now use the chatbot with economic data:")
        print("    1. Run: streamlit run streamlit_app.py")
        print("    2. Ask: 'Is there economic data released today?'")
        print("    3. Get: Real BLS/FRED data in response!")
    
    print("\n")
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
