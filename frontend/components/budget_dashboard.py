"""
Budget Dashboard Component
===========================
UI components for displaying personal budget analysis with transaction data.

Features:
- Cash flow summary cards (income, expenses, net flow)
- Budget vs actual comparison
- Category spending breakdown
- Recent transactions table
- Spending trends charts
- Plaid connection status
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Optional

from frontend.utils.budget_analysis import BudgetAnalyzer, format_currency, format_percentage, get_trend_emoji
from frontend.styles.colors import COLOR_SCHEME


def show_plaid_connection_prompt(user_id: int):
    """Display prompt to connect bank account via Plaid."""
    st.markdown("---")
    st.header("💰 Personal Budget Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("📊 **Connect your bank account to unlock budget analysis**")
        st.markdown("""
        Get insights into your spending with:
        - 📈 Real-time cash flow tracking
        - 🎯 Budget vs actual comparisons
        - 📊 Category-wise spending breakdown
        - 💡 Personalized financial insights
        - 🔒 Bank-level security with Plaid
        """)
    
    with col2:
        # Display Plaid logo from local file
        import os
        from pathlib import Path
        
        # Try to load Plaid logo
        logo_path = Path(__file__).parent.parent.parent / "resources" / "images" / "plaid_logo.png"
        
        if logo_path.exists():
            st.image(str(logo_path), width=200, use_container_width=False)
        else:
            # Fallback if logo not found
            st.markdown("""
            <div style='text-align: center; padding: 20px 10px; background: linear-gradient(135deg, rgba(0,0,0,0.3) 0%, rgba(6,182,212,0.2) 100%); border-radius: 10px; margin-bottom: 10px;'>
                <div style='font-size: 2rem; font-weight: 700; color: #06B6D4; margin-bottom: 5px;'>
                    PLAID
                </div>
                <p style='font-size: 0.75rem; color: rgba(230,238,248,0.7); margin: 0;'>
                    🔒 Bank-Level Security
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<p style='text-align: center; font-size: 0.8rem; color: rgba(230,238,248,0.6); margin-top: 5px;'>🔒 Bank-Level Security</p>", unsafe_allow_html=True)
        
        # Connect Your Bank button with Plaid Link
        try:
            from frontend.utils.plaid_link import render_plaid_link_button
            
            # Render Plaid Link button with OAuth flow
            render_plaid_link_button(user_id)
            
        except ValueError as e:
            # Credentials not configured - show setup instructions
            if st.button("🔗 Connect Your Bank", type="primary", use_container_width=True, key="connect_bank_btn"):
                st.warning("⚠️ Plaid credentials not configured")
                st.info("""
                **To enable bank connections:**
                
                1. 📝 **Sign up at:** https://plaid.com/dashboard
                2. 🔑 **Get credentials:**
                   - PLAID_CLIENT_ID
                   - PLAID_SECRET
                3. ⚙️ **Update .env file** with your credentials
                4. 🔄 **Restart app** to apply changes
                
                **What you'll be able to do:**
                - 🏦 Connect any US bank account
                - 📊 Auto-sync transactions (last 90 days)
                - 💰 Track spending by category
                - 📈 Get personalized insights
                
                🔒 **Security:** Your bank credentials are never stored. Plaid uses bank-level encryption trusted by Venmo, Robinhood, and thousands of fintech apps.
                """)
                
                st.markdown("[![Sign Up](https://img.shields.io/badge/Sign%20Up-Plaid%20Dashboard-00d4ff?style=for-the-badge)](https://plaid.com/dashboard)", unsafe_allow_html=True)
        
        except Exception as e:
            # Other error - show error message
            st.error(f"Error loading Plaid Link: {e}")
            with st.expander("🐛 Debug Info"):
                import traceback
                st.code(traceback.format_exc())


