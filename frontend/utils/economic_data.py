"""
Economic Data Integration Module
==================================
Fetches real-time economic data from BLS, FRED, Census, and news APIs
Integrates with Bentley Chatbot for economic insights

APIs Used:
- BLS (Bureau of Labor Statistics) - Employment, inflation
- FRED (Federal Reserve Economic Data) - Macroeconomic indicators
- Census API - Population and demographic data
- NewsAPI (optional) - Economic news headlines
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import streamlit as st
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EconomicDataFetcher:
    """Fetches economic indicators from various US government APIs"""
    
    # Common BLS Series IDs
    BLS_SERIES = {
        'unemployment_rate': 'LNS14000000',           # Total unemployment rate (seasonally adjusted)
        'unemployment_uninsured': 'LNS13327709',      # Uninsured unemployment rate
        'civilian_employment': 'LNS12000000',         # Total employed
        'payroll_employment': 'PAYEMS',               # Nonfarm payroll employment (FRED series)
        'labor_force_participation': 'LNS11300000',   # Labor force participation rate
        'initial_jobless_claims': 'LNS13326394',      # Initial jobless claims
        'avg_hourly_earnings': 'CES0500000003',       # Average hourly earnings
        'inflation_cpi': 'CPIAUCSL',                  # Consumer Price Index (FRED)
        'producer_price': 'PPICMM',                   # Producer Price Index (FRED)
    }
    
    # Common FRED Series IDs
    FRED_SERIES = {
        'gdp': 'A191RL1Q225SBEA',                     # Real GDP (quarterly)
        'unrate': 'UNRATE',                           # Unemployment Rate
        'payems': 'PAYEMS',                           # Total Nonfarm Payroll
        'cpi': 'CPIAUCSL',                            # CPI for All Urban Consumers
        'pce': 'PCE',                                 # Personal Consumption Expenditures
        'retail_sales': 'RSXFS',                      # Retail Sales
        'industrial_production': 'INDPRO',            # Industrial Production Index
        'consumer_sentiment': 'UMCSENT',              # Consumer Sentiment Index
        'housing_starts': 'HOUST',                    # Housing Starts
        'mortgage_rate': 'MORTGAGE30US',              # 30-Year Mortgage Rate
    }
    
    def __init__(self):
        """Initialize with API credentials from environment"""
        self.bls_key = os.getenv('BLS_API_KEY', '')
        self.fred_key = os.getenv('FRED_API_KEY', '')
        self.census_key = os.getenv('CENSUS_API_KEY', '')
        self.newsapi_key = os.getenv('NEWSAPI_KEY', '')
        
        self.bls_url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
        self.fred_url = 'https://api.stlouisfed.org/fred/series/observations'
        self.census_url = 'https://api.census.gov/data/'
    
    @st.cache_data(ttl=3600)
    def get_unemployment_rate(self) -> Optional[Dict]:
        """
        Fetch current unemployment rate from BLS
        
        Returns:
            Dict with date, value, and recent trend
        """
        return self._fetch_bls_data(self.BLS_SERIES['unemployment_rate'], 'Unemployment Rate')
    
    @st.cache_data(ttl=3600)
    def get_employment_change(self) -> Optional[Dict]:
        """
        Fetch nonfarm payroll employment data from FRED
        Shows monthly change in jobs
        
        Returns:
            Dict with latest employment data
        """
        return self._fetch_fred_data(self.FRED_SERIES['payems'], 'Nonfarm Payroll Employment')
    
    @st.cache_data(ttl=3600)
    def get_inflation_cpi(self) -> Optional[Dict]:
        """
        Fetch Consumer Price Index (inflation) from FRED
        
        Returns:
            Dict with CPI and inflation rate
        """
        data = self._fetch_fred_data(self.FRED_SERIES['cpi'], 'CPI')
        if data:
            # Calculate YoY inflation rate if we have historical data
            if data.get('historical') and len(data['historical']) > 12:
                current = float(data['historical'][0].get('value', 0))
                year_ago = float(data['historical'][12].get('value', 0))
                if year_ago > 0:
                    inflation = ((current - year_ago) / year_ago) * 100
                    data['inflation_rate'] = round(inflation, 2)
        return data
    
    @st.cache_data(ttl=3600)
    def get_consumer_sentiment(self) -> Optional[Dict]:
        """
        Fetch University of Michigan Consumer Sentiment Index
        
        Returns:
            Dict with sentiment index
        """
        return self._fetch_fred_data(
            self.FRED_SERIES['consumer_sentiment'],
            'Consumer Sentiment Index'
        )
    
    @st.cache_data(ttl=3600)
    def get_housing_starts(self) -> Optional[Dict]:
        """
        Fetch housing starts data from FRED
        
        Returns:
            Dict with housing starts (thousands per month)
        """
        return self._fetch_fred_data(self.FRED_SERIES['housing_starts'], 'Housing Starts')
    
    @st.cache_data(ttl=3600)
    def get_economic_calendar(self) -> List[Dict]:
        """
        Get scheduled economic data releases for the next 7 days
        
        Note: For production, integrate with Investing.com or TradingView API
        This returns a curated list of major US economic releases
        
        Returns:
            List of upcoming releases
        """
        today = datetime.now().date()
        
        releases = [
            {
                'name': 'Initial Jobless Claims',
                'description': 'Weekly unemployment benefits claims',
                'agency': 'Department of Labor',
                'time': '08:30 AM ET',
                'release_date': today,
                'frequency': 'Weekly (Thursdays)',
                'importance': '🔴 High',
                'impact': 'Labor Market',
                'url': 'https://www.dol.gov/ui/data.pdf'
            },
            {
                'name': 'ISM Manufacturing PMI',
                'description': 'Manufacturing activity and sentiment',
                'agency': 'Institute for Supply Management',
                'time': '10:00 AM ET',
                'release_date': today + timedelta(days=1),
                'frequency': 'Monthly (first business day)',
                'importance': '🔴 High',
                'impact': 'Manufacturing',
                'url': 'https://www.ismworld.org/'
            },
            {
                'name': 'Employment Situation',
                'description': 'Jobs added, unemployment rate, wage growth',
                'agency': 'Bureau of Labor Statistics',
                'time': '08:30 AM ET',
                'release_date': today + timedelta(days=2),
                'frequency': 'Monthly (first Friday)',
                'importance': '🔴 Very High',
                'impact': 'Labor Market',
                'url': 'https://www.bls.gov/news.release/empsit.toc.htm'
            },
            {
                'name': 'Consumer Price Index (CPI)',
                'description': 'Inflation measure for consumer goods',
                'agency': 'Bureau of Labor Statistics',
                'time': '08:30 AM ET',
                'release_date': today + timedelta(days=3),
                'frequency': 'Monthly (second week)',
                'importance': '🔴 Very High',
                'impact': 'Inflation',
                'url': 'https://www.bls.gov/cpi/'
            },
            {
                'name': 'Producer Price Index (PPI)',
                'description': 'Inflation at producer/wholesale level',
                'agency': 'Bureau of Labor Statistics',
                'time': '08:30 AM ET',
                'release_date': today + timedelta(days=4),
                'frequency': 'Monthly (second week)',
                'importance': '🟠 Moderate',
                'impact': 'Inflation',
                'url': 'https://www.bls.gov/ppi/'
            },
            {
                'name': 'Retail Sales',
                'description': 'Consumer spending at retail establishments',
                'agency': 'Census Bureau',
                'time': '08:30 AM ET',
                'release_date': today + timedelta(days=5),
                'frequency': 'Monthly (mid-month)',
                'importance': '🔴 High',
                'impact': 'Consumer Spending',
                'url': 'https://www.census.gov/retail/index.html'
            },
            {
                'name': 'Housing Starts & Building Permits',
                'description': 'New residential construction activity',
                'agency': 'Census Bureau',
                'time': '08:30 AM ET',
                'release_date': today + timedelta(days=6),
                'frequency': 'Monthly (mid-month)',
                'importance': '🟠 Moderate',
                'impact': 'Housing Market',
                'url': 'https://www.census.gov/construction/nrc/index.html'
            },
        ]
        
        return releases
    
    def get_todays_releases(self) -> List[Dict]:
        """Get releases scheduled for today"""
        today = datetime.now().date()
        calendar = self.get_economic_calendar()
        return [r for r in calendar if r['release_date'] == today]
    
    @st.cache_data(ttl=3600)
    def get_economic_summary(self) -> str:
        """
        Generate a comprehensive economic summary for chatbot context
        
        Returns:
            Formatted markdown string with key economic indicators
        """
        summary_parts = []
        
        # Header
        summary_parts.append("📊 **Current Economic Conditions**\n")
        
        # Unemployment
        unemployment = self.get_unemployment_rate()
        if unemployment:
            summary_parts.append(
                f"• **Unemployment Rate**: {unemployment['value']}% "
                f"({unemployment['date']})"
            )
        
        # Inflation/CPI
        inflation = self.get_inflation_cpi()
        if inflation:
            cpi_val = inflation['value']
            inflation_rate = inflation.get('inflation_rate', 'N/A')
            summary_parts.append(
                f"• **Inflation (CPI)**: {cpi_val} | YoY: {inflation_rate}%"
            )
        
        # Consumer Sentiment
        sentiment = self.get_consumer_sentiment()
        if sentiment:
            summary_parts.append(
                f"• **Consumer Sentiment Index**: {sentiment['value']} "
                f"({sentiment['date']})"
            )
        
        # Housing
        housing = self.get_housing_starts()
        if housing:
            summary_parts.append(
                f"• **Housing Starts**: {housing['value']}k units/month"
            )
        
        # Today's releases
        todays = self.get_todays_releases()
        if todays:
            summary_parts.append("\n📅 **Today's Economic Releases**:")
            for release in todays:
                summary_parts.append(
                    f"  {release['importance']} **{release['name']}** @ {release['time']}"
                )
        
        return "\n".join(summary_parts) if len(summary_parts) > 1 else "No economic data available"
    
    def _fetch_bls_data(self, series_id: str, label: str) -> Optional[Dict]:
        """
        Generic BLS data fetcher
        
        Args:
            series_id: BLS series ID
            label: Human-readable label
        
        Returns:
            Dict with latest value and historical data
        """
        headers = {'Content-Type': 'application/json'}
        payload = {
            'seriesid': [series_id],
            'startyear': str(datetime.now().year - 1),
            'endyear': str(datetime.now().year),
            'registrationkey': self.bls_key,
            'calculations': True
        }
        
        try:
            response = requests.post(
                self.bls_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'REQUEST_SUCCEEDED':
                series = result['Results']['series'][0]
                data_points = series['data']
                
                if data_points:
                    latest = data_points[0]
                    return {
                        'series_id': series_id,
                        'label': label,
                        'date': f"{latest['year']}-{latest['period']}",
                        'value': float(latest['value']),
                        'historical': data_points[:12],
                        'source': 'BLS'
                    }
        except Exception as e:
            logger.warning(f"BLS fetch failed for {series_id}: {e}")
        
        return None
    
    def _fetch_fred_data(self, series_id: str, label: str) -> Optional[Dict]:
        """
        Generic FRED data fetcher
        
        Args:
            series_id: FRED series ID
            label: Human-readable label
        
        Returns:
            Dict with latest value and historical data
        """
        params = {
            'series_id': series_id,
            'api_key': self.fred_key,
            'sort_order': 'desc',
            'limit': 24,
            'file_type': 'json'
        }
        
        try:
            response = requests.get(
                self.fred_url,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if 'observations' in data and data['observations']:
                latest = data['observations'][0]
                
                return {
                    'series_id': series_id,
                    'label': label,
                    'date': latest['date'],
                    'value': latest.get('value', 'N/A'),
                    'historical': data['observations'][:24],
                    'source': 'FRED',
                    'url': f'https://fred.stlouisfed.org/series/{series_id}'
                }
        except Exception as e:
            logger.warning(f"FRED fetch failed for {series_id}: {e}")
        
        return None
    
    def get_economic_news(self, keywords: str = 'economy', limit: int = 5) -> Optional[List[Dict]]:
        """
        Fetch recent economic news headlines
        
        Args:
            keywords: Search keywords
            limit: Number of articles to return
        
        Returns:
            List of news articles or None if API not configured
        """
        if not self.newsapi_key:
            logger.warning("NewsAPI key not configured")
            return None
        
        url = 'https://newsapi.org/v2/everything'
        params = {
            'q': keywords,
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': limit,
            'apiKey': self.newsapi_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'ok':
                return data.get('articles', [])
        except Exception as e:
            logger.warning(f"NewsAPI fetch failed: {e}")
        
        return None
    
    def format_for_chatbot(self, include_calendar: bool = True) -> str:
        """
        Format economic data for chatbot display
        
        Args:
            include_calendar: Include upcoming releases calendar
        
        Returns:
            Formatted markdown string
        """
        output = self.get_economic_summary()
        
        if include_calendar:
            upcoming = self.get_economic_calendar()
            upcoming_week = [
                r for r in upcoming
                if datetime.now().date() <= r['release_date'] <= 
                datetime.now().date() + timedelta(days=7)
            ]
            
            if upcoming_week:
                output += "\n\n📋 **Next 7 Days of Releases**:\n"
                for release in upcoming_week[:5]:  # Show top 5
                    days_ahead = (release['release_date'] - datetime.now().date()).days
                    when = "Today" if days_ahead == 0 else f"in {days_ahead} days"
                    output += f"• {release['importance']} {release['name']} ({when})\n"
        
        return output


# Singleton cache function for use in Streamlit
@st.cache_resource
def get_economic_fetcher() -> EconomicDataFetcher:
    """
    Get cached instance of EconomicDataFetcher
    Use this in your Streamlit app to avoid recreating the fetcher
    
    Returns:
        EconomicDataFetcher instance
    """
    return EconomicDataFetcher()


# Helper functions for quick access
@st.cache_data(ttl=3600)
def get_unemployment_rate_quick() -> float:
    """Quick access to just the unemployment rate value"""
    fetcher = get_economic_fetcher()
    data = fetcher.get_unemployment_rate()
    return float(data['value']) if data else None


@st.cache_data(ttl=3600)
def get_inflation_rate_quick() -> float:
    """Quick access to YoY inflation rate"""
    fetcher = get_economic_fetcher()
    data = fetcher.get_inflation_cpi()
    return data.get('inflation_rate') if data else None


@st.cache_data(ttl=3600)
def get_todays_economic_calendar() -> List[Dict]:
    """Quick access to today's releases"""
    fetcher = get_economic_fetcher()
    return fetcher.get_todays_releases()
