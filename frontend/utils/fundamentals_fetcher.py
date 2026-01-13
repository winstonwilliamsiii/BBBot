"""
Multi-Source Fundamentals Fetcher
Fetches equity fundamentals with rate limiting and fallback sources
Supports: Tiingo (primary), Alpha Vantage (fallback), yfinance (backup)
"""

import os
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# API Keys
TIINGO_API_KEY = os.getenv('TIINGO_API_KEY')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Error tracking for exponential backoff
ERROR_CACHE = {}
ERROR_CACHE_TTL = 300  # Cache errors for 5 minutes
MAX_BACKOFF = 3600  # Max 1 hour backoff


class ErrorCache:
    """Track failed API calls to avoid repeated failures"""
    
    def __init__(self):
        self.errors = {}  # {source: {ticker: {timestamp, count, backoff_until}}}
    
    def should_skip(self, source: str, ticker: str) -> bool:
        """Check if we should skip this call due to recent errors"""
        if source not in self.errors:
            return False
        
        if ticker not in self.errors[source]:
            return False
        
        error_info = self.errors[source][ticker]
        backoff_until = error_info.get('backoff_until', 0)
        
        if time.time() < backoff_until:
            remaining = int(backoff_until - time.time())
            print(f"⏰ Skipping {source} for {ticker} - backing off for {remaining}s")
            return True
        
        return False
    
    def record_error(self, source: str, ticker: str, error_type: str = 'general'):
        """Record an error and calculate backoff time"""
        if source not in self.errors:
            self.errors[source] = {}
        
        if ticker not in self.errors[source]:
            self.errors[source][ticker] = {
                'timestamp': time.time(),
                'count': 1,
                'error_type': error_type,
                'backoff_until': time.time() + 60  # Start with 1 minute
            }
        else:
            error_info = self.errors[source][ticker]
            error_info['count'] += 1
            error_info['timestamp'] = time.time()
            error_info['error_type'] = error_type
            
            # Exponential backoff: 1min, 2min, 5min, 10min, 30min, 1hour
            backoff_times = [60, 120, 300, 600, 1800, 3600]
            backoff_index = min(error_info['count'] - 1, len(backoff_times) - 1)
            backoff_duration = backoff_times[backoff_index]
            
            error_info['backoff_until'] = time.time() + backoff_duration
            print(f"🔴 Error #{error_info['count']} for {source}/{ticker} - backing off {backoff_duration}s")
    
    def record_success(self, source: str, ticker: str):
        """Clear error history on successful call"""
        if source in self.errors and ticker in self.errors[source]:
            del self.errors[source][ticker]
    
    def cleanup_old_errors(self):
        """Remove errors older than TTL"""
        current_time = time.time()
        for source in list(self.errors.keys()):
            for ticker in list(self.errors[source].keys()):
                error_info = self.errors[source][ticker]
                if current_time - error_info['timestamp'] > ERROR_CACHE_TTL:
                    del self.errors[source][ticker]
            
            if not self.errors[source]:
                del self.errors[source]


# Global error cache instance
error_cache = ErrorCache()


# Rate limiting configuration
class RateLimiter:
    """Simple rate limiter to avoid API throttling"""
    
    def __init__(self, calls_per_minute: int = 5):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute  # seconds between calls
        self.last_call_time = {}
    
    def wait_if_needed(self, source: str):
        """Wait if necessary to respect rate limits"""
        if source in self.last_call_time:
            elapsed = time.time() - self.last_call_time[source]
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                time.sleep(wait_time)
        
        self.last_call_time[source] = time.time()


# Global rate limiter instances
tiingo_limiter = RateLimiter(calls_per_minute=5)  # Tiingo: conservative limit
alpha_vantage_limiter = RateLimiter(calls_per_minute=5)  # Alpha Vantage: 5 calls/min free tier


