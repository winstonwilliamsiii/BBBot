"""
MT5 Bridge REST Server (FastAPI)
================================

Lightweight REST wrapper around MT5Bridge.

Endpoints:
- GET  /health
- POST /connect
- POST /disconnect
- GET  /account
- GET  /positions
- GET  /position/{symbol}
- GET  /symbol/{symbol}
- GET  /market-data?symbol=EURUSD&timeframe=H1&limit=100
- GET  /price/{symbol}
- POST /trade
- POST /close
- POST /modify
"""

import json
import os
import threading
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
import uvicorn

# Ensure project root is on sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pages.api.mt5_bridge import MT5Bridge, error_response

app = FastAPI(title="MT5 Bridge REST API", version="1.0.0")

_bridge_lock = threading.Lock()
_bridge_instance = None


class ConnectBody(BaseModel):
    user: Optional[str] = None
    password: Optional[str] = None
    host: Optional[str] = None


class TradeBody(BaseModel):
    symbol: str
    action: str
    volume: float
    price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    comment: str = ""


class CloseBody(BaseModel):
    symbol: str
    volume: float = 0.0


class ModifyBody(BaseModel):
    ticket: int
    stop_loss: float = 0.0
    take_profit: float = 0.0


def _get_bridge() -> MT5Bridge:
    global _bridge_instance
    with _bridge_lock:
        if _bridge_instance is None:
            _bridge_instance = MT5Bridge()
        return _bridge_instance


def _json_response(payload: str, status: int = 200) -> Response:
    return Response(content=payload, status_code=status, media_type="application/json")


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
def connect(body: ConnectBody) -> Response:
    bridge = _get_bridge()
    return _bridge_call(bridge.connect, body.user, body.password, body.host)


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


@app.get("/position/{symbol}")
def position(symbol: str) -> Response:
    bridge = _get_bridge()
    return _bridge_call(bridge.get_position, symbol)


@app.get("/symbol/{symbol}")
def symbol_info(symbol: str) -> Response:
    bridge = _get_bridge()
    return _bridge_call(bridge.get_symbol_info, symbol)


@app.get("/market-data")
def market_data(
    symbol: str = Query(..., description="Trading symbol, e.g. EURUSD"),
    timeframe: str = Query("H1", description="MT5 timeframe string"),
    limit: int = Query(100, description="Number of bars to fetch"),
) -> Response:
    bridge = _get_bridge()
    return _bridge_call(bridge.get_market_data, symbol, timeframe, limit)


@app.get("/price/{symbol}")
def price(symbol: str) -> Response:
    bridge = _get_bridge()
    return _bridge_call(bridge.get_current_price, symbol)


@app.post("/trade")
def trade(body: TradeBody) -> Response:
    bridge = _get_bridge()
    return _bridge_call(
        bridge.place_trade,
        body.symbol,
        body.action,
        body.volume,
        body.price,
        body.stop_loss,
        body.take_profit,
        body.comment,
    )


@app.post("/close")
def close_position(body: CloseBody) -> Response:
    bridge = _get_bridge()
    return _bridge_call(bridge.close_position, body.symbol, body.volume)


@app.post("/modify")
def modify_order(body: ModifyBody) -> Response:
    bridge = _get_bridge()
    return _bridge_call(bridge.modify_order, body.ticket, body.stop_loss, body.take_profit)


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host=host, port=port)
