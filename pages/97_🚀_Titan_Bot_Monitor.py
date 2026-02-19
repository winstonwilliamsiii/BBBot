"""
Titan Bot Monitor - Bentley Dashboard
"""

import pandas as pd
import streamlit as st

from frontend.utils.bot_fund_mapping import BOT_FUND_ALLOCATIONS
from frontend.utils.styling import apply_custom_styling, create_metric_card
from scripts.mansa_titan_bot import TitanBot, TitanConfig


st.set_page_config(
    page_title="Titan Bot Monitor",
    page_icon="🚀",
    layout="wide",
)

apply_custom_styling()

st.title("🚀 Stars Bot Monitor")


def _build_bot_status_rows() -> pd.DataFrame:
    bot_links = {
        "Titan": "pages/97_🚀_Titan_Bot_Monitor.py",
        "Rigel": "pages/08_🤖_Trading_Bot.py",
        "Dogon": "Not configured",
        "Orion": "Not configured",
    }

    rows = []
    for bot_name, fund_name in BOT_FUND_ALLOCATIONS.items():
        page_target = bot_links.get(bot_name, "Not configured")
        status = "linked" if page_target != "Not configured" else "pending"
        rows.append(
            {
                "Bot": bot_name,
                "Fund": fund_name,
                "Monitor": page_target,
                "Status": status,
            }
        )
    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def load_snapshot() -> dict:
    config = TitanConfig.from_env()
    bot = TitanBot(config)
    try:
        bot.ensure_database_tables()
    except (RuntimeError, OSError, ValueError):
        pass
    return bot.dashboard_snapshot()


snapshot = load_snapshot()

st.subheader("Bot/Fund Allocation")
allocation_df = _build_bot_status_rows()
st.dataframe(allocation_df, use_container_width=True)

link_col1, link_col2, link_col3, link_col4 = st.columns(4)
with link_col1:
    st.page_link(
        "pages/97_🚀_Titan_Bot_Monitor.py",
        label="Titan • Mansa_Tech",
        icon="🚀",
    )
with link_col2:
    st.page_link(
        "pages/08_🤖_Trading_Bot.py",
        label="Rigel • Mansa_FOREX",
        icon="🤖",
    )
with link_col3:
    st.caption("Dogon • Mansa_ETF (pending page)")
with link_col4:
    st.caption("Orion • Mansa_Minerals (pending page)")

st.markdown("---")
st.subheader("Titan Execution Metrics")

col1, col2, col3, col4 = st.columns(4)
with col1:
    create_metric_card("Total Trades", str(snapshot["total_trades"]))
with col2:
    create_metric_card("Submitted", str(snapshot["submitted_trades"]))
with col3:
    create_metric_card("Simulated", str(snapshot["simulated_trades"]))
with col4:
    create_metric_card("Blocked", str(snapshot["blocked_trades"]))

st.subheader("Service Health")
health_df = pd.DataFrame(snapshot.get("health", []))
if health_df.empty:
    st.info("No service health data available yet.")
else:
    st.dataframe(health_df, use_container_width=True)

st.subheader("Recent Titan Trades")
trades_df = snapshot.get("trades_df", pd.DataFrame())
if trades_df.empty:
    st.info("No Titan trades logged yet.")
else:
    view_df = trades_df.copy()
    view_df = view_df.sort_values("timestamp")
    st.dataframe(
        view_df[
            [
                "timestamp",
                "symbol",
                "side",
                "qty",
                "status",
                "prediction_probability",
            ]
        ],
        use_container_width=True,
    )

    chart_df = view_df[["timestamp", "prediction_probability"]].dropna()
    if not chart_df.empty:
        st.subheader("Prediction Probability Trend")
        st.line_chart(chart_df.set_index("timestamp"))
