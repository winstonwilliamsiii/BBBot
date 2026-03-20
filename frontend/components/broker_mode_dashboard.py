"""
Broker Mode & Bot Control Dashboard Component

Streamlit UI for:
1. Global Live/Paper mode switch
2. Per-broker mode overrides
3. Bot activity status and control
4. Bot-broker mapping visualization
"""

import streamlit as st
import pandas as pd
from typing import Dict, List
import logging
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

# Add project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from config.broker_mode_config import get_config, BOT_BROKER_MAPPING, SUPPORTED_BROKERS
    from frontend.utils.broker_mode_resolver import get_effective_mode, log_mode_switch
except ImportError as e:
    logger.error(f"Import error in broker mode dashboard: {e}")
    raise


def render_global_mode_controls():
    """Render global Live/Paper mode switch."""
    st.subheader("🌍 Global Trading Mode")

    config = get_config()
    current_global = config.get_global_mode()

    col1, col2 = st.columns([2, 1])

    with col1:
        new_mode = st.radio(
            "Select global trading mode:",
            options=["paper", "live"],
            index=0 if current_global == "paper" else 1,
            format_func=lambda x: f"📄 PAPER (Demo/Testing)" if x == "paper" else "🔴 LIVE (Real Money)",
            key="global_mode_radio",
        )

    with col2:
        st.metric(
            "Current",
            current_global.upper(),
            delta=f"{'Testing' if current_global == 'paper' else 'Real Trading'}",
        )

    if new_mode != current_global:
        if st.button(
            f"Apply Global Mode → {new_mode.upper()}",
            type="primary",
            use_container_width=True,
        ):
            try:
                config.set_global_mode(new_mode)
                log_mode_switch("GLOBAL", new_mode)
                st.success(f"✅ Global mode changed to {new_mode.upper()}")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error changing mode: {e}")


