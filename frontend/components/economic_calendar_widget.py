"""
Economic Calendar & Stock IPO Widget
======================================
Displays today's economic events, releases, and upcoming IPOs

Features:
- Economic calendar with today's major releases
- Stock IPO information using yfinance
- Color-coded by importance
- Real-time updates
- Mansa Capital branding
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import yfinance as yf
import logging

logger = logging.getLogger(__name__)


class EconomicCalendarWidget:
    """Widget for displaying economic calendar and IPO data"""
    
    # Economic releases (curated list)
    MAJOR_RELEASES = [
        {
            'name': 'Initial Jobless Claims',
            'agency': 'Department of Labor',
            'time': '08:30 AM ET',
            'impact': 'High',
            'color': '#EF4444',  # Red
            'description': 'Weekly unemployment benefits claims',
            'schedule': 'Every Thursday',
            'category': 'Employment'
        },
        {
            'name': 'ISM Manufacturing PMI',
            'agency': 'Institute for Supply Management',
            'time': '10:00 AM ET',
            'impact': 'High',
            'color': '#F97316',  # Orange
            'description': 'Manufacturing activity index',
            'schedule': '1st business day of month',
            'category': 'Manufacturing'
        },
        {
            'name': 'Non-Farm Payroll',
            'agency': 'Bureau of Labor Statistics',
            'time': '08:30 AM ET',
            'impact': 'Very High',
            'color': '#DC2626',  # Dark Red
            'description': 'Jobs added, unemployment rate, wage growth',
            'schedule': 'First Friday of month',
            'category': 'Employment'
        },
        {
            'name': 'Consumer Price Index (CPI)',
            'agency': 'Bureau of Labor Statistics',
            'time': '08:30 AM ET',
            'impact': 'Very High',
            'color': '#DC2626',  # Dark Red
            'description': 'Inflation measure for consumer goods',
            'schedule': 'Mid-month',
            'category': 'Inflation'
        },
        {
            'name': 'Producer Price Index (PPI)',
            'agency': 'Bureau of Labor Statistics',
            'time': '08:30 AM ET',
            'impact': 'High',
            'color': '#F97316',  # Orange
            'description': 'Inflation at producer level',
            'schedule': 'Mid-month',
            'category': 'Inflation'
        },
        {
            'name': 'Retail Sales',
            'agency': 'Census Bureau',
            'time': '08:30 AM ET',
            'impact': 'High',
            'color': '#F97316',  # Orange
            'description': 'Consumer spending at retail',
            'schedule': 'Mid-month',
            'category': 'Consumer Spending'
        },
        {
            'name': 'Housing Starts & Permits',
            'agency': 'Census Bureau',
            'time': '08:30 AM ET',
            'impact': 'Moderate',
            'color': '#EABB00',  # Yellow/Gold
            'description': 'New residential construction activity',
            'schedule': 'Mid-month',
            'category': 'Housing'
        },
        {
            'name': 'Fed Interest Rate Decision',
            'agency': 'Federal Reserve',
            'time': '02:00 PM ET',
            'impact': 'Very High',
            'color': '#DC2626',  # Dark Red
            'description': 'FOMC meeting decision on rates',
            'schedule': 'Every 6 weeks',
            'category': 'Monetary Policy'
        },
        {
            'name': 'PCE Inflation Index',
            'agency': 'Bureau of Economic Analysis',
            'time': '08:30 AM ET',
            'impact': 'High',
            'color': '#F97316',  # Orange
            'description': 'Fed preferred inflation measure',
            'schedule': 'Monthly',
            'category': 'Inflation'
        },
        {
            'name': 'Durable Goods Orders',
            'agency': 'Census Bureau',
            'time': '08:30 AM ET',
            'impact': 'Moderate',
            'color': '#EABB00',  # Yellow/Gold
            'description': 'New orders for manufactured goods',
            'schedule': 'Monthly',
            'category': 'Manufacturing'
        },
    ]
    
    def __init__(self):
        """Initialize widget"""
        self.today = datetime.now().date()
    
    def get_todays_releases(_self) -> List[Dict]:
        """Get major economic releases for today"""
        # This would be enhanced with actual API calls
        # For now, return curated list with next occurrence
        return _self.MAJOR_RELEASES
    
    def get_upcoming_ipos(_self) -> List[Dict]:
        """
        Get upcoming IPO information
        Note: yfinance doesn't directly provide IPO data,
        so we provide a curated list and links to resources
        
        Returns:
            List of IPO information
        """
        ipos = [
            {
                'company': 'Coming Soon',
                'ticker': 'TBD',
                'expected_date': 'Check SEC EDGAR',
                'industry': 'Varies',
                'exchange': 'NYSE/NASDAQ',
                'info': 'IPO Calendar available at: https://www.nasdaq.com/market-activity/ipos'
            }
        ]
        
        try:
            # Try to get recent market events from yfinance
            import yfinance as yf
            # Get market summary for broader context
            market_info = yf.Ticker("^GSPC").info
            if market_info:
                return ipos
        except Exception as e:
            logger.warning(f"IPO fetch failed: {e}")
        
        return ipos
    
    def render_economic_calendar(self):
        """Render economic calendar widget"""
        st.markdown("""
        <style>
        .calendar-container {
            background: linear-gradient(135deg, #111827 0%, #0A0A0A 100%);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #14B8A6;
            margin: 1rem 0;
            box-shadow: 0 4px 12px rgba(20, 184, 166, 0.2);
        }
        .calendar-header {
            color: #FACC15;
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .release-item {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(20, 184, 166, 0.3);
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            transition: all 0.3s ease;
        }
        .release-item:hover {
            background: rgba(20, 184, 166, 0.1);
            border-color: #14B8A6;
            transform: translateX(5px);
        }
        .release-name {
            color: #FFFFFF;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .release-time {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
            margin-bottom: 4px;
        }
        .release-category {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 8px;
        }
        .impact-very-high {
            background-color: #DC2626;
            color: white;
        }
        .impact-high {
            background-color: #F97316;
            color: white;
        }
        .impact-moderate {
            background-color: #EABB00;
            color: #000;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div class="calendar-container">
            <div class="calendar-header">
                📅 Economic Calendar & Market Events
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Get releases
        releases = self.get_todays_releases()
        
        # Organize by impact
        very_high = [r for r in releases if r['impact'] == 'Very High']
        high = [r for r in releases if r['impact'] == 'High']
        moderate = [r for r in releases if r['impact'] == 'Moderate']
        
        # Create columns for impact levels
        st.markdown("### 🔴 Very High Impact (Moves Markets)")
        if very_high:
            for release in very_high:
                self._render_release_item(release)
        else:
            st.info("No very high impact releases today")
        
        st.markdown("### 🟠 High Impact")
        if high:
            for release in high:
                self._render_release_item(release)
        else:
            st.info("No high impact releases today")
        
        st.markdown("### 🟡 Moderate Impact")
        if moderate:
            for release in moderate:
                self._render_release_item(release)
        else:
            st.info("No moderate impact releases today")
    
    def _render_release_item(self, release: Dict):
        """Render a single release item"""
        impact_class = f"impact-{release['impact'].lower().replace(' ', '-')}"
        
        st.markdown(f"""
        <div class="release-item">
            <div class="release-name">{release['name']}</div>
            <div class="release-time">⏰ {release['time']}</div>
            <div>
                <span class="release-category {impact_class}">{release['impact']} Impact</span>
                <span class="release-category" style="background: rgba(20, 184, 166, 0.2); color: #14B8A6;">
                    {release['category']}
                </span>
            </div>
            <div style="color: rgba(255, 255, 255, 0.6); font-size: 0.85rem; margin-top: 8px;">
                {release['description']}<br>
                <strong>Agency:</strong> {release['agency']}<br>
                <strong>Schedule:</strong> {release['schedule']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_ipo_calendar(self):
        """Render IPO calendar widget"""
        st.markdown("""
        <style>
        .ipo-container {
            background: linear-gradient(135deg, #111827 0%, #0A0A0A 100%);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #06B6D4;
            margin: 1rem 0;
            box-shadow: 0 4px 12px rgba(6, 182, 212, 0.2);
        }
        .ipo-header {
            color: #FACC15;
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .ipo-item {
            background: rgba(6, 182, 212, 0.1);
            border: 1px solid rgba(6, 182, 212, 0.3);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        .ipo-company {
            color: #06B6D4;
            font-weight: 600;
            font-size: 1.1rem;
            margin-bottom: 8px;
        }
        .ipo-info {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
            line-height: 1.6;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="ipo-container">
            <div class="ipo-header">
                🚀 IPO Calendar & New Listings
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Create tabs for IPO info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="ipo-item">
                <div class="ipo-company">📊 Today's IPOs</div>
                <div class="ipo-info">
                    Check real-time IPO calendar for new listings on major exchanges.
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(
                "📈 NASDAQ IPO Calendar",
                "https://www.nasdaq.com/market-activity/ipos",
                use_container_width=True
            )
        
        with col2:
            st.markdown("""
            <div class="ipo-item">
                <div class="ipo-company">🏦 Upcoming IPOs</div>
                <div class="ipo-info">
                    Track companies planning IPOs in the next 90 days.
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(
                "📅 IPO Pipeline",
                "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=S-1",
                use_container_width=True
            )
        
        with col3:
            st.markdown("""
            <div class="ipo-item">
                <div class="ipo-company">🎯 Recent IPOs</div>
                <div class="ipo-info">
                    Performance of companies that went public recently.
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(
                "📈 Recent Listings",
                "https://finance.yahoo.com/",
                use_container_width=True
            )
    
    def render_market_summary(self):
        """Render market summary widget"""
        st.markdown("""
        <style>
        .market-summary {
            background: linear-gradient(135deg, #111827 0%, #0A0A0A 100%);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #10B981;
            margin: 1rem 0;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
        }
        .summary-header {
            color: #FACC15;
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        .market-card {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
        }
        .market-index {
            color: #10B981;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .market-value {
            color: #FFFFFF;
            font-size: 1.1rem;
            margin-bottom: 4px;
        }
        .market-change {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="market-summary">
            <div class="summary-header">📊 Market Indices (Live)</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Fetch market indices
        indices = {
            'S&P 500': '^GSPC',
            'Dow Jones': '^DJI',
            'Nasdaq': '^IXIC',
            'Russell 2000': '^RUT',
        }
        
        cols = st.columns(len(indices))
        
        for idx, (name, ticker) in enumerate(indices.items()):
            with cols[idx]:
                try:
                    # Use history() for more reliable real-time data
                    data = yf.Ticker(ticker)
                    hist = data.history(period='2d')  # Get last 2 days for comparison
                    
                    if not hist.empty and len(hist) >= 1:
                        current = hist['Close'].iloc[-1]
                        
                        # Get previous close for change calculation
                        if len(hist) >= 2:
                            prev_close = hist['Close'].iloc[-2]
                        else:
                            # Fallback to info if only one day available
                            info = data.info
                            prev_close = info.get('previousClose', current)
                        
                        if pd.notna(current) and pd.notna(prev_close) and prev_close > 0:
                            change = current - prev_close
                            change_pct = (change / prev_close * 100)
                            change_color = '#10B981' if change >= 0 else '#EF4444'
                            change_arrow = '📈' if change >= 0 else '📉'
                            
                            st.markdown(f"""
                            <div class="market-card">
                                <div class="market-index">{name}</div>
                                <div class="market-value">{current:,.2f}</div>
                                <div class="market-change" style="color: {change_color};">
                                    {change_arrow} {change:+.2f} ({change_pct:+.2f}%)
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info(f"{name}: Data unavailable")
                    else:
                        st.info(f"{name}: Data unavailable")
                except Exception as e:
                    logger.error(f"Error fetching {name} ({ticker}): {str(e)}")
                    st.info(f"{name}: Error fetching data")
    
    def render_full_dashboard(self):
        """Render complete economic calendar and IPO dashboard"""
        # Title
        st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h2 style='color: #FFFFFF; font-size: 2rem; margin-bottom: 0.5rem;'>
                📅 Economic Calendar & Market Events
            </h2>
            <p style='color: rgba(255,255,255,0.9); font-size: 0.95rem; margin-bottom: 0.3rem;'>
                Today's releases, upcoming IPOs, and market summary
            </p>
            <div style='background: linear-gradient(135deg, #0A0A0A 0%, #111827 100%); 
                        padding: 0.75rem 1.5rem; border-radius: 8px; margin: 1rem auto; 
                        max-width: 400px; border: 1px solid #FACC15; box-shadow: 0 2px 8px rgba(250, 204, 21, 0.2);'>
                <p style='color: #FACC15; font-size: 0.85rem; font-weight: 600; margin: 0; letter-spacing: 0.5px;'>
                    ⚡ Powered by Mansa Capital, LLC
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📅 Economic Calendar", "🚀 IPO Calendar", "📊 Market Summary"])
        
        with tab1:
            self.render_economic_calendar()
        
        with tab2:
            self.render_ipo_calendar()
        
        with tab3:
            self.render_market_summary()


# Helper function for easy use
@st.cache_resource
def get_calendar_widget() -> EconomicCalendarWidget:
    """Get or create economic calendar widget"""
    return EconomicCalendarWidget()


def render_todays_events():
    """Quick render of today's events for sidebar or header"""
    widget = get_calendar_widget()
    releases = widget.get_todays_releases()
    
    if releases:
        with st.expander("📅 Today's Economic Events", expanded=False):
            very_high = [r for r in releases if r['impact'] == 'Very High']
            if very_high:
                st.markdown("**🔴 Very High Impact:**")
                for r in very_high:
                    st.markdown(f"• {r['name']} @ {r['time']}")
            
            high = [r for r in releases if r['impact'] == 'High']
            if high:
                st.markdown("**🟠 High Impact:**")
                for r in high:
                    st.markdown(f"• {r['name']} @ {r['time']}")
