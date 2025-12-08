"""
Broker Connections Display Module
Shows connected broker accounts and fund positions for authorized users
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import requests


class BrokerConnection:
    """Represents a broker account connection"""
    
    def __init__(
        self,
        broker_name: str,
        account_number: str,
        status: str,
        last_sync: datetime,
        balance: float,
        positions_count: int = 0,
    ):
        self.broker_name = broker_name
        self.account_number = account_number
        self.status = status
        self.last_sync = last_sync
        self.balance = balance
        self.positions_count = positions_count
    
    def to_dict(self) -> dict:
        return {
            'Broker': self.broker_name,
            'Account': self.account_number,
            'Status': self.status,
            'Last Sync': self.last_sync.strftime('%Y-%m-%d %H:%M:%S'),
            'Balance': f"${self.balance:,.2f}",
            'Positions': self.positions_count,
        }


class WebullFund:
    """Represents a Webull WeFolio fund"""
    
    def __init__(
        self,
        fund_id: str,
        name: str,
        nav: float,
        shares: float,
        value: float,
        daily_change: float,
        daily_change_pct: float,
    ):
        self.fund_id = fund_id
        self.name = name
        self.nav = nav
        self.shares = shares
        self.value = value
        self.daily_change = daily_change
        self.daily_change_pct = daily_change_pct
    
    def to_dict(self) -> dict:
        return {
            'Fund Name': self.name,
            'NAV': f"${self.nav:.2f}",
            'Shares': f"{self.shares:.4f}",
            'Value': f"${self.value:,.2f}",
            'Daily Change': f"${self.daily_change:+,.2f}",
            'Change %': f"{self.daily_change_pct:+.2f}%",
        }


class BrokerConnectionManager:
    """Manages broker connections and data fetching"""
    
    @staticmethod
    def get_demo_connections() -> List[BrokerConnection]:
        """Get demo broker connections for testing"""
        return [
            BrokerConnection(
                broker_name="Webull",
                account_number="****5678",
                status="Connected",
                last_sync=datetime.now(),
                balance=125430.50,
                positions_count=12,
            ),
            BrokerConnection(
                broker_name="TD Ameritrade",
                account_number="****9012",
                status="Connected",
                last_sync=datetime.now(),
                balance=87650.25,
                positions_count=8,
            ),
            BrokerConnection(
                broker_name="E*TRADE",
                account_number="****3456",
                status="Pending",
                last_sync=datetime.now(),
                balance=0.0,
                positions_count=0,
            ),
        ]
    
    @staticmethod
    def get_demo_webull_funds() -> List[WebullFund]:
        """Get demo Webull WeFolio funds for testing"""
        return [
            WebullFund(
                fund_id="WF001",
                name="Growth Leaders Fund",
                nav=125.45,
                shares=100.5,
                value=12607.73,
                daily_change=156.32,
                daily_change_pct=1.25,
            ),
            WebullFund(
                fund_id="WF002",
                name="Tech Innovation Fund",
                nav=98.72,
                shares=75.25,
                value=7428.67,
                daily_change=-42.15,
                daily_change_pct=-0.56,
            ),
            WebullFund(
                fund_id="WF003",
                name="Dividend Income Fund",
                nav=145.89,
                shares=50.0,
                value=7294.50,
                daily_change=28.50,
                daily_change_pct=0.39,
            ),
            WebullFund(
                fund_id="WF004",
                name="ESG Sustainable Fund",
                nav=112.34,
                shares=120.75,
                value=13562.54,
                daily_change=203.44,
                daily_change_pct=1.52,
            ),
        ]
    
    @staticmethod
    def fetch_webull_funds(api_token: str) -> List[WebullFund]:
        """
        Fetch WeFolio funds from Webull API
        
        Args:
            api_token: Webull API authentication token
            
        Returns:
            List of WebullFund objects
        """
        try:
            url = "https://api.webull.com/portfolio/v1/getFunds"
            headers = {"Authorization": f"Bearer {api_token}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            funds_data = response.json().get("funds", [])
            
            funds = []
            for fund in funds_data:
                funds.append(WebullFund(
                    fund_id=fund.get("id", ""),
                    name=fund.get("name", "Unknown Fund"),
                    nav=float(fund.get("nav", 0)),
                    shares=float(fund.get("shares", 0)),
                    value=float(fund.get("value", 0)),
                    daily_change=float(fund.get("daily_change", 0)),
                    daily_change_pct=float(fund.get("daily_change_pct", 0)),
                ))
            
            return funds
            
        except requests.RequestException as e:
            st.error(f"Failed to fetch Webull funds: {e}")
            return []
        except (KeyError, ValueError) as e:
            st.error(f"Error parsing Webull fund data: {e}")
            return []
    
    @staticmethod
    def save_funds_to_db(funds: List[WebullFund], db_config: dict):
        """
        Save Webull funds to MySQL database
        
        Args:
            funds: List of WebullFund objects
            db_config: Database configuration dictionary
        """
        try:
            import mysql.connector
            
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            for fund in funds:
                cursor.execute(
                    """
                    REPLACE INTO wefolio_funds 
                    (id, name, nav, shares, value, daily_change, daily_change_pct, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        fund.fund_id,
                        fund.name,
                        fund.nav,
                        fund.shares,
                        fund.value,
                        fund.daily_change,
                        fund.daily_change_pct,
                        datetime.now(),
                    )
                )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            st.success(f"✅ Saved {len(funds)} funds to database")
            
        except Exception as e:
            st.error(f"Failed to save funds to database: {e}")


