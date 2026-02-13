"""
Demo Mode Configuration
========================
Run Streamlit app with demo credentials and bypass MySQL for testing.
"""

import streamlit as st
import os

def setup_demo_mode():
    """Configure app to run in demo mode without requiring real API credentials"""
    
    # Set demo environment variables
    os.environ['DEMO_MODE'] = 'true'
    os.environ['BYPASS_MYSQL'] = 'true'
    os.environ['DEMO_USER'] = 'demo'
    os.environ['DEMO_ROLE'] = 'ADMIN'
    
    # Initialize session state for demo
    if 'demo_mode' not in st.session_state:
        st.session_state.demo_mode = True
        st.session_state.username = 'demo'
        st.session_state.role = 'ADMIN'
        st.session_state.is_authenticated = True
        
    st.sidebar.success("🎮 Demo Mode Active")
    st.sidebar.info("Using demo credentials - some features limited")

def is_demo_mode():
    """Check if app is running in demo mode"""
    return os.getenv('DEMO_MODE') == 'true' or st.session_state.get('demo_mode', False)

def get_demo_data():
    """Provide demo data for testing"""
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Demo portfolio data
    demo_portfolio = pd.DataFrame({
        'Symbol': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN'],
        'Quantity': [100, 50, 30, 25, 40],
        'Purchase_Price': [150.0, 300.0, 140.0, 200.0, 180.0],
        'Purchase_Date': [
            datetime.now() - timedelta(days=365),
            datetime.now() - timedelta(days=300),
            datetime.now() - timedelta(days=200),
            datetime.now() - timedelta(days=150),
            datetime.now() - timedelta(days=100)
        ]
    })
    
    # Demo transactions
    demo_transactions = pd.DataFrame({
        'date': pd.date_range(start='2025-01-01', periods=30, freq='D'),
        'amount': [100, -50, 200, -75, -30, 150, -100, 80, -60, -40] * 3,
        'category': ['Income', 'Food', 'Salary', 'Transport', 'Entertainment'] * 6,
        'description': ['Paycheck', 'Grocery Store', 'Bonus', 'Gas', 'Movie'] * 6
    })
    
    return {
        'portfolio': demo_portfolio,
        'transactions': demo_transactions
    }
