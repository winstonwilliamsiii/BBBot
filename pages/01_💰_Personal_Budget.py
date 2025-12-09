"""
Personal Budget Page
====================
Full budget management interface with detailed analysis and transaction history.

Features:
- Complete cash flow dashboard
- Transaction search and filtering
- Budget vs actual tracking
- Category management
- Monthly/yearly trends
- Financial insights and alerts
- Plaid account management
"""

import streamlit as st

# RBAC imports
try:
    from frontend.utils.rbac import RBACManager, Permission, show_login_form, show_user_info
    from frontend.components.budget_dashboard import show_full_budget_dashboard
    RBAC_AVAILABLE = True
except ImportError:
    RBAC_AVAILABLE = False
    st.error("⚠️ RBAC module not available. Please check your installation.")

from frontend.utils.styling import apply_custom_styling, add_footer
from frontend.styles.colors import COLOR_SCHEME


def main():
    """Main function for the budget page."""
    
    # Page config
    st.set_page_config(
        page_title="Personal Budget | BBBot",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply styling
    apply_custom_styling()
    
    # Initialize RBAC session state
    RBACManager.init_session_state()
    
    # Check RBAC availability
    if not RBAC_AVAILABLE:
        st.error("🚫 Authentication system not available. Please contact your administrator.")
        return
    
    # Sidebar - User info and navigation
    with st.sidebar:
        st.markdown(f"""
        <h2 style='color: {COLOR_SCHEME['primary']}; text-align: center;'>
        💰 Budget Manager
        </h2>
        """, unsafe_allow_html=True)
        
        # Show user info if logged in
        if RBACManager.is_authenticated():
            show_user_info()
            
            st.markdown("---")
            
            # Quick actions
            st.subheader("Quick Actions")
            
            if st.button("🏠 Home", use_container_width=True):
                st.switch_page("streamlit_app.py")
            
            if st.button("📈 Investment Analysis", use_container_width=True):
                st.switch_page("pages/02_📈_Investment_Analysis.py")
            
            st.markdown("---")
            
            # Budget tips
            with st.expander("💡 Budget Tips"):
                st.markdown("""
                **Smart Budgeting:**
                - Follow the 50/30/20 rule
                  - 50% Needs (rent, utilities)
                  - 30% Wants (entertainment)
                  - 20% Savings/debt
                
                - Track every transaction
                - Review spending weekly
                - Set realistic goals
                - Build an emergency fund
                - Automate savings
                """)
        else:
            st.info("🔐 Please login to access your budget.")
    
    # Main content area
    if not RBACManager.is_authenticated():
        # Show login form for unauthenticated users
        st.title("💰 Personal Budget Dashboard")
        st.markdown("---")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ## Welcome to Your Personal Budget Manager
            
            Take control of your finances with powerful budgeting tools:
            
            ### 📊 **Features**
            - **Real-time Cash Flow Tracking** - Monitor income and expenses automatically
            - **Smart Categorization** - Transactions organized by category
            - **Budget vs Actual** - Compare planned spending with reality
            - **Financial Insights** - AI-powered spending analysis and alerts
            - **Trend Analysis** - Visualize your financial journey over time
            - **Secure Bank Integration** - Connect via Plaid (bank-level security)
            
            ### 🔒 **Privacy & Security**
            - Your data is encrypted and secure
            - Bank credentials never stored
            - Read-only access to transactions
            - RBAC authentication required
            
            ### 🚀 **Get Started**
            1. Login to your account
            2. Connect your bank account via Plaid
            3. Watch as transactions automatically sync
            4. Set budgets and track your progress
            """)
        
        with col2:
            st.image("https://via.placeholder.com/400x300?text=Budget+Dashboard", use_column_width=True)
            
            st.markdown("---")
            
            # Login form
            st.subheader("🔑 Login to Continue")
            if show_login_form():
                st.rerun()
    
    else:
        # User is authenticated - show budget dashboard
        user = RBACManager.get_current_user()
        
        # Check permission
        if not RBACManager.has_permission(Permission.VIEW_BUDGET):
            st.error("🚫 You don't have permission to view budget analysis.")
            st.info("💡 Contact your administrator to upgrade your account for budget access.")
            
            if st.button("🏠 Return to Home"):
                st.switch_page("streamlit_app.py")
            
            return
        
        # Display full budget dashboard
        try:
            show_full_budget_dashboard(user.user_id)
        except Exception as e:
            st.error(f"❌ Error loading budget dashboard: {e}")
            
            with st.expander("🔍 Troubleshooting"):
                st.markdown("""
                **Common Issues:**
                
                1. **Database not set up**
                   ```bash
                   mysql -u root -p mydb < scripts/setup/budget_schema.sql
                   ```
                
                2. **Missing environment variables**
                   - Check `.env` file has MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
                
                3. **Plaid not connected**
                   - Make sure you've connected your bank account
                   - Check PLAID_CLIENT_ID, PLAID_SECRET in `.env`
                
                4. **No transactions synced**
                   - Trigger a manual sync from the dashboard
                   - Check Plaid access token is valid
                
                **Need help?** Contact your system administrator.
                """)
            
            if st.button("🏠 Return to Home"):
                st.switch_page("streamlit_app.py")
    
    # Footer
    add_footer()


if __name__ == "__main__":
    main()