def show_budget_summary(user_id: int, month: str = None):
    """
    Display budget summary section on home page.
    This is a compact view with key metrics only.
    
    Args:
        user_id: User ID
        month: Month in YYYY-MM format (defaults to current month)
    """
    analyzer = BudgetAnalyzer()
    
    # Check Plaid connection
    plaid_status = analyzer.check_plaid_connection(user_id)
    
    if not plaid_status['connected']:
        show_plaid_connection_prompt(user_id)
        return
    
    st.markdown("---")
    st.header("💰 Personal Budget Analysis")
    
    # Month selector and last sync info
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        # Month selector (last 12 months)
        months_list = []
        for i in range(12):
            m = datetime.now().replace(day=1) - pd.DateOffset(months=i)
            months_list.append(m.strftime('%Y-%m'))
        
        selected_month = st.selectbox(
            "Select Month",
            options=months_list,
            index=0,
            format_func=lambda x: datetime.strptime(x, '%Y-%m').strftime('%B %Y')
        )
        month = selected_month
    
    with col2:
        if plaid_status.get('last_sync'):
            last_sync = plaid_status['last_sync']
            if isinstance(last_sync, str):
                last_sync = datetime.fromisoformat(last_sync)
            time_diff = datetime.now() - last_sync
            
            if time_diff.total_seconds() < 3600:
                sync_text = f"{int(time_diff.total_seconds() / 60)} minutes ago"
            elif time_diff.total_seconds() < 86400:
                sync_text = f"{int(time_diff.total_seconds() / 3600)} hours ago"
            else:
                sync_text = f"{time_diff.days} days ago"
            
            st.info(f"🔄 Last synced: {sync_text}")
            if st.button("🔄 Sync Now", use_container_width=True):
                st.success("✅ Sync scheduled!")
                # TODO: Trigger Plaid sync
        else:
            st.info("🔄 Syncing...")
    
    # Get cash flow data
    cash_flow = analyzer.calculate_cash_flow(user_id, month)
    
    # Cash Flow Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        income_emoji = get_trend_emoji(cash_flow['income_change_pct'])
        st.metric(
            label="💵 Total Income",
            value=format_currency(cash_flow['income']),
            delta=f"{income_emoji} {format_percentage(cash_flow['income_change_pct'])} vs last month"
        )
    
    with col2:
        expense_emoji = get_trend_emoji(-cash_flow['expense_change_pct'])  # Inverted for expenses
        st.metric(
            label="💸 Total Expenses",
            value=format_currency(cash_flow['expenses']),
            delta=f"{expense_emoji} {format_percentage(cash_flow['expense_change_pct'])} vs last month",
            delta_color="inverse"  # Red is good for expense decrease
        )
    
    with col3:
        net_emoji = get_trend_emoji(cash_flow['net_flow_change_pct'])
        net_color = "normal" if cash_flow['net_flow'] >= 0 else "inverse"
        st.metric(
            label="💰 Net Cash Flow",
            value=format_currency(cash_flow['net_flow']),
            delta=f"{net_emoji} {format_percentage(cash_flow['net_flow_change_pct'])} vs last month",
            delta_color=net_color
        )
    
    # Top Categories (Top 3)
    st.subheader("📊 Top Spending Categories")
    
    top_categories = analyzer.get_spending_by_category(user_id, month, limit=3)
    
    if not top_categories.empty:
        for idx, row in top_categories.iterrows():
            category = row['category']
            amount = row['amount']
            percentage = row['percentage']
            
            # Get budget for this category
            budget_df = analyzer.get_budget_status(user_id, month)
            if not budget_df.empty:
                budget_row = budget_df[budget_df['category'] == category]
                if not budget_row.empty:
                    budget = budget_row.iloc[0]['budgeted']
                    actual = budget_row.iloc[0]['actual']
                    status = budget_row.iloc[0]['status']
                    icon = budget_row.iloc[0].get('icon', '💰')
                    
                    # Progress bar
                    progress_pct = (actual / budget * 100) if budget > 0 else 0
                    progress_color = (
                        "🟢" if status == "Under Budget" 
                        else "🟡" if status == "On Track" 
                        else "🔴"
                    )
                    
                    st.markdown(f"""
                    **{icon} {category}** {progress_color}  
                    {format_currency(actual)} / {format_currency(budget)} ({percentage:.0f}% of total spending)
                    """)
                    st.progress(min(progress_pct / 100, 1.0))
                else:
                    st.markdown(f"**💰 {category}**: {format_currency(amount)} ({percentage:.0f}% of total)")
            else:
                st.markdown(f"**💰 {category}**: {format_currency(amount)} ({percentage:.0f}% of total)")
    else:
        st.info("No spending data available for this month.")
    
    # Link to full budget page
    st.markdown("")
    if st.button("📊 View Full Budget Dashboard →", use_container_width=True):
        st.switch_page("pages/01_💰_Personal_Budget.py")
    
    # Bank connection info
    st.caption(f"🏦 Connected: {plaid_status.get('institution', 'Unknown Bank')}")


