"""
MT5 Bridge REST Server (Flask)
=============================

Lightweight REST wrapper around MT5Bridge.

Endpoints:
- GET  /health
- POST /connect
- POST /disconnect
- GET  /account
- GET  /positions
- GET  /position/<symbol>
- GET  /symbol/<symbol>
- GET  /market-data?symbol=EURUSD&timeframe=H1&limit=100
- GET  /price/<symbol>
- POST /trade
- POST /close
- POST /modify
"""

import json
import os
import threading
import sys
from pathlib import Path
from flask import Flask, request, Response

# Ensure project root is on sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pages.api.mt5_bridge import MT5Bridge, error_response

app = Flask(__name__)

_bridge_lock = threading.Lock()
_bridge_instance = None


def _get_bridge() -> MT5Bridge:
    global _bridge_instance
    with _bridge_lock:
        if _bridge_instance is None:
            _bridge_instance = MT5Bridge()
        return _bridge_instance


def _json_response(payload: str, status: int = 200) -> Response:
    return Response(payload, status=status, mimetype="application/json")


def _bridge_call(func, *args, **kwargs) -> Response:
    try:
        result = func(*args, **kwargs)
        data = json.loads(result)
        status = 200 if data.get("success", False) else 400
        return _json_response(result, status=status)
    except Exception as exc:
        return _json_response(error_response(str(exc)), status=500)


@app.get("/health")
def health() -> Response:
    payload = json.dumps({
        "status": "ok",
        "service": "mt5-bridge",
    })
    return _json_response(payload)


@app.post("/connect")
def connect() -> Response:
    body = request.get_json(silent=True) or {}
    bridge = _get_bridge()
    return _bridge_call(
        bridge.connect,
        body.get("user"),
        body.get("password"),
        body.get("host"),
    )


@app.post("/disconnect")
def disconnect() -> Response:
    bridge = _get_bridge()
    return _bridge_call(bridge.disconnect)


@app.get("/account")
def account() -> Response:
    bridge = _get_bridge()
    return _bridge_call(bridge.get_account_info)


@app.get("/positions")
def positions() -> Response:
    bridge = _get_bridge()
    return _bridge_call(bridge.get_positions)


@app.get("/position/<symbol>")
def position(symbol: str) -> Response:
    bridge = _get_bridge()
    return _bridge_call(bridge.get_position, symbol)


@app.get("/symbol/<symbol>")
def symbol_info(symbol: str) -> Response:
    bridge = _get_bridge()
    return _bridge_call(bridge.get_symbol_info, symbol)


@app.get("/market-data")
def market_data() -> Response:
    symbol = request.args.get("symbol")
    timeframe = request.args.get("timeframe", "H1")
    limit = int(request.args.get("limit", "100"))

    if not symbol:
        return _json_response(error_response("symbol is required"), status=400)

    bridge = _get_bridge()
    return _bridge_call(bridge.get_market_data, symbol, timeframe, limit)


@app.get("/price/<symbol>")
def price(symbol: str) -> Response:
    bridge = _get_bridge()
    return _bridge_call(bridge.get_current_price, symbol)


@app.post("/trade")
def trade() -> Response:
    body = request.get_json(silent=True) or {}

    required = ["symbol", "action", "volume"]
    missing = [key for key in required if key not in body]
    if missing:
        return _json_response(error_response(f"missing fields: {', '.join(missing)}"), status=400)

    bridge = _get_bridge()
    return _bridge_call(
        bridge.place_trade,
        body.get("symbol"),
        body.get("action"),
        float(body.get("volume")),
        float(body.get("price", 0.0)),
        float(body.get("stop_loss", 0.0)),
        float(body.get("take_profit", 0.0)),
        body.get("comment", ""),
    )


@app.post("/close")
def close_position() -> Response:
    body = request.get_json(silent=True) or {}
    symbol = body.get("symbol")
    if not symbol:
        return _json_response(error_response("symbol is required"), status=400)

    volume = float(body.get("volume", 0.0))
    bridge = _get_bridge()
    return _bridge_call(bridge.close_position, symbol, volume)


@app.post("/modify")
def modify_order() -> Response:
    body = request.get_json(silent=True) or {}
    ticket = body.get("ticket")
    if ticket is None:
        return _json_response(error_response("ticket is required"), status=400)

    stop_loss = float(body.get("stop_loss", 0.0))
    take_profit = float(body.get("take_profit", 0.0))

    bridge = _get_bridge()
    return _bridge_call(bridge.modify_order, int(ticket), stop_loss, take_profit)


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    app.run(host=host, port=port)
