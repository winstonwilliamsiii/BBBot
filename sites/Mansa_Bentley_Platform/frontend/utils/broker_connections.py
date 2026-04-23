"""
Broker Connections Display Module
Shows connected broker accounts and fund positions for authorized users
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List


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


class BrokerConnectionManager:
    """Manages broker connections and data fetching"""
    
    @staticmethod
    def get_demo_connections() -> List[BrokerConnection]:
        """Get demo broker connections for testing"""
        return [
            BrokerConnection(
                broker_name="Alpaca",
                account_number="****1122",
                status="Connected",
                last_sync=datetime.now(),
                balance=124500.25,
                positions_count=11,
            ),
            BrokerConnection(
                broker_name="Interactive Brokers (IBKR)",
                account_number="****9012",
                status="Connected",
                last_sync=datetime.now(),
                balance=87650.25,
                positions_count=15,
            ),
            BrokerConnection(
                broker_name="MT5 (FTMO)",
                account_number="****3456",
                status="Connected",
                last_sync=datetime.now(),
                balance=42380.75,
                positions_count=8,
            ),
            BrokerConnection(
                broker_name="MT5 (Axi)",
                account_number="****7890",
                status="Connected",
                last_sync=datetime.now(),
                balance=35200.00,
                positions_count=5,
            ),
            BrokerConnection(
                broker_name="Zenit Prop Connector",
                account_number="****2345",
                status="Pending",
                last_sync=datetime.now(),
                balance=0.00,
                positions_count=0,
            ),
        ]
    
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