def render_broker_mode_overrides():
    """Render per-broker mode overrides."""
    st.subheader("🏦 Broker-Specific Overrides")

    config = get_config()
    global_mode = config.get_global_mode()

    st.info(
        f"Current global mode: **{global_mode.upper()}**. "
        "Set broker-specific overrides below to use different mode for specific broker."
    )

    cols = st.columns(len(SUPPORTED_BROKERS))

    for idx, broker in enumerate(SUPPORTED_BROKERS):
        with cols[idx]:
            current_mode = config.get_broker_mode(broker)
            effective_mode = current_mode == "paper"

            # Display current mode with badge
            badge = "📄 PAPER" if effective_mode else "🔴 LIVE"
            st.markdown(f"**{broker.upper()}** - {badge}")

            # Toggle button
            if st.button(
                f"Switch to {'LIVE' if effective_mode else 'PAPER'}",
                key=f"broker_mode_{broker}",
                use_container_width=True,
            ):
                new_mode = "live" if effective_mode else "paper"
                try:
                    config.set_broker_mode(broker, new_mode)
                    log_mode_switch(broker, new_mode)
                    st.success(f"✅ {broker.upper()} → {new_mode.upper()}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


def render_bot_status_table():
    """Render bot activity status table."""
    st.subheader("🤖 Bot Status & Activity")

    config = get_config()

    # Build status dataframe
    bots_data = []
    for bot_name, bot_broker in BOT_BROKER_MAPPING.items():
        active = config.is_bot_active(bot_name)
        mode = config.get_broker_mode(bot_broker)
        bots_data.append(
            {
                "Bot": bot_name,
                "Status": "🟢 ACTIVE" if active else "⚫ INACTIVE",
                "Broker": bot_broker.upper(),
                "Mode": f"{'📄 Paper' if mode == 'paper' else '🔴 Live'}",
                "Active": active,
            }
        )

    df = pd.DataFrame(bots_data)

    # Display as table
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Active bots summary
    active_count = sum(1 for b in bots_data if b["Active"])
    st.metric(f"Active Bots", f"{active_count}/{len(bots_data)}")


def render_bot_control_panel():
    """Render bot start/stop controls."""
    st.subheader("⚙️ Bot Control Panel")

    config = get_config()

    st.info(
        "💡 Tip: Stop/start bots without restarting the app. "
        "This controls the bot registry but does not affect running processes."
    )

    # Create two columns: Active and Inactive
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🟢 Active Bots")
        active_bots = [
            name
            for name, broker in BOT_BROKER_MAPPING.items()
            if config.is_bot_active(name)
        ]

        if active_bots:
            for bot in active_bots:
                broker = BOT_BROKER_MAPPING[bot]
                mode = config.get_broker_mode(broker)
                col_a, col_b = st.columns([2, 1])

                with col_a:
                    st.write(f"🤖 **{bot}** ({broker.upper()}/{mode.upper()})")

                with col_b:
                    if st.button("⏹️ Stop", key=f"stop_{bot}", use_container_width=True):
                        try:
                            config.set_bot_active(bot, False)
                            st.success(f"Stopped {bot}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        else:
            st.write("No active bots")

    with col2:
        st.markdown("### ⚫ Inactive Bots")
        inactive_bots = [
            name
            for name, broker in BOT_BROKER_MAPPING.items()
            if not config.is_bot_active(name)
        ]

        if inactive_bots:
            for bot in inactive_bots:
                broker = BOT_BROKER_MAPPING[bot]
                mode = config.get_broker_mode(broker)
                col_a, col_b = st.columns([2, 1])

                with col_a:
                    st.write(f"🤖 {bot} ({broker.upper()}/{mode.upper()})")

                with col_b:
                    if st.button("▶️ Start", key=f"start_{bot}", use_container_width=True):
                        try:
                            config.set_bot_active(bot, True)
                            st.success(f"Started {bot}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        else:
            st.write("All bots are active")


def render_mode_config_file_viewer():
    """Render raw config file viewer for debugging."""
    st.subheader("📋 Config File Viewer")

    config = get_config()

    if st.checkbox("Show raw configuration (debug)"):
        st.json(config.get_config_dict())

        # Download button
        import json

        config_json = json.dumps(config.get_config_dict(), indent=2)
        st.download_button(
            label="📥 Download config.json",
            data=config_json,
            file_name="broker_modes.json",
            mime="application/json",
        )


def render_mode_environment_vars():
    """Display current environment variable overrides."""
    st.subheader("🔐 Environment Variable Overrides")

    import os

    st.info("Set these environment variables to override broker modes at runtime:")

    env_vars_status = []
    for broker in SUPPORTED_BROKERS:
        env_var = f"{broker.upper()}_MODE"
        value = os.getenv(env_var)
        env_vars_status.append(
            {
                "Variable": env_var,
                "Set": "✅ Yes" if value else "❌ No",
                "Value": value or "(not set)",
            }
        )

    df = pd.DataFrame(env_vars_status)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.code(
        """
# Example: Set Alpaca to LIVE mode temporarily
$env:ALPACA_MODE = "live"

# Example: Set MT5 to PAPER mode
$env:MT5_MODE = "paper"

# Check current setting
$env:ALPACA_MODE
    """.strip(),
        language="powershell",
    )


def render_broker_mode_dashboard():
    """Main renderer - combines all sections."""
    st.set_page_config(page_title="Broker Mode Control", layout="wide")

    st.title("🎮 Broker Mode & Bot Control Dashboard")

    st.markdown(
        """
    Monitor and control broker trading modes and bot activity from one place.
    
    - **Global Mode**: Default for all brokers when creating new connections
    - **Broker Overrides**: Different mode per broker for mixed paper/live experiments
    - **Bot Control**: Start/stop bots without restarting the app
    - **ML Experiments**: Run experiments on Paper while live trading on other accounts
    """
    )

    st.divider()

    # Main controls
    render_global_mode_controls()
    st.divider()

    render_broker_mode_overrides()
    st.divider()

    render_bot_status_table()
    st.divider()

    render_bot_control_panel()
    st.divider()

    render_mode_environment_vars()
    st.divider()

    render_mode_config_file_viewer()
