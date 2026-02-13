"""
Example: Adding Economic Calendar Widget to Homepage
=====================================================
Shows different ways to integrate the calendar widget into streamlit_app.py

Copy/paste any of these examples into your streamlit_app.py
"""

# ============================================================================
# EXAMPLE 1: FULL DASHBOARD ON HOMEPAGE (Recommended for main visibility)
# ============================================================================

def example_full_dashboard():
    """Full dashboard with all three tabs"""
    import streamlit as st
    from frontend.components.economic_calendar_widget import get_calendar_widget
    
    st.markdown("---")
    
    # Render full dashboard with tabs
    widget = get_calendar_widget()
    widget.render_full_dashboard()


# ============================================================================
# EXAMPLE 2: QUICK SUMMARY IN SIDEBAR (Minimal space)
# ============================================================================

def example_sidebar_summary():
    """Quick event summary in sidebar"""
    import streamlit as st
    from frontend.components.economic_calendar_widget import render_todays_events
    
    # Add to your sidebar section:
    with st.sidebar:
        st.markdown("---")
        render_todays_events()


# ============================================================================
# EXAMPLE 3: SPLIT VIEW WITH ECONOMIC CALENDAR ON LEFT
# ============================================================================

def example_split_view():
    """Split calendar and other content side by side"""
    import streamlit as st
    from frontend.components.economic_calendar_widget import get_calendar_widget
    
    col1, col2 = st.columns([1.2, 0.8])
    
    with col1:
        st.markdown("## Main Content")
        # Your existing content here
        st.info("Portfolio data, charts, etc. would go here")
    
    with col2:
        st.markdown("## 📅 Today's Events")
        widget = get_calendar_widget()
        widget.render_economic_calendar()


# ============================================================================
# EXAMPLE 4: TABS WITH CALENDAR AS NEW TAB
# ============================================================================

def example_with_tabs():
    """Add calendar as a new tab in your app"""
    import streamlit as st
    from frontend.components.economic_calendar_widget import get_calendar_widget
    
    # If you have existing tabs:
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Dashboard", "Portfolio", "Budget", "📅 Calendar"]
    )
    
    with tab1:
        st.markdown("## Dashboard")
        st.info("Your dashboard content here")
    
    with tab2:
        st.markdown("## Portfolio")
        st.info("Your portfolio content here")
    
    with tab3:
        st.markdown("## Budget")
        st.info("Your budget content here")
    
    with tab4:
        widget = get_calendar_widget()
        widget.render_full_dashboard()


# ============================================================================
# EXAMPLE 5: JUST ECONOMIC CALENDAR
# ============================================================================

def example_just_calendar():
    """Minimal - just the economic calendar"""
    import streamlit as st
    from frontend.components.economic_calendar_widget import get_calendar_widget
    
    st.markdown("## 📅 Economic Calendar")
    
    widget = get_calendar_widget()
    widget.render_economic_calendar()


# ============================================================================
# EXAMPLE 6: JUST IPO CALENDAR
# ============================================================================

def example_just_ipos():
    """Minimal - just IPO information"""
    import streamlit as st
    from frontend.components.economic_calendar_widget import get_calendar_widget
    
    st.markdown("## 🚀 IPO Calendar")
    
    widget = get_calendar_widget()
    widget.render_ipo_calendar()


# ============================================================================
# EXAMPLE 7: JUST MARKET SUMMARY
# ============================================================================

def example_just_market():
    """Minimal - just market indices"""
    import streamlit as st
    from frontend.components.economic_calendar_widget import get_calendar_widget
    
    st.markdown("## 📊 Market Summary")
    
    widget = get_calendar_widget()
    widget.render_market_summary()


# ============================================================================
# EXAMPLE 8: FEATURED SECTION WITH ICON
# ============================================================================

