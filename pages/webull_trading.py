"""
Webull Trading Dashboard for BentleyBot
Streamlit interface for viewing portfolio and placing trades
"""

import streamlit as st
import pandas as pd
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.webull_client import create_webull_client
from frontend.styles.colors import COLOR_SCHEME
from frontend.utils.styling import create_metric_card, create_custom_card


def initialize_webull_client():
    """Initialize Webull client with error handling"""
    try:
        # Check if credentials are configured
        if not os.getenv("WEBULL_APP_KEY") or not os.getenv("WEBULL_APP_SECRET"):
            st.warning(
                "⚠️ Webull API credentials not configured. "
                "Add WEBULL_APP_KEY and WEBULL_APP_SECRET to your .env file."
            )
            return None
        
        # Create client (use production=False for testing)
        client = create_webull_client(use_production=False)
        return client
    except Exception as e:
        st.error(f"❌ Failed to initialize Webull client: {str(e)}")
        return None


def display_portfolio_summary(client):
    """Display portfolio summary metrics"""
    st.subheader("📊 Portfolio Summary")
    
    try:
        summary = client.get_portfolio_summary()
        
        # Display key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            create_metric_card(
                "Total Value",
                f"${summary['total_value']:,.2f}",
                ""
            )
        
        with col2:
            create_metric_card(
                "Cash Balance",
                f"${summary['cash_balance']:,.2f}",
                ""
            )
        
        with col3:
            create_metric_card(
                "Buying Power",
                f"${summary['buying_power']:,.2f}",
                ""
            )
        
        with col4:
            create_metric_card(
                "Positions",
                str(summary['total_positions']),
                ""
            )
        
        return summary
    except Exception as e:
        st.error(f"Failed to fetch portfolio summary: {str(e)}")
        return None


def display_positions(client):
    """Display current positions in a table"""
    st.subheader("📈 Current Positions")
    
    try:
        positions = client.get_account_positions()
        
        if not positions:
            st.info("No positions found.")
            return
        
        # Convert to DataFrame for display
        df_data = []
        for pos in positions:
            df_data.append({
                "Symbol": pos.get('symbol', 'N/A'),
                "Quantity": pos.get('quantity', 0),
                "Market Value": f"${pos.get('market_value', 0):,.2f}",
                "Cost Basis": f"${pos.get('cost_basis', 0):,.2f}",
                "P&L": f"${pos.get('unrealized_profit_loss', 0):,.2f}",
                "P&L %": f"{(pos.get('unrealized_profit_loss', 0) / pos.get('cost_basis', 1) * 100):+.2f}%"
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Failed to fetch positions: {str(e)}")


def display_open_orders(client):
    """Display open orders"""
    st.subheader("📋 Open Orders")
    
    try:
        orders = client.get_open_orders()
        
        if not orders:
            st.info("No open orders.")
            return
        
        # Convert to DataFrame
        df_data = []
        for order in orders:
            df_data.append({
                "Symbol": order.get('symbol', 'N/A'),
                "Side": order.get('side', 'N/A'),
                "Type": order.get('order_type', 'N/A'),
                "Quantity": order.get('quantity', 0),
                "Price": f"${order.get('limit_price', 0):.2f}",
                "Status": order.get('status', 'N/A'),
                "Order ID": order.get('client_order_id', 'N/A')[:8]
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Failed to fetch open orders: {str(e)}")


def trade_form(client):
    """Display trading form"""
    st.subheader("🚀 Place Trade")
    
    with st.form("trade_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("Symbol", placeholder="AAPL").upper()
            quantity = st.number_input("Quantity", min_value=1, value=1)
            side = st.selectbox("Side", ["BUY", "SELL"])
        
        with col2:
            order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"])
            limit_price = st.number_input(
                "Limit Price",
                min_value=0.01,
                value=100.0,
                disabled=(order_type == "MARKET")
            )
            time_in_force = st.selectbox("Time in Force", ["DAY", "GTC"])
        
        # Preview button
        col_preview, col_submit = st.columns(2)
        
        preview_clicked = col_preview.form_submit_button("👀 Preview Order", use_container_width=True)
        submit_clicked = col_submit.form_submit_button("✅ Place Order", use_container_width=True, type="primary")
        
        if preview_clicked:
            try:
                preview = client.preview_equity_order(
                    symbol=symbol,
                    quantity=quantity,
                    side=side,
                    order_type=order_type,
                    limit_price=limit_price if order_type == "LIMIT" else None
                )
                st.success("✅ Order Preview")
                st.json(preview)
            except Exception as e:
                st.error(f"Preview failed: {str(e)}")
        
        if submit_clicked:
            try:
                result = client.place_equity_order(
                    symbol=symbol,
                    quantity=quantity,
                    side=side,
                    order_type=order_type,
                    limit_price=limit_price if order_type == "LIMIT" else None,
                    time_in_force=time_in_force
                )
                st.success(f"✅ Order placed successfully!")
                st.json(result)
                st.rerun()
            except Exception as e:
                st.error(f"Order placement failed: {str(e)}")


def main():
    """Main Webull dashboard"""
    st.set_page_config(
        page_title="Webull Trading | BentleyBot",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 Webull Trading Dashboard")
    st.markdown("---")
    
    # Initialize client
    client = initialize_webull_client()
    
    if client is None:
        st.stop()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Portfolio", "Trading", "Orders"])
    
    with tab1:
        # Portfolio summary
        summary = display_portfolio_summary(client)
        st.markdown("---")
        
        # Display positions
        if summary:
            display_positions(client)
    
    with tab2:
        # Trading form
        trade_form(client)
    
    with tab3:
        # Open orders
        display_open_orders(client)
        
        # Refresh button
        if st.button("🔄 Refresh Orders"):
            st.rerun()


if __name__ == "__main__":
    main()
