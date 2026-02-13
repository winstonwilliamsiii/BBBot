"""
Bentley Budget Bot - DEMO VERSION (No Infrastructure Required)
This version works without MySQL, Plaid, or MLflow for investor demo
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Bentley Budget Bot - Demo",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# DEMO STYLING
# ============================================
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .success-box {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .info-box {
        background: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
col1, col2 = st.columns([3, 1])
with col1:
    st.title("💰 Bentley Budget Bot")
    st.subheader("Multi-Platform Financial Portfolio Dashboard")
with col2:
    st.metric("Demo Version", "✅ No DB Required")

st.markdown("---")

# ============================================
# DEMO DATA GENERATION
# ============================================

def generate_demo_portfolio():
    """Generate sample portfolio data"""
    return pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA'],
        'Shares': [50, 100, 25, 30, 10],
        'Price': [185.50, 420.25, 140.80, 875.30, 245.75],
        'Value': [9275, 42025, 3520, 26259, 2457.50],
        'Change %': [+5.2, +3.1, -1.5, +12.3, -2.8]
    })

def generate_demo_crypto():
    """Generate sample crypto data"""
    return pd.DataFrame({
        'Cryptocurrency': ['Bitcoin', 'Ethereum', 'Cardano', 'Solana', 'Ripple'],
        'Symbol': ['BTC', 'ETH', 'ADA', 'SOL', 'XRP'],
        'Price': [42350.50, 2280.75, 0.98, 95.35, 2.15],
        'Holdings': [0.5, 10, 5000, 100, 10000],
        'Value': [21175.25, 22807.50, 4900, 9535, 21500],
        '24h Change': [+2.1, -0.8, +1.5, +3.2, -1.1]
    })

def generate_demo_transactions():
    """Generate sample transaction history"""
    dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
    return pd.DataFrame({
        'Date': dates,
        'Description': ['Stock Purchase', 'Crypto Deposit', 'Dividend', 'Stock Sale', 
                       'Transfer In', 'Fee', 'Stock Purchase', 'Crypto Trade', 
                       'Dividend', 'Transfer Out'],
        'Amount': [2500, 5000, 125, -3500, 10000, -50, 1500, -2000, 185, -5000],
        'Category': ['Stocks', 'Crypto', 'Dividend', 'Stocks', 'Transfer', 
                    'Fee', 'Stocks', 'Crypto', 'Dividend', 'Transfer']
    })

# ============================================
# MAIN DASHBOARD
# ============================================

st.markdown("""
<div class="success-box">
    <strong>✅ DEMO MODE ACTIVE</strong><br>
    This is a functional demo using sample data. Full version requires:<br>
    • MySQL database (for portfolio persistence)<br>
    • Plaid integration (for real bank connections)<br>
    • MLflow (for machine learning models)