def show_full_budget_dashboard(user_id: int):
    """
    Display full budget dashboard with all details.
    This is used on the dedicated budget page.
    
    Args:
        user_id: User ID
    """
    analyzer = BudgetAnalyzer()
    
    # Check Plaid connection
    plaid_status = analyzer.check_plaid_connection(user_id)
    
    if not plaid_status['connected']:
        show_plaid_connection_prompt(user_id)
        return
    
    # Header
    st.title("💰 Personal Budget Dashboard")
    
    # Month selector
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        months_list = []
        for i in range(12):
            m = datetime.now().replace(day=1) - pd.DateOffset(months=i)
            months_list.append(m.strftime('%Y-%m'))
        
        selected_month = st.selectbox(
            "Select Month",
            options=months_list,
            index=0,
            format_func=lambda x: datetime.strptime(x, '%Y-%m').strftime('%B %Y')
        )
    
    with col2:
        if st.button("🔄 Sync Transactions", use_container_width=True):
            with st.spinner("Syncing with bank..."):
                # TODO: Trigger Plaid sync
                st.success("✅ Transactions synced!")
    
    with col3:
        if st.button("⚙️ Manage Budgets", use_container_width=True):
            st.info("Budget management coming soon!")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💳 Transactions", "📈 Trends", "💡 Insights"])
    
    with tab1:
        show_overview_tab(analyzer, user_id, selected_month)
    
    with tab2:
        show_transactions_tab(analyzer, user_id, selected_month)
    
    with tab3:
        show_trends_tab(analyzer, user_id)
    
    with tab4:
        show_insights_tab(analyzer, user_id, selected_month)


def show_overview_tab(analyzer: BudgetAnalyzer, user_id: int, month: str):
    """Display overview tab with cash flow and budget status."""
    
    # Cash flow metrics
    cash_flow = analyzer.calculate_cash_flow(user_id, month)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💵 Income",
            format_currency(cash_flow['income']),
            format_percentage(cash_flow['income_change_pct'])
        )
    
    with col2:
        st.metric(
            "💸 Expenses",
            format_currency(cash_flow['expenses']),
            format_percentage(cash_flow['expense_change_pct']),
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "💰 Net Flow",
            format_currency(cash_flow['net_flow']),
            format_percentage(cash_flow['net_flow_change_pct'])
        )
    
    with col4:
        st.metric(
            "📊 Transactions",
            cash_flow['transaction_count'],
            f"Avg: {format_currency(cash_flow['avg_transaction'])}"
        )
    
    st.markdown("---")
    
    # Budget vs Actual
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Budget Status")
        budget_status = analyzer.get_budget_status(user_id, month)
        
        if not budget_status.empty:
            # Create horizontal bar chart
            fig = go.Figure()
            
            for _, row in budget_status.iterrows():
                fig.add_trace(go.Bar(
                    y=[row['category']],
                    x=[row['budgeted']],
                    name='Budget',
                    orientation='h',
                    marker=dict(color='lightgray'),
                    text=format_currency(row['budgeted']),
                    textposition='inside'
                ))
                
                color = 'green' if row['status'] == 'Under Budget' else 'orange' if row['status'] == 'On Track' else 'red'
                fig.add_trace(go.Bar(
                    y=[row['category']],
                    x=[row['actual']],
                    name='Actual',
                    orientation='h',
                    marker=dict(color=color),
                    text=format_currency(row['actual']),
                    textposition='inside'
                ))
            
            fig.update_layout(
                barmode='overlay',
                height=400,
                showlegend=True,
                xaxis_title="Amount ($)",
                yaxis_title=""
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No budget data available. Set up your budgets to track spending!")
    
    with col2:
        st.subheader("📊 Spending by Category")
        categories = analyzer.get_spending_by_category(user_id, month)
        
        if not categories.empty:
            fig = px.pie(
                categories,
                values='amount',
                names='category',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>'
            )
            
            fig.update_layout(height=400)
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No spending data available for this month.")


def show_transactions_tab(analyzer: BudgetAnalyzer, user_id: int, month: str):
    """Display transactions tab with searchable/filterable table."""
    
    st.subheader("💳 Transaction History")
    
    # Date range for the month
    start_date = f"{month}-01"
    end_date = (datetime.strptime(start_date, '%Y-%m-%d') + pd.DateOffset(months=1) - pd.DateOffset(days=1)).strftime('%Y-%m-%d')
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("🔍 Search transactions", "")
    
    with col2:
        categories = analyzer.get_spending_by_category(user_id, month)
        category_list = ['All'] + list(categories['category'].unique()) if not categories.empty else ['All']
        selected_category = st.selectbox("Category", category_list)
    
    with col3:
        transaction_type = st.selectbox("Type", ["All", "Income", "Expenses"])
    
    # Fetch transactions
    df = analyzer.fetch_transactions(user_id, start_date, end_date)
    
    if not df.empty:
        # Apply filters
        if search_term:
            df = df[df['name'].str.contains(search_term, case=False, na=False) | 
                   df['merchant_name'].str.contains(search_term, case=False, na=False)]
        
        if selected_category != 'All':
            df = df[df['category'] == selected_category]
        
        if transaction_type == "Income":
            df = df[df['amount'] > 0]
        elif transaction_type == "Expenses":
            df = df[df['amount'] < 0]
        
        # Format display
        display_df = df[['date', 'name', 'merchant_name', 'amount', 'category', 'pending']].copy()
        display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
        display_df['amount'] = display_df['amount'].apply(format_currency)
        display_df.columns = ['Date', 'Description', 'Merchant', 'Amount', 'Category', 'Pending']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Export button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Export to CSV",
            data=csv,
            file_name=f"transactions_{month}.csv",
            mime="text/csv"
        )
    else:
        st.info("No transactions found for the selected filters.")


