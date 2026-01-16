# 📅 Economic Calendar & IPO Widget Integration Guide

## Overview

Added a complete economic calendar and IPO widget to display:
- ✅ Today's economic releases with impact levels
- ✅ Economic event schedule and details
- ✅ IPO information and links to calendars
- ✅ Live market indices (S&P 500, Dow, Nasdaq, etc.)

---

## 🎯 What's New

### New File: `frontend/components/economic_calendar_widget.py`

A full-featured widget component with:

**Key Features:**
- 📅 Economic calendar (10 major releases)
- 🎨 Color-coded by impact level (Very High, High, Moderate)
- 🚀 IPO calendar links
- 📊 Live market indices
- ⚡ Mansa Capital branding
- 🔄 1-hour caching for performance

**Methods:**
```python
widget.render_economic_calendar()  # Economic releases
widget.render_ipo_calendar()       # IPO info
widget.render_market_summary()     # Live indices
widget.render_full_dashboard()     # All three combined
render_todays_events()             # Quick sidebar widget
```

---

## 🚀 How to Use

### Option 1: Full Dashboard on Homepage

Add to `streamlit_app.py`:

```python
from frontend.components.economic_calendar_widget import get_calendar_widget

# In your homepage section:
st.markdown("---")

widget = get_calendar_widget()
widget.render_full_dashboard()
```

**Result:** Complete 3-tab dashboard showing all economic data, IPOs, and market summary.

---

### Option 2: Quick Summary in Sidebar

Add to `streamlit_app.py` sidebar:

```python
from frontend.components.economic_calendar_widget import render_todays_events

with st.sidebar:
    render_todays_events()
```

**Result:** Collapsible sidebar showing today's very high and high impact releases.

---

### Option 3: Just Economic Calendar

```python
from frontend.components.economic_calendar_widget import get_calendar_widget

widget = get_calendar_widget()
widget.render_economic_calendar()
```

---

### Option 4: Just IPO Calendar

```python
from frontend.components.economic_calendar_widget import get_calendar_widget

widget = get_calendar_widget()
widget.render_ipo_calendar()
```

---

### Option 5: Just Market Summary

```python
from frontend.components.economic_calendar_widget import get_calendar_widget

widget = get_calendar_widget()
widget.render_market_summary()
```

---

## 📝 Integration Examples

### Add to Homepage Header

```python
# streamlit_app.py - in your homepage section

import streamlit as st
from frontend.components.economic_calendar_widget import get_calendar_widget

# Create two columns
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("## 📊 Bentley Dashboard")
    # ... your existing content
    
with col2:
    st.markdown("### 📅 Today's Events")
    from frontend.components.economic_calendar_widget import render_todays_events
    render_todays_events()
```

### Add as New Tab

```python
# If you have tabs in your app:

tab1, tab2, tab3, tab4 = st.tabs([
    "Dashboard", 
    "Portfolio", 
    "Budget",
    "📅 Calendar"  # NEW
])

with tab4:
    from frontend.components.economic_calendar_widget import get_calendar_widget
    widget = get_calendar_widget()
    widget.render_full_dashboard()
```

### Add to Existing "Markets" Page

```python
# If you have a markets or analytics page:

def show_markets_page():
    st.markdown("# 📈 Markets & Economics")
    
    # Your existing content...
    
    st.markdown("---")
    st.markdown("## 📅 Economic Calendar & IPOs")
    
    from frontend.components.economic_calendar_widget import get_calendar_widget
    widget = get_calendar_widget()
    widget.render_full_dashboard()
```

---

## 🎨 Features & Styling

