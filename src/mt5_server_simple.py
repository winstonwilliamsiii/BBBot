"""
Simple MT5 REST API Server - FastAPI
Runs on port 8002 (8000 is used by Airbyte)
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import MetaTrader5 as mt5
from datetime import datetime
import logging
import os
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MT5 Simple REST API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

mt5_connected = False


@app.get("/Health")
def health():
    initialized = mt5.initialize()
    status = "healthy" if initialized else "degraded"
    return {
        "status": status,
        "mt5_initialized": initialized,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/Connect")
def connect(
    user: str = Query(...),
    password: str = Query(...),
    host: str = Query(...),
):
    global mt5_connected
    if not mt5.initialize():
        raise HTTPException(
            status_code=500,
            detail=f"MT5 initialization failed: {mt5.last_error()}",
        )
    authorized = mt5.login(login=int(user), password=password, server=host)
    if authorized:
        mt5_connected = True
        account = mt5.account_info()
        return {
            "success": True,
            "connected": True,
            "account": {
                "login": account.login,
                "balance": account.balance,
                "equity": account.equity,
            },
        }
    raise HTTPException(
        status_code=401, detail=f"Login failed: {mt5.last_error()}"
    )


@app.get("/AccountInfo")
def account_info():
    if not mt5_connected:
        raise HTTPException(status_code=401, detail="Not connected")
    account = mt5.account_info()
    if not account:
        raise HTTPException(status_code=500, detail="Failed to get account info")
    return {
        "login": account.login,
        "balance": account.balance,
        "equity": account.equity,
        "profit": account.profit,
        "margin": account.margin,
        "free_margin": account.margin_free,
    }


@app.get("/Positions")
def positions():
    if not mt5_connected:
        raise HTTPException(status_code=401, detail="Not connected")
    pos_list = mt5.positions_get()
    if not pos_list:
        return {"positions": []}
    result = [
        {
            "ticket": pos.ticket,
            "symbol": pos.symbol,
            "type": "BUY" if pos.type == 0 else "SELL",
            "volume": pos.volume,
            "open_price": pos.price_open,
            "current_price": pos.price_current,
            "profit": pos.profit,
        }
        for pos in pos_list
    ]
    return {"positions": result}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8002"))
    print(f"\n🚀 MT5 REST API Server starting on http://localhost:{port}")
    print("📡 Endpoints: /Health, /Connect, /AccountInfo, /Positions\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