def show_trends_tab(analyzer: BudgetAnalyzer, user_id: int):
    """Display trends tab with historical charts."""
    
    st.subheader("📈 Cash Flow Trends")
    
    # Get historical data
    trends = analyzer.get_monthly_trends(user_id, months=6)
    
    if not trends.empty:
        # Line chart for cash flow
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=trends['month'],
            y=trends['income'],
            mode='lines+markers',
            name='Income',
            line=dict(color='green', width=2),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=trends['month'],
            y=trends['expenses'],
            mode='lines+markers',
            name='Expenses',
            line=dict(color='red', width=2),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=trends['month'],
            y=trends['net_flow'],
            mode='lines+markers',
            name='Net Cash Flow',
            line=dict(color='blue', width=3, dash='dash'),
            marker=dict(size=10)
        ))
        
        fig.update_layout(
            title="6-Month Cash Flow Trend",
            xaxis_title="Month",
            yaxis_title="Amount ($)",
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_income = trends['income'].mean()
            st.metric("📊 Avg Monthly Income", format_currency(avg_income))
        
        with col2:
            avg_expenses = trends['expenses'].mean()
            st.metric("📊 Avg Monthly Expenses", format_currency(avg_expenses))
        
        with col3:
            avg_net = trends['net_flow'].mean()
            st.metric("📊 Avg Net Cash Flow", format_currency(avg_net))
    else:
        st.info("Insufficient historical data. Connect your bank and sync transactions!")


def show_insights_tab(analyzer: BudgetAnalyzer, user_id: int, month: str):
    """Display insights tab with alerts and recommendations."""
    
    st.subheader("💡 Financial Insights & Alerts")
    
    insights = analyzer.generate_insights(user_id, month)
    
    if insights:
        for insight in insights:
            if insight['severity'] == 'high':
                st.error(f"{insight['icon']} {insight['message']}")
            elif insight['severity'] == 'medium':
                st.warning(f"{insight['icon']} {insight['message']}")
            else:
                st.info(f"{insight['icon']} {insight['message']}")
    else:
        st.success("✅ Everything looks good! No alerts for this month.")
    
    st.markdown("---")
    
    # Recommendations
    st.subheader("💡 Personalized Recommendations")
    
    cash_flow = analyzer.calculate_cash_flow(user_id, month)
    
    recommendations = []
    
    if cash_flow['net_flow'] < 0:
        recommendations.append("💰 **Negative cash flow detected.** Review your expenses and identify areas to cut back.")
    
    if cash_flow['expense_change_pct'] > 10:
        recommendations.append("📉 **Spending increased significantly.** Check for unusual expenses or subscription renewals.")
    
    top_cat = analyzer.get_spending_by_category(user_id, month, limit=1)
    if not top_cat.empty and top_cat.iloc[0]['percentage'] > 40:
        recommendations.append(f"⚠️ **High concentration in {top_cat.iloc[0]['category']}.** Consider diversifying expenses.")
    
    if not recommendations:
        recommendations.append("✅ Your finances look healthy! Keep up the good work.")
    
    for rec in recommendations:
        st.markdown(f"- {rec}")