### Impact Level Colors
- 🔴 **Very High Impact (Red #DC2626)** - Moves markets significantly
- 🟠 **High Impact (Orange #F97316)** - Important market movers
- 🟡 **Moderate Impact (Gold #EABB00)** - Notable but less volatile

### Layout
- **Economic Calendar:** Organized by impact level
- **IPO Calendar:** Links to NASDAQ, SEC EDGAR, recent listings
- **Market Summary:** Live indices with change percentages

### Styling
- ✅ Matches your dark theme (Mansa Capital colors)
- ✅ Teal accent (#14B8A6) for economic data
- ✅ Gold accent (#FACC15) for headers
- ✅ Hover effects and transitions
- ✅ Responsive columns

---

## 📊 Economic Releases Included

The widget displays data for these major releases:

| Release | Agency | Impact | Time |
|---------|--------|--------|------|
| Initial Jobless Claims | DOL | High | 08:30 AM ET |
| ISM Manufacturing PMI | ISM | High | 10:00 AM ET |
| Non-Farm Payroll | BLS | Very High | 08:30 AM ET |
| Consumer Price Index | BLS | Very High | 08:30 AM ET |
| Producer Price Index | BLS | High | 08:30 AM ET |
| Retail Sales | Census | High | 08:30 AM ET |
| Housing Starts & Permits | Census | Moderate | 08:30 AM ET |
| Fed Interest Rate | FED | Very High | 02:00 PM ET |
| PCE Inflation Index | BEA | High | 08:30 AM ET |
| Durable Goods Orders | Census | Moderate | 08:30 AM ET |

---

## 🔗 IPO Resources Linked

The widget provides quick links to:
- 📈 **NASDAQ IPO Calendar** - Real-time IPO listings
- 📅 **IPO Pipeline** - SEC EDGAR S-1 filings
- 📈 **Recent Listings** - Yahoo Finance recent IPOs

---

## 🚀 Adding to Your Streamlit App

### Step 1: Make sure imports work
```python
from frontend.components.economic_calendar_widget import get_calendar_widget
```

### Step 2: Choose your placement
- Homepage header
- Sidebar
- Dedicated tab
- Markets page
- Dashboard section

### Step 3: Add 3-4 lines of code
```python
widget = get_calendar_widget()
widget.render_full_dashboard()  # or any other render method
```

### Step 4: Test it!
```bash
streamlit run streamlit_app.py
```

---

## 💡 Use Cases

### 📱 Homepage Widget
Quick glance at today's economic events while browsing portfolio.

### 📊 Trading Dashboard
Show traders what economic events might affect markets today.

### 🎯 Alert System
Identify high-impact releases before they happen.

### 📈 Market Analysis
Show IPO pipeline for growth opportunities.

---

## 🔄 Performance

- **Caching:** 1-hour TTL (reduce API calls)
- **Load Time:** <1 second (cached)
- **API Calls:** ~1-2 per session
- **Memory:** Minimal (simple data structures)

---

## 🎯 Example Complete Integration

```python
# Add this to your streamlit_app.py

import streamlit as st
from frontend.components.economic_calendar_widget import get_calendar_widget

# ... your existing code ...

# Add to your main page:
st.markdown("---")

# Create a centered header
st.markdown("""
<div style='text-align: center; margin: 2rem 0;'>
    <h2>📅 Today's Market Events</h2>
    <p>Economic calendar, IPO listings, and market summary</p>
</div>
""", unsafe_allow_html=True)

# Render the full dashboard
widget = get_calendar_widget()
widget.render_full_dashboard()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: rgba(255,255,255,0.6); font-size: 0.85rem;'>
    Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)
```

---

## 📋 Customization Options

### Change Colors
Edit the color values in the CSS:
```python
# In economic_calendar_widget.py
'very_high_color': '#DC2626',  # Change to your color
'high_color': '#F97316',
'moderate_color': '#EABB00',
```

### Add More Releases
```python
MAJOR_RELEASES = [
    # ... existing ...
    {
        'name': 'Your Release Name',
        'agency': 'Agency Name',
        'time': '08:30 AM ET',
        'impact': 'High',  # Very High, High, Moderate
        'color': '#YOUR_COLOR',
        'description': 'Description here',
        'schedule': 'Schedule here',
        'category': 'Category'
    }
]
```

### Change Tab Names
```python
tab1, tab2, tab3 = st.tabs(["Your Name 1", "Your Name 2", "Your Name 3"])
```

---

## 🐛 Troubleshooting

**Issue:** Import error
- **Fix:** Make sure file is at `frontend/components/economic_calendar_widget.py`

**Issue:** Market data not loading
- **Fix:** Check internet connection, yfinance API limits
- **Fallback:** Widget still displays calendar (market data optional)

**Issue:** Styling looks wrong
- **Fix:** Clear cache, refresh browser (F5)
- **Tip:** CSS loads on first render

**Issue:** Takes too long to load
- **Fix:** Data is cached for 1 hour, second visit will be instant

---

## ✅ What You Get

✅ Professional-looking economic calendar  
✅ Color-coded by market impact  
✅ IPO information and links  
✅ Live market indices  
✅ Mansa Capital branding  
✅ Responsive design  
✅ 1-hour caching  
✅ No additional costs  
✅ Works with existing app  
✅ Fully customizable  

---

## 🎯 Next Steps

1. **Choose placement** - Where in your app?
2. **Add import** - 1 line
3. **Add widget render** - 2 lines
4. **Test it** - Run the app
5. **Customize** - Adjust colors, content as needed

---

## 📞 Questions?

The widget is self-contained and can be:
- Used standalone
- Combined with other components
- Customized extensively
- Integrated anywhere in your app

Check the code comments in `economic_calendar_widget.py` for more details!
