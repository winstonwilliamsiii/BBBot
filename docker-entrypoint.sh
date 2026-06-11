#!/usr/bin/env bash
# docker-entrypoint.sh
# Launches the virtual display, MetaTrader 5 (headless via Wine),
# and the Python MT5 REST bridge in the foreground.
set -e

MT5_EXE="${WINEPREFIX}/drive_c/Program Files/MetaTrader 5/terminal64.exe"
DISPLAY_NUM="${DISPLAY:-:0}"
BRIDGE_LOG="/app/logs/mt5_bridge.log"
MT5_LOG="/app/logs/mt5_wine.log"

mkdir -p /app/logs

# ── 1. Start Xvfb (virtual framebuffer) ──────────────────────────────────────
echo "[entrypoint] Starting Xvfb on ${DISPLAY_NUM}"
Xvfb "${DISPLAY_NUM}" -screen 0 1024x768x24 -nolisten tcp &
XVFB_PID=$!
export DISPLAY="${DISPLAY_NUM}"
sleep 2  # give Xvfb time to initialise

# ── 2. Launch MT5 terminal headlessly via Wine ────────────────────────────────
# /portable  — run MT5 in portable mode (uses its own directory for data)
# /config:N  — suppress the first-run wizard (N = no broker wizard)
echo "[entrypoint] Starting MetaTrader 5 via Wine (headless)"
wine "${MT5_EXE}" /portable >> "${MT5_LOG}" 2>&1 &
MT5_PID=$!

# Allow MT5 to boot and connect before the REST bridge starts accepting calls
sleep 10

# ── 3. Verify MT5 is running ─────────────────────────────────────────────────
if ! kill -0 "${MT5_PID}" 2>/dev/null; then
    echo "[entrypoint] WARNING: MT5 process exited early — check ${MT5_LOG}"
fi

# ── 4. Start the Python REST bridge in the foreground ────────────────────────
echo "[entrypoint] Starting MT5 REST bridge"
exec python scripts/mt5_rest.py 2>&1 | tee -a "${BRIDGE_LOG}"