def fetch_tiingo_fundamentals(ticker: str) -> Optional[Dict]:
    """
    Fetch fundamentals from Tiingo API
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with fundamental data or None if failed
    """
    if not TIINGO_API_KEY or TIINGO_API_KEY == 'your_tiingo_api_key_here':
        return None
    
    # Check error cache - skip if backing off
    if error_cache.should_skip('tiingo', ticker):
        return None
    
    try:
        # Rate limiting
        tiingo_limiter.wait_if_needed('tiingo')
        
        url = f"https://api.tiingo.com/tiingo/daily/{ticker}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {TIINGO_API_KEY}"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        # Handle rate limiting
        if response.status_code == 429:
            print(f"🚫 Tiingo rate limited (429) for {ticker}")
            error_cache.record_error('tiingo', ticker, 'rate_limit_429')
            return None
        
        response.raise_for_status()
        data = response.json()
        
        # Try to fetch fundamentals from Tiingo's fundamentals endpoint (requires subscription)
        fundamentals_data = {}
        try:
            tiingo_limiter.wait_if_needed('tiingo')
            fund_url = f"https://api.tiingo.com/tiingo/fundamentals/{ticker}/statements"
            fund_response = requests.get(fund_url, headers=headers, timeout=10)
            
            if fund_response.status_code == 200:
                fund_json = fund_response.json()
                if fund_json and len(fund_json) > 0:
                    # Get most recent quarterly data
                    latest = fund_json[0] if isinstance(fund_json, list) else fund_json
                    
                    # Extract fundamentals if available
                    if 'statementData' in latest:
                        stmt_data = latest['statementData']
                        fundamentals_data = {
                            'market_cap': stmt_data.get('marketCap'),
                            'pe_ratio': stmt_data.get('pe'),
                            'pb_ratio': stmt_data.get('pb'),
                            'dividend_yield': stmt_data.get('dividendYield'),
                            'eps': stmt_data.get('eps'),
                            'roe': stmt_data.get('roe'),
                            'roa': stmt_data.get('roa'),
                            'revenue_ttm': stmt_data.get('revenue'),
                            'profit_margin': stmt_data.get('profitMargin'),
                        }
        except Exception as e:
            print(f"ℹ️ Tiingo fundamentals not available (may require subscription): {e}")
        
        # Record success to clear any previous errors
        error_cache.record_success('tiingo', ticker)
        
        # Combine metadata with fundamentals
        result = {
            'source': 'tiingo',
            'ticker': ticker,
            'company_name': data.get('name', 'N/A'),
            'name': data.get('name', 'N/A'),
            'exchange': data.get('exchangeCode', 'N/A'),
            'description': data.get('description', 'N/A'),
            'start_date': data.get('startDate', 'N/A'),
            'end_date': data.get('endDate', 'N/A'),
        }
        
        # Add fundamentals if available
        if fundamentals_data:
            result.update(fundamentals_data)
        
        return result
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print(f"🚫 Tiingo rate limit (429) for {ticker}")
            error_cache.record_error('tiingo', ticker, 'rate_limit_429')
        elif e.response.status_code == 403:
            print(f"🔒 Tiingo 403 Forbidden for {ticker} - API key may need activation or lacks permissions")
            error_cache.record_error('tiingo', ticker, 'forbidden_403')
        elif e.response.status_code == 401:
            print(f"🔑 Tiingo 401 Unauthorized for {ticker} - Check API key")
            error_cache.record_error('tiingo', ticker, 'unauthorized_401')
        else:
            print(f"❌ Tiingo HTTP error {e.response.status_code} for {ticker}")
            error_cache.record_error('tiingo', ticker, 'http_error')
        return None
    except requests.exceptions.RequestException as e:
        if "429" in str(e) or "Too Many Requests" in str(e):
            print(f"⚠️ Tiingo rate limit hit: {e}")
            error_cache.record_error('tiingo', ticker, 'rate_limit')
        else:
            print(f"❌ Tiingo request error for {ticker}: {e}")
            error_cache.record_error('tiingo', ticker, 'network_error')
        return None
    except Exception as e:
        print(f"❌ Tiingo unexpected error for {ticker}: {e}")
        error_cache.record_error('tiingo', ticker, 'unknown_error')
        return None


