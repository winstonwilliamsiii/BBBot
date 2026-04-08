"""
🤖 ML Trading Bot Dashboard
Monitor automated trading bot performance with Mean Reversion & Random Forest strategies
"""

import streamlit as st
import pandas as pd
import numpy as np
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import cache-busting reload function
try:
    from config_env import reload_env
    ENV_RELOAD_AVAILABLE = True
except ImportError:
    ENV_RELOAD_AVAILABLE = False

# Import custom styling
try:
    from frontend.styles.colors import COLOR_SCHEME
    from frontend.utils.styling import apply_custom_styling
    STYLING_AVAILABLE = True
except ImportError:
    STYLING_AVAILABLE = False
    COLOR_SCHEME = {
        'primary': '#06B6D4',
        'secondary': '#0F172A',
        'accent': '#FF8C00',
        'text': '#E6EEF8'
    }

try:
    from config.broker_mode_config import get_config as get_broker_mode_config
except ImportError:
    get_broker_mode_config = None

# Database connection
try:
    from sqlalchemy import create_engine
    import os
    
    # Reload env vars to ensure fresh database credentials
    if ENV_RELOAD_AVAILABLE:
        reload_env(force=False)
    
    MYSQL_CONFIG = {
        'host': 'localhost',
        'port': 3307,
        'user': 'root',
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': 'bentleybot'
    }
    
    connection_string = (
        f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@"
        f"{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
    )
    engine = create_engine(connection_string)
    DB_AVAILABLE = True
except Exception as e:
    DB_AVAILABLE = False
    st.error(f"Database connection failed: {e}")
    st.caption(
        "Titan launcher controls can still run without the legacy "
        "bot_status table."
    )

# Apply custom styling
if STYLING_AVAILABLE:
    apply_custom_styling()