</div>
""", unsafe_allow_html=True)

st.markdown("")

# Portfolio Summary
portfolio = generate_demo_portfolio()
total_portfolio_value = portfolio['Value'].sum()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Portfolio Value", f"${total_portfolio_value:,.2f}", "+12.5%")
with col2:
    st.metric("Crypto Holdings", "$58,742.75", "+5.8%")
with col3:
    st.metric("Cash Available", "$25,000", "Ready")
with col4:
    st.metric("Total Assets", f"${total_portfolio_value + 58742.75 + 25000:,.2f}", "+8.3%")

st.markdown("---")

# ============================================
# TAB INTERFACE
# ============================================

tab1, tab2, tab3, tab4 = st.tabs(["📊 Stock Portfolio", "🔴 Crypto Holdings", "💳 Transactions", "📈 Analysis"])

# TAB 1: Stock Portfolio
with tab1:
    st.subheader("Stock Portfolio")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.dataframe(
            portfolio,
            use_container_width=True,
            column_config={
                "Value": st.column_config.NumberColumn(format="$%,.2f"),
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Change %": st.column_config.NumberColumn(format="%.1f%%"),
            }
        )
    
    with col2:
        st.subheader("Portfolio Breakdown")
        fig_data = pd.DataFrame({
            'Stock': portfolio['Ticker'],
            'Value': portfolio['Value']
        })
        st.bar_chart(fig_data.set_index('Stock'))
    
    st.markdown("---")
    st.info("💡 **Feature:** Connect real portfolio via CSV upload or Plaid integration")

# TAB 2: Crypto
with tab2:
    st.subheader("Cryptocurrency Holdings")
    
    crypto = generate_demo_crypto()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.dataframe(
            crypto,
            use_container_width=True,
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Value": st.column_config.NumberColumn(format="$%.2f"),
                "24h Change": st.column_config.NumberColumn(format="%.1f%%"),
            }
        )
    
    with col2:
        st.subheader("Holdings by Crypto")
        fig_data = pd.DataFrame({
            'Crypto': crypto['Symbol'],
            'Value': crypto['Value']
        })
        st.bar_chart(fig_data.set_index('Crypto'))
    
    st.markdown("---")
    st.info("💡 **Feature:** Real-time prices from CoinGecko, Binance, or other exchanges")

# TAB 3: Transactions
with tab3:
    st.subheader("Transaction History")
    
    transactions = generate_demo_transactions()
    transactions['Date'] = pd.to_datetime(transactions['Date']).dt.strftime('%Y-%m-%d')
    
    st.dataframe(
        transactions,
        use_container_width=True,
        column_config={
            "Amount": st.column_config.NumberColumn(format="$%.2f"),
            "Date": st.column_config.TextColumn(),
        }
    )
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("By Category")
        category_sum = transactions.groupby('Category')['Amount'].sum()
        st.bar_chart(category_sum)
    
    with col2:
        st.subheader("Trend Over Time")
        daily_total = transactions.groupby('Date')['Amount'].sum().cumsum()
        st.line_chart(daily_total)

# TAB 4: Analysis
with tab4:
    st.subheader("Portfolio Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Performance Metrics")
        metrics_data = {
            'Metric': ['YTD Return', 'Monthly Return', 'Sharpe Ratio', 'Max Drawdown'],
            'Value': ['+18.5%', '+2.3%', '1.85', '-8.2%']
        }
        st.dataframe(pd.DataFrame(metrics_data), use_container_width=True)
    
    with col2:
        st.write("### Risk Assessment")
        risk_data = {
            'Risk Factor': ['Volatility', 'Beta', 'Correlation', 'Concentration'],
            'Level': ['Medium', 'High', 'Low', 'Medium']
        }
        st.dataframe(pd.DataFrame(risk_data), use_container_width=True)
    
    st.markdown("---")
    st.info("💡 **Feature:** Advanced ML models (MLflow) for predictions and signals")

# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    st.title("⚙️ Settings")
    st.markdown("---")
    
    st.subheader("📊 Demo Features")
    st.checkbox("Show Stock Portfolio", value=True)
    st.checkbox("Show Crypto Holdings", value=True)
    st.checkbox("Show Transaction History", value=True)
    
    st.markdown("---")
    st.subheader("🔧 Infrastructure Status")
    
    st.write("### Database Services")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**MySQL**")
        st.caption("💾 Status: Not required")
    with col2:
        st.write("**Redis**")
        st.caption("💾 Status: Not required")
    
    st.write("### External APIs")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Plaid**")
        st.caption("🔗 Status: Optional")
    with col2:
        st.write("**MLflow**")
        st.caption("🤖 Status: Optional")
    
    st.markdown("---")
    st.write("### 📚 Demo Information")
    st.info("""
    This demo version shows all UI/UX features without requiring:
    - Database connections
    - External API keys
    - Infrastructure setup
    
    Perfect for presenting to stakeholders!
    """)
    
    st.markdown("---")
    st.write("### 🚀 For Production Use")
    st.warning("""
    **Required Components:**
    1. Deploy full requirements.txt
    2. Set up MySQL database
    3. Configure Plaid integration
    4. Set up MLflow tracking
    5. Configure environment variables
    
    See `PRODUCTION_SETUP.md` for details.
    """)

# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p><strong>Bentley Budget Bot</strong> - Financial Portfolio Dashboard</p>
    <p>Demo Version | Built with Streamlit</p>
    <p>For inquiries: <a href="mailto:contact@bentleybot.com">contact@bentleybot.com</a></p>
</div>
""", unsafe_allow_html=True)