def fetch_alpha_vantage_fundamentals(ticker: str) -> Optional[Dict]:
    """
    Fetch fundamentals from Alpha Vantage API (comprehensive fundamentals)
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with fundamental data or None if failed
    """
    if not ALPHA_VANTAGE_API_KEY or ALPHA_VANTAGE_API_KEY == 'your_alpha_vantage_key_here':
        return None
    
    # Check error cache - skip if backing off
    if error_cache.should_skip('alpha_vantage', ticker):
        return None
    
    try:
        # Rate limiting
        alpha_vantage_limiter.wait_if_needed('alpha_vantage')
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "OVERVIEW",
            "symbol": ticker,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for rate limiting or errors
        if "Note" in data:
            error_msg = data.get('Note', 'Rate limited')
            print(f"⚠️ Alpha Vantage rate limited: {error_msg}")
            error_cache.record_error('alpha_vantage', ticker, 'rate_limit')
            return None
        
        if "Error Message" in data:
            print(f"❌ Alpha Vantage error for {ticker}: {data['Error Message']}")
            error_cache.record_error('alpha_vantage', ticker, 'api_error')
            return None
        
        if not data or "Symbol" not in data:
            print(f"⚠️ No Alpha Vantage data for {ticker}")
            error_cache.record_error('alpha_vantage', ticker, 'no_data')
            return None
        
        # Parse comprehensive fundamentals
        def safe_float(val):
            try:
                return float(val) if val and val != 'None' and val != '-' else None
            except (ValueError, TypeError):
                return None
        
        def safe_int(val):
            try:
                return int(float(val)) if val and val != 'None' and val != '-' else None
            except (ValueError, TypeError):
                return None
        
        return {
            'source': 'alpha_vantage',
            'name': data.get('Name', 'N/A'),
            'exchange': data.get('Exchange', 'N/A'),
            'sector': data.get('Sector', 'N/A'),
            'industry': data.get('Industry', 'N/A'),
            'market_cap': safe_int(data.get('MarketCapitalization')),
            'pe_ratio': safe_float(data.get('PERatio')),
            'forward_pe': safe_float(data.get('ForwardPE')),
            'peg_ratio': safe_float(data.get('PEGRatio')),
            'price_to_book': safe_float(data.get('PriceToBookRatio')),
            'price_to_sales': safe_float(data.get('PriceToSalesRatioTTM')),
            'dividend_yield': safe_float(data.get('DividendYield')),
            'eps': safe_float(data.get('EPS')),
            'revenue_ttm': safe_int(data.get('RevenueTTM')),
            'gross_profit_ttm': safe_int(data.get('GrossProfitTTM')),
            'profit_margin': safe_float(data.get('ProfitMargin')),
            'operating_margin': safe_float(data.get('OperatingMarginTTM')),
            'roe': safe_float(data.get('ReturnOnEquityTTM')),
            'roa': safe_float(data.get('ReturnOnAssetsTTM')),
            'revenue_per_share': safe_float(data.get('RevenuePerShareTTM')),
            'quarterly_earnings_growth': safe_float(data.get('QuarterlyEarningsGrowthYOY')),
            'quarterly_revenue_growth': safe_float(data.get('QuarterlyRevenueGrowthYOY')),
            'analyst_target_price': safe_float(data.get('AnalystTargetPrice')),
            '52_week_high': safe_float(data.get('52WeekHigh')),
            '52_week_low': safe_float(data.get('52WeekLow')),
            '50_day_ma': safe_float(data.get('50DayMovingAverage')),
            '200_day_ma': safe_float(data.get('200DayMovingAverage')),
            'beta': safe_float(data.get('Beta')),
            'shares_outstanding': safe_int(data.get('SharesOutstanding')),
            'book_value': safe_float(data.get('BookValue')),
            'ebitda': safe_int(data.get('EBITDA')),
            'ev_to_revenue': safe_float(data.get('EVToRevenue')),
            'ev_to_ebitda': safe_float(data.get('EVToEBITDA')),
        }
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print(f"🚫 Alpha Vantage rate limit (429) for {ticker}")
            error_cache.record_error('alpha_vantage', ticker, 'rate_limit_429')
        else:
            print(f"❌ Alpha Vantage HTTP error {e.response.status_code} for {ticker}")
            error_cache.record_error('alpha_vantage', ticker, 'http_error')
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Alpha Vantage request error for {ticker}: {e}")
        error_cache.record_error('alpha_vantage', ticker, 'network_error')
        return None
    except Exception as e:
        print(f"❌ Alpha Vantage unexpected error for {ticker}: {e}")
        error_cache.record_error('alpha_vantage', ticker, 'unknown_error')
        return None