def example_featured_section():
    """Calendar in a featured section with styling"""
    import streamlit as st
    from frontend.components.economic_calendar_widget import get_calendar_widget
    
    st.markdown("""
    <div style='text-align: center; margin: 2rem 0 1rem 0;'>
        <h2 style='color: #FFFFFF; margin-bottom: 0.5rem;'>
            📅 Economic Calendar & Market Events
        </h2>
        <p style='color: rgba(255,255,255,0.7); margin: 0;'>
            Stay informed about economic releases and market-moving events
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    widget = get_calendar_widget()
    widget.render_full_dashboard()


# ============================================================================
# EXAMPLE 9: ADVANCED - ADD TO EXISTING HOMEPAGE
# ============================================================================

def example_integrated_homepage():
    """Complete integration with existing content"""
    import streamlit as st
    from frontend.components.economic_calendar_widget import get_calendar_widget, render_todays_events
    
    # Your existing homepage content...
    st.markdown("# 📊 Bentley Budget Bot")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Portfolio Value", "$125,430", "+12%")
    with col2:
        st.metric("Monthly Savings", "$2,450", "+8%")
    with col3:
        st.metric("YTD Return", "18.5%", "+2.1%")
    
    # ADD THIS SECTION:
    st.markdown("---")
    st.markdown("## 📅 Economic Calendar & Market Events")
    
    widget = get_calendar_widget()
    widget.render_full_dashboard()
    
    # Continue with rest of your content...
    st.markdown("---")
    st.markdown("## Your Other Sections")


# ============================================================================
# EXAMPLE 10: SIDEBAR + MAIN CONTENT
# ============================================================================

def example_sidebar_main():
    """Calendar in sidebar with main content on right"""
    import streamlit as st
    from frontend.components.economic_calendar_widget import render_todays_events
    
    # Sidebar
    with st.sidebar:
        st.markdown("## Bentley Assistant")
        render_todays_events()
        st.markdown("---")
        # Other sidebar content...
    
    # Main content
    st.markdown("# Dashboard")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("Your main content")
    with col2:
        st.info("More content")


# ============================================================================
# QUICK COPY-PASTE SNIPPETS
# ============================================================================

"""
SNIPPET 1: Add to homepage (3 lines)
─────────────────────────────────────
from frontend.components.economic_calendar_widget import get_calendar_widget

widget = get_calendar_widget()
widget.render_full_dashboard()


SNIPPET 2: Add to sidebar (2 lines)
──────────────────────────────────────
from frontend.components.economic_calendar_widget import render_todays_events

with st.sidebar:
    render_todays_events()


SNIPPET 3: Add as tab (varies)
──────────────────────────────────
from frontend.components.economic_calendar_widget import get_calendar_widget

# In your tab:
widget = get_calendar_widget()
widget.render_full_dashboard()


SNIPPET 4: Just economic calendar (3 lines)
──────────────────────────────────────────────
from frontend.components.economic_calendar_widget import get_calendar_widget

widget = get_calendar_widget()
widget.render_economic_calendar()
"""


# ============================================================================
# RECOMMENDED PLACEMENT OPTIONS
# ============================================================================

"""
🎯 BEST PLACES TO ADD IT:

1. HOMEPAGE (Top of Page)
   - Most visible
   - Users see it immediately
   - Use Example 8 (featured section)

2. SIDEBAR (Always Visible)
   - Persistent
   - Doesn't take main space
   - Use Example 2 (sidebar summary)

3. NEW TAB (Dedicated Space)
   - Organized
   - Users choose to view
   - Use Example 4 (tabs)

4. MARKETS PAGE (If you have one)
   - Logical placement
   - Related content
   - Use Example 9 (integrated)

5. SPLIT VIEW (Side by Side)
   - Shows both together
   - Interactive
   - Use Example 3 (split view)

💡 RECOMMENDATION:
   Start with Example 1 (full dashboard) on homepage
   Later add Example 2 (sidebar summary) as well
"""


if __name__ == "__main__":
    # Uncomment one example to test:
    
    # example_full_dashboard()
    # example_split_view()
    # example_with_tabs()
    # example_featured_section()
    
    print("Copy any example function into your streamlit_app.py")
    print("Or use the snippets in the QUICK COPY-PASTE section above")