# Page config
st.set_page_config(
    page_title="ML Trading Bot Dashboard",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    /* Gradient background matching home page */
    .stApp {
        background: linear-gradient(135deg, #0F172A 0%, #0B1220 100%);
        color: #E6EEF8;
    }
    
    /* Metric styling */
    [data-testid="stMetricLabel"] {
        color: rgba(230, 238, 248, 0.9) !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #E6EEF8 !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricDelta"] {
        color: rgba(230, 238, 248, 0.9) !important;
        font-size: 0.9rem !important;
        opacity: 0.9 !important;
    }
    
    /* Headers and text */
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: #E6EEF8 !important;
    }
    
    /* Status indicators */
    .status-active {
        color: #10B981;
        font-weight: bold;
    }
    
    .status-inactive {
        color: #EF4444;
        font-weight: bold;
    }
    
    /* Trade cards */
    .trade-card {{
        background: rgba(15, 23, 42, 0.6);
        border-left: 4px solid;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }}
    
    .trade-buy {{
        border-left-color: #10B981;
    }}
    
    .trade-sell {{
        border-left-color: #EF4444;
    }}

    /* DROPDOWN MENU OPTIONS - Ensure visibility */
    [data-baseweb="popover"],
    [data-baseweb="menu"] {{
        background-color: #0B1220 !important;
    }}
    
    [data-baseweb="menu"] li,
    [role="option"] {{
        background-color: #0B1220 !important;
        color: #E6EEF8 !important;
    }}
    
    [data-baseweb="menu"] li:hover,
    [role="option"]:hover {{
        background-color: rgba(6, 182, 212, 0.2) !important;
        color: #E6EEF8 !important;
    }}

    /* Sidebar styling - prevent color changes */
    [data-testid="stSidebar"] {{
        background-color: #0B1220 !important;
    }}
    
    [data-testid="stSidebar"] * {{
        color: #E6EEF8 !important;
    }}
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label {{
        color: #E6EEF8 !important;
        font-weight: 500 !important;
    }}
    </style>
""", unsafe_allow_html=True)

# Header
st.title("🤖 ML Trading Bot Dashboard")
st.markdown("**Automated Trading with Mean Reversion & Random Forest Strategies**")

# Bot status check
def _get_bot_trading_mode(bot_name: str) -> str:
    if get_broker_mode_config is None:
        return "paper"

    try:
        config = get_broker_mode_config()
        broker_name = config.get_bot_broker(bot_name)
        if not broker_name:
            return "paper"
        return config.get_broker_mode(broker_name)
    except Exception:
        return "paper"


def _set_bot_launch_preferences(
    bot_name: str,
    trading_mode: Literal["paper", "live"],
    active: bool,
) -> None:
    if get_broker_mode_config is None:
        return

    try:
        config = get_broker_mode_config()
        broker_name = config.get_bot_broker(bot_name)
        if broker_name:
            config.set_broker_mode(broker_name, trading_mode)
        config.set_bot_active(bot_name, active)
    except Exception:
        return


def _execute_bot_mode(
    bot_name: str,
    mode: str,
    trading_mode: str = "paper",
) -> dict:
    repo_root = Path(__file__).resolve().parents[2]
    launcher = repo_root / "start_bot_mode.ps1"

    if not launcher.exists():
        return {"ok": False, "output": f"Launcher not found: {launcher}"}

    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(launcher),
        "-Bot",
        bot_name,
        "-Mode",
        mode.upper(),
        "-TradingMode",
        trading_mode,
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        merged = "\n".join(
            part for part in [result.stdout.strip(), result.stderr.strip()] if part
        )
        return {"ok": result.returncode == 0, "output": merged or "No output"}
    except Exception as exc:
        return {"ok": False, "output": str(exc)}


def _latest_bot_mode_event() -> dict | None:
    repo_root = Path(__file__).resolve().parents[2]
    latest_path = repo_root / "logs" / "last_bot_mode_event.json"
    if not latest_path.exists():
        return None

    try:
        with latest_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
            if isinstance(payload, dict):
                return payload
    except Exception:
        return None

    return None


def get_bot_status(bot_name: str = "Titan"):
    """Resolve launcher-first status without relying on bot_status."""
    strategy = "Mansa Tech - Titan Bot"
    trading_mode = _get_bot_trading_mode(bot_name)
    latest_event = _latest_bot_mode_event()

    if (
        latest_event
        and str(latest_event.get("bot", "")).lower() == bot_name.lower()
    ):
        last_mode = str(latest_event.get("mode", "")).lower()
        launcher_status = str(latest_event.get("status", "unknown")).lower()
        if (
            last_mode == "on"
            and launcher_status in {"ready", "placeholder", "warning"}
        ):
            status = "active"
        elif last_mode == "off":
            status = "inactive"
        else:
            status = launcher_status or "unknown"

        return {
            "status": status,
            "strategy": strategy,
            "timestamp": latest_event.get("timestamp"),
            "note": latest_event.get("note", ""),
            "trading_mode": latest_event.get("trading_mode", trading_mode),
        }

    active_flag = None
    if get_broker_mode_config is not None:
        try:
            config = get_broker_mode_config()
            active_flag = config.get_bot_active(bot_name)
        except Exception:
            active_flag = None

    if active_flag is None:
        status = "unknown"
    else:
        status = "active" if active_flag else "inactive"

    return {
        "status": status,
        "strategy": strategy,
        "timestamp": None,
        "note": "Launcher event not available yet",
        "trading_mode": trading_mode,
    }


def _build_quick_start_command(bot_name: str, mode: str) -> str:
    return (
        "powershell -ExecutionPolicy Bypass -File "
        f"./start_bot_mode.ps1 -Bot {bot_name} -Mode {mode.upper()}"
    )


def _render_sidebar_launch_output() -> None:
    selected_output = st.session_state.get("selected_bot_launch_output")
    if selected_output:
        with st.expander("Last Command Output", expanded=False):
            st.code(selected_output, language="text")


def _render_sidebar_launch_command() -> None:
    selected_cmd = st.session_state.get("selected_bot_launch_command")
    if selected_cmd:
        st.code(selected_cmd, language="powershell")


def _legacy_db_bot_status():
    """Deprecated legacy DB status lookup retained only for reference."""
    try:
        # Check Airflow DAG status (simplified)
        query = """
            SELECT status, strategy, timestamp
            FROM bot_status
            ORDER BY timestamp DESC
            LIMIT 1
        """
        status_df = pd.read_sql(query, engine)
        
        if not status_df.empty:
            return status_df.iloc[0].to_dict()
        else:
            return {'status': 'unknown', 'strategy': 'N/A', 'timestamp': None}
    except:
        return {'status': 'unknown', 'strategy': 'N/A', 'timestamp': None}


# Load data functions
@st.cache_data(ttl=60)
def load_recent_trades(days=7):
    """Load recent trade history"""
    if not DB_AVAILABLE:
        return pd.DataFrame()
    
    query = f"""
        SELECT ticker, action, shares, price, value, timestamp, status, strategy
        FROM trades_history
        WHERE timestamp >= DATE_SUB(NOW(), INTERVAL {days} DAY)
        ORDER BY timestamp DESC
    """
    
    try:
        return pd.read_sql(query, engine, parse_dates=['timestamp'])
    except:
        return pd.DataFrame()


@st.cache_data(ttl=60)
def load_performance_metrics(days=30):
    """Load performance metrics"""
    if not DB_AVAILABLE:
        return pd.DataFrame()
    
    query = f"""
        SELECT date, total_trades, buy_trades, sell_trades, total_value, strategy
        FROM performance_metrics
        WHERE date >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
        ORDER BY date DESC
    """
    
    try:
        return pd.read_sql(query, engine, parse_dates=['date'])
    except:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_active_signals():
    """Load active trading signals"""
    if not DB_AVAILABLE:
        return pd.DataFrame()
    
    query = """
        SELECT ticker, signal, price, timestamp, strategy
        FROM trading_signals
        WHERE DATE(timestamp) = CURDATE()
        ORDER BY timestamp DESC
    """
    
    try:
        return pd.read_sql(query, engine, parse_dates=['timestamp'])
    except:
        return pd.DataFrame()


# Sidebar controls
st.sidebar.header("🎛️ Bot Controls")

# Bot status
bot_status = get_bot_status()
status_color = "🟢" if bot_status['status'] == 'active' else "🟡" if bot_status['status'] == 'unknown' else "🔴"
st.sidebar.markdown(f"**Status:** {status_color} {bot_status['status'].upper()}")
st.sidebar.markdown(f"**Strategy:** {bot_status.get('strategy', 'N/A').replace('_', ' ').title()}")
st.sidebar.caption(
    f"Trading Mode: {str(bot_status.get('trading_mode', 'paper')).upper()}"
)
if bot_status.get("note"):
    st.sidebar.caption(str(bot_status["note"]))

# Manual controls
st.sidebar.markdown("---")
st.sidebar.subheader("Titan Controls")

titan_sidebar_mode = st.sidebar.selectbox(
    "Titan Trading Mode",
    options=["paper", "live"],
    index=0 if str(bot_status.get("trading_mode", "paper")) == "paper" else 1,
    key="sidebar_titan_trading_mode",
)

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("▶️ Titan ON", use_container_width=True):
        _set_bot_launch_preferences("Titan", titan_sidebar_mode, True)
        with st.spinner("Running Titan ON..."):
            execution = _execute_bot_mode("Titan", "on", titan_sidebar_mode)
        st.session_state["selected_bot_launch_output"] = execution["output"]
        st.session_state["selected_bot_launch_command"] = (
            _build_quick_start_command("Titan", "on")
            + f" -TradingMode {titan_sidebar_mode}"
        )
        if execution["ok"]:
            st.sidebar.success("Titan ON command completed.")
        else:
            st.sidebar.error("Titan ON command failed.")
        st.rerun()

with col2:
    if st.button("⏸️ Titan OFF", use_container_width=True):
        _set_bot_launch_preferences("Titan", titan_sidebar_mode, False)
        with st.spinner("Running Titan OFF..."):
            execution = _execute_bot_mode("Titan", "off", titan_sidebar_mode)
        st.session_state["selected_bot_launch_output"] = execution["output"]
        st.session_state["selected_bot_launch_command"] = (
            _build_quick_start_command("Titan", "off")
            + f" -TradingMode {titan_sidebar_mode}"
        )
        if execution["ok"]:
            st.sidebar.success("Titan OFF command completed.")
        else:
            st.sidebar.error("Titan OFF command failed.")
        st.rerun()

_render_sidebar_launch_command()
_render_sidebar_launch_output()

# Refresh data
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Date range selector
st.sidebar.markdown("---")
date_range = st.sidebar.selectbox(
    "Time Period",
    ["Today", "Last 7 Days", "Last 30 Days", "All Time"]
)

days_map = {
    "Today": 1,
    "Last 7 Days": 7,
    "Last 30 Days": 30,
    "All Time": 365
}
selected_days = days_map[date_range]

# Main dashboard
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview", 
    "📈 Performance", 
    "🎯 Active Signals", 
    "📜 Trade History"
])

# TAB 1: Overview
with tab1:
    # Key metrics
    trades_df = load_recent_trades(selected_days)
    perf_df = load_performance_metrics(selected_days)
    
    if not trades_df.empty:
        total_trades = len(trades_df)
        buy_trades = len(trades_df[trades_df['action'] == 'BUY'])
        sell_trades = len(trades_df[trades_df['action'] == 'SELL'])
        total_value = trades_df['value'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Trades", f"{total_trades}", f"{date_range}")
        
        with col2:
            st.metric("Buy Orders", f"{buy_trades}", f"{buy_trades / total_trades * 100:.0f}%" if total_trades > 0 else "0%")
        
        with col3:
            st.metric("Sell Orders", f"{sell_trades}", f"{sell_trades / total_trades * 100:.0f}%" if total_trades > 0 else "0%")
        
        with col4:
            st.metric("Total Volume", f"${total_value:,.0f}", None)
        
        # Recent activity chart
        st.markdown("---")
        st.subheader("Recent Trading Activity")
        
        if not perf_df.empty:
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Daily Trade Count', 'Daily Trade Volume'),
                vertical_spacing=0.15
            )
            
            # Trade count
            fig.add_trace(
                go.Bar(
                    x=perf_df['date'],
                    y=perf_df['total_trades'],
                    name='Total Trades',
                    marker_color=COLOR_SCHEME['primary']
                ),
                row=1, col=1
            )
            
            # Trade volume
            fig.add_trace(
                go.Bar(
                    x=perf_df['date'],
                    y=perf_df['total_value'],
                    name='Trade Volume',
                    marker_color=COLOR_SCHEME['accent']
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                height=500,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color=COLOR_SCHEME['text'])
            )
            
            fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info(f"No trading activity in {date_range.lower()}")

# TAB 2: Performance
with tab2:
    st.subheader("Strategy Performance Comparison")
    
    if not perf_df.empty:
        # Group by strategy
        strategy_perf = perf_df.groupby('strategy').agg({
            'total_trades': 'sum',
            'buy_trades': 'sum',
            'sell_trades': 'sum',
            'total_value': 'sum'
        }).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Mean Reversion Strategy**")
            mr_data = strategy_perf[strategy_perf['strategy'] == 'mean_reversion']
            if not mr_data.empty:
                st.metric("Total Trades", f"{int(mr_data['total_trades'].iloc[0])}")
                st.metric("Win Rate", "N/A")  # TODO: Calculate from trade results
                st.metric("Total Volume", f"${mr_data['total_value'].iloc[0]:,.0f}")
            else:
                st.info("No Mean Reversion data")
        
        with col2:
            st.markdown("**Random Forest Strategy**")
            rf_data = strategy_perf[strategy_perf['strategy'] == 'random_forest']
            if not rf_data.empty:
                st.metric("Total Trades", f"{int(rf_data['total_trades'].iloc[0])}")
                st.metric("Win Rate", "N/A")  # TODO: Calculate from trade results
                st.metric("Total Volume", f"${rf_data['total_value'].iloc[0]:,.0f}")
            else:
                st.info("No Random Forest data")
        
        # Performance chart
        st.markdown("---")
        fig = go.Figure()
        
        for strategy in strategy_perf['strategy'].unique():
            strategy_data = perf_df[perf_df['strategy'] == strategy]
            fig.add_trace(go.Scatter(
                x=strategy_data['date'],
                y=strategy_data['total_value'].cumsum(),
                mode='lines+markers',
                name=strategy.replace('_', ' ').title(),
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title="Cumulative Trade Volume by Strategy",
            xaxis_title="Date",
            yaxis_title="Cumulative Volume ($)",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLOR_SCHEME['text']),
            hovermode='x unified'
        )
        
        fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
        fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
        
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No performance data available")

# TAB 3: Active Signals
with tab3:
    st.subheader("Today's Trading Signals")
    
    signals_df = load_active_signals()
    
    if not signals_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🟢 Buy Signals**")
            buy_signals = signals_df[signals_df['signal'] == 1]
            
            if not buy_signals.empty:
                for _, signal in buy_signals.iterrows():
                    st.markdown(f"""
                        <div class="trade-card trade-buy">
                            <strong>{signal['ticker']}</strong><br>
                            Price: ${signal['price']:.2f}<br>
                            Time: {signal['timestamp'].strftime('%H:%M:%S')}<br>
                            Strategy: {signal['strategy'].replace('_', ' ').title()}
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No buy signals today")
        
        with col2:
            st.markdown("**🔴 Sell Signals**")
            sell_signals = signals_df[signals_df['signal'] == -1]
            
            if not sell_signals.empty:
                for _, signal in sell_signals.iterrows():
                    st.markdown(f"""
                        <div class="trade-card trade-sell">
                            <strong>{signal['ticker']}</strong><br>
                            Price: ${signal['price']:.2f}<br>
                            Time: {signal['timestamp'].strftime('%H:%M:%S')}<br>
                            Strategy: {signal['strategy'].replace('_', ' ').title()}
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No sell signals today")
    
    else:
        st.info("No active signals today")

# TAB 4: Trade History
with tab4:
    st.subheader("Recent Trade History")
    
    if not trades_df.empty:
        # Format dataframe
        display_df = trades_df.copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_df['value'] = display_df['value'].apply(lambda x: f"${x:,.2f}")
        display_df['price'] = display_df['price'].apply(lambda x: f"${x:.2f}")
        
        # Color code actions
        def color_action(val):
            color = '#10B981' if val == 'BUY' else '#EF4444'
            return f'color: {color}; font-weight: bold'
        
        styled_df = display_df.style.applymap(
            color_action,
            subset=['action']
        )
        
        st.dataframe(
            display_df[['timestamp', 'ticker', 'action', 'shares', 'price', 'value', 'status', 'strategy']],
            use_container_width=True,
            hide_index=True
        )
        
        # Export option
        csv = trades_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Trade History (CSV)",
            data=csv,
            file_name=f"trade_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    else:
        st.info(f"No trade history in {date_range.lower()}")

# Footer
st.markdown("---")
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("⚠️ **Disclaimer:** This is an automated trading bot. Past performance does not guarantee future results.")