def fetch_yfinance_fundamentals(ticker: str) -> Optional[Dict]:
    """
    Fetch fundamentals from yfinance (backup source)
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with fundamental data or None if failed
    """
    try:
        import yfinance as yf
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or len(info) < 5:
            return None
        
        return {
            'source': 'yfinance',
            'name': info.get('longName', info.get('shortName', 'N/A')),
            'exchange': info.get('exchange', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap'),
            'pe_ratio': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'peg_ratio': info.get('pegRatio'),
            'price_to_book': info.get('priceToBook'),
            'dividend_yield': info.get('dividendYield'),
            'eps': info.get('trailingEps'),
            'revenue_ttm': info.get('totalRevenue'),
            'profit_margin': info.get('profitMargins'),
            'roe': info.get('returnOnEquity'),
            'roa': info.get('returnOnAssets'),
            'beta': info.get('beta'),
            '52_week_high': info.get('fiftyTwoWeekHigh'),
            '52_week_low': info.get('fiftyTwoWeekLow'),
            '50_day_ma': info.get('fiftyDayAverage'),
            '200_day_ma': info.get('twoHundredDayAverage'),
        }
        
    except ImportError:
        print("⚠️ yfinance not installed")
        return None
    except Exception as e:
        print(f"❌ yfinance error for {ticker}: {e}")
        return None


def fetch_fundamentals_multi_source(
    ticker: str,
    sources: List[str] = ['alpha_vantage', 'tiingo', 'yfinance']
) -> Optional[Dict]:
    """
    Fetch fundamentals with automatic fallback across multiple sources
    
    Args:
        ticker: Stock ticker symbol
        sources: Ordered list of sources to try (default: alpha_vantage, tiingo, yfinance)
        
    Returns:
        Dictionary with fundamental data and source info
    """
    print(f"\n{'='*60}")
    print(f"Fetching fundamentals for {ticker}")
    print(f"Sources to try: {' -> '.join(sources)}")
    print(f"{'='*60}")
    
    for source in sources:
        print(f"\nTrying {source}...")
        
        data = None
        
        if source == 'tiingo':
            data = fetch_tiingo_fundamentals(ticker)
        elif source == 'alpha_vantage':
            data = fetch_alpha_vantage_fundamentals(ticker)
        elif source == 'yfinance':
            data = fetch_yfinance_fundamentals(ticker)
        
        if data:
            print(f"✅ Success! Data from {source}")
            return data
        else:
            print(f"⚠️ {source} failed, trying next source...")
    
    print(f"\n❌ All sources failed for {ticker}")
    return None


def format_fundamental_value(key: str, value) -> str:
    """Format fundamental value for display"""
    if value is None or value == 'N/A':
        return 'N/A'
    
    if isinstance(value, (int, float)):
        # Large numbers (market cap, revenue)
        if 'cap' in key.lower() or 'revenue' in key.lower() or 'ebitda' in key.lower():
            if value >= 1_000_000_000_000:
                return f"${value/1_000_000_000_000:.2f}T"
            elif value >= 1_000_000_000:
                return f"${value/1_000_000_000:.2f}B"
            elif value >= 1_000_000:
                return f"${value/1_000_000:.2f}M"
            else:
                return f"${value:,.0f}"
        
        # Percentages
        elif 'margin' in key.lower() or 'yield' in key.lower() or 'growth' in key.lower() or key.lower() in ['roe', 'roa']:
            return f"{value*100:.2f}%" if value < 1 else f"{value:.2f}%"
        
        # Ratios and small numbers
        elif 'ratio' in key.lower() or 'pe' in key.lower() or 'beta' in key.lower():
            return f"{value:.2f}"
        
        # Prices
        elif 'price' in key.lower() or 'ma' in key.lower() or 'eps' in key.lower():
            return f"${value:.2f}"
        
        # Default
        else:
            return f"{value:,.2f}"
    
    return str(value)


# Cache decorator for Streamlit with error handling
@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour, suppress spinner
def cached_fetch_fundamentals(ticker: str, sources: Optional[List[str]] = None) -> Optional[Dict]:
    """
    Cached version of fetch_fundamentals_multi_source with error handling
    
    Args:
        ticker: Stock ticker symbol
        sources: Optional list of sources to try in order
        
    Returns:
        Dictionary with fundamental data or None if all sources fail
    """
    # Cleanup old errors periodically
    error_cache.cleanup_old_errors()
    
    try:
        if sources:
            return fetch_fundamentals_multi_source(ticker, sources=sources)
        else:
            return fetch_fundamentals_multi_source(ticker)
    except Exception as e:
        print(f"❌ Cached fetch error for {ticker}: {e}")
        return None


if __name__ == "__main__":
    import sys
    
    # Test the multi-source fetcher
    test_tickers = ['AAPL', 'MSFT', 'IONQ', 'QBTS']
    
    print("="*70)
    print("MULTI-SOURCE FUNDAMENTALS FETCHER TEST")
    print("="*70)
    
    for ticker in test_tickers:
        data = fetch_fundamentals_multi_source(ticker)
        
        if data:
            print(f"\n{'='*60}")
            print(f"✅ {ticker} - Data from {data.get('source', 'unknown')}")
            print(f"{'='*60}")
            
            # Display key metrics
            key_metrics = [
                'name', 'exchange', 'sector', 'market_cap', 
                'pe_ratio', 'eps', 'dividend_yield'
            ]
            
            for key in key_metrics:
                if key in data:
                    formatted = format_fundamental_value(key, data[key])
                    print(f"  {key.replace('_', ' ').title()}: {formatted}")
        else:
            print(f"\n❌ {ticker} - No data available from any source")
        
        print()