def display_broker_connections():
    """Display broker account connections"""
    st.subheader("🔗 Connected Broker Accounts")
    
    connections = BrokerConnectionManager.get_demo_connections()
    
    if not connections:
        st.info("No broker connections found. Add connections to see your accounts here.")
        return
    
    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    
    total_balance = sum(conn.balance for conn in connections)
    connected_count = sum(1 for conn in connections if conn.status == "Connected")
    total_positions = sum(conn.positions_count for conn in connections)
    
    col1.metric("Total Balance", f"${total_balance:,.2f}")
    col2.metric("Connected Accounts", connected_count)
    col3.metric("Total Positions", total_positions)
    
    # Display connections table
    st.markdown("#### Account Details")
    
    connections_df = pd.DataFrame([conn.to_dict() for conn in connections])
    
    # Style the dataframe
    st.dataframe(
        connections_df,
        use_container_width=True,
        hide_index=True,
    )
    
    # Add connection status indicators
    st.markdown("##### Connection Status Legend")
    col1, col2, col3 = st.columns(3)
    col1.success("✅ Connected - Actively syncing")
    col2.warning("⏳ Pending - Awaiting authorization")
    col3.error("❌ Disconnected - Requires re-authentication")


def display_webull_funds():
    """Display Webull WeFolio funds"""
    st.subheader("💼 Webull WeFolio Funds")
    
    # Option to use real API or demo data
    use_real_api = st.checkbox("Use Real Webull API", value=False)
    
    if use_real_api:
        api_token = st.text_input("Webull API Token", type="password")
        
        if st.button("Fetch Funds"):
            if api_token:
                with st.spinner("Fetching funds from Webull..."):
                    funds = BrokerConnectionManager.fetch_webull_funds(api_token)
                    
                    if funds:
                        st.session_state.webull_funds = funds
                        st.success(f"✅ Fetched {len(funds)} funds")
                    else:
                        st.error("Failed to fetch funds. Using demo data.")
                        st.session_state.webull_funds = BrokerConnectionManager.get_demo_webull_funds()
            else:
                st.warning("Please enter your Webull API token")
    else:
        # Use demo data
        if 'webull_funds' not in st.session_state:
            st.session_state.webull_funds = BrokerConnectionManager.get_demo_webull_funds()
    
    funds = st.session_state.get('webull_funds', BrokerConnectionManager.get_demo_webull_funds())
    
    if not funds:
        st.info("No WeFolio funds found.")
        return
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_value = sum(fund.value for fund in funds)
    total_daily_change = sum(fund.daily_change for fund in funds)
    total_daily_change_pct = (total_daily_change / total_value) * 100 if total_value > 0 else 0
    
    col1.metric("Total Fund Value", f"${total_value:,.2f}")
    col2.metric("Number of Funds", len(funds))
    col3.metric("Daily Change", f"${total_daily_change:+,.2f}", f"{total_daily_change_pct:+.2f}%")
    
    avg_nav = sum(fund.nav for fund in funds) / len(funds) if funds else 0
    col4.metric("Avg NAV", f"${avg_nav:.2f}")
    
    # Display funds table
    st.markdown("#### Fund Details")
    
    funds_df = pd.DataFrame([fund.to_dict() for fund in funds])
    
    st.dataframe(
        funds_df,
        use_container_width=True,
        hide_index=True,
    )
    
    # Fund allocation chart
    st.markdown("#### Fund Allocation")
    
    import plotly.express as px
    
    allocation_df = pd.DataFrame({
        'Fund': [fund.name for fund in funds],
        'Value': [fund.value for fund in funds],
    })
    
    fig = px.pie(
        allocation_df,
        values='Value',
        names='Fund',
        title='Portfolio Allocation by Fund',
        hole=0.3,
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance comparison
    st.markdown("#### Fund Performance Comparison")
    
    performance_df = pd.DataFrame({
        'Fund': [fund.name for fund in funds],
        'Daily Change %': [fund.daily_change_pct for fund in funds],
    }).sort_values('Daily Change %', ascending=False)
    
    fig_perf = px.bar(
        performance_df,
        x='Daily Change %',
        y='Fund',
        orientation='h',
        title='Daily Performance Comparison',
        color='Daily Change %',
        color_continuous_scale=['red', 'yellow', 'green'],
    )
    
    fig_perf.update_layout(height=300)
    st.plotly_chart(fig_perf, use_container_width=True)
    
    # Sync to database option
    if st.button("💾 Sync Funds to Database"):
        db_config = {
            "host": st.secrets.get("MYSQL_HOST", "localhost"),
            "user": st.secrets.get("MYSQL_USER", "user"),
            "password": st.secrets.get("MYSQL_PASSWORD", "pass"),
            "database": st.secrets.get("MYSQL_DATABASE", "bentley_budget"),
        }
        
        BrokerConnectionManager.save_funds_to_db(funds, db_config)


def display_position_analysis():
    """Display position-level analysis across brokers"""
    st.subheader("📊 Position Analysis")
    
    st.info("🚧 Position-level analysis coming soon. This will show:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Cross-Broker Analytics:**
        - Consolidated position view
        - Duplicate holdings detection
        - Sector/industry exposure
        - Geographic diversification
        """)
    
    with col2:
        st.markdown("""
        **Performance Metrics:**
        - Unrealized gains/losses
        - Cost basis tracking
        - Return on investment
        - Tax lot optimization
        """)


def display_connection_health():
    """Display broker connection health monitoring"""
    st.subheader("🔍 Connection Health")
    
    connections = BrokerConnectionManager.get_demo_connections()
    
    # Health metrics
    col1, col2, col3 = st.columns(3)
    
    connected = sum(1 for c in connections if c.status == "Connected")
    pending = sum(1 for c in connections if c.status == "Pending")
    disconnected = sum(1 for c in connections if c.status not in ["Connected", "Pending"])
    
    col1.metric("🟢 Connected", connected)
    col2.metric("🟡 Pending", pending)
    col3.metric("🔴 Disconnected", disconnected)
    
    # Last sync status
    st.markdown("#### Sync Status")
    
    for conn in connections:
        with st.expander(f"{conn.broker_name} - {conn.account_number}"):
            col1, col2 = st.columns(2)
            
            col1.write(f"**Status:** {conn.status}")
            col1.write(f"**Last Sync:** {conn.last_sync.strftime('%Y-%m-%d %H:%M:%S')}")
            
            col2.write(f"**Balance:** ${conn.balance:,.2f}")
            col2.write(f"**Positions:** {conn.positions_count}")
            
            if conn.status == "Connected":
                if st.button(f"Refresh {conn.broker_name}", key=f"refresh_{conn.broker_name}"):
                    with st.spinner(f"Syncing {conn.broker_name}..."):
                        import time
                        time.sleep(1)  # Simulate API call
                        st.success(f"✅ {conn.broker_name} synced successfully")
                        st.rerun()
