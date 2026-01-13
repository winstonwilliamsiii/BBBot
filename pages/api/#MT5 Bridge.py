"""
MT5 Bridge - Local CLI Interface for MetaTrader 5
=================================================

LOCAL DEV: Called from Next.js using child_process.spawn()
PRODUCTION: Use mt5_rest_api_server.py (FastAPI/REST) instead

Usage from Node.js:
    const { spawn } = require('child_process');
    const mt5 = spawn('python', ['pages/api/#MT5 Bridge.py', 'EURUSD', '0.1', 'buy']);
    mt5.stdout.on('data', (data) => console.log(JSON.parse(data)));

Command line:
    python "pages/api/#MT5 Bridge.py" EURUSD 0.1 buy
    python "pages/api/#MT5 Bridge.py" EURUSD 0.1 sell
    python "pages/api/#MT5 Bridge.py" --account-info
    python "pages/api/#MT5 Bridge.py" --positions
"""

import MetaTrader5 as mt5
import json
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def error_response(message, code="ERROR"):
    """Return standardized error JSON"""
    return json.dumps({
        "success": False,
        "error": message,
        "code": code,
        "timestamp": datetime.now().isoformat()
    })

def success_response(data):
    """Return standardized success JSON"""
    return json.dumps({
        "success": True,
        "data": data,
        "timestamp": datetime.now().isoformat()
    })

def connect():
    """Initialize and login to MT5 with credentials from .env"""
    if not mt5.initialize():
        print(error_response("MT5 initialize failed", "INIT_FAILED"))
        sys.exit(1)
    
    # Try to login with credentials from .env
    mt5_user = os.getenv("MT5_USER")
    mt5_password = os.getenv("MT5_PASSWORD")
    mt5_host = os.getenv("MT5_HOST")
    
    if mt5_user and mt5_password and mt5_host:
        authorized = mt5.login(
            login=int(mt5_user),
            password=mt5_password,
            server=mt5_host
        )
        
        if not authorized:
            error = mt5.last_error()
            print(error_response(f"MT5 login failed: {error}", "LOGIN_FAILED"))
            mt5.shutdown()
            sys.exit(1)
    
    return True

def get_account_info():
    """Get MT5 account information"""
    connect()
    account = mt5.account_info()
    
    if account is None:
        print(error_response("Failed to get account info", "ACCOUNT_ERROR"))
        mt5.shutdown()
        sys.exit(1)
    
    result = {
        "broker": "mt5",
        "login": account.login,
        "server": account.server,
        "balance": account.balance,
        "equity": account.equity,
        "profit": account.profit,
        "margin": account.margin,
        "free_margin": account.margin_free,
        "margin_level": account.margin_level,
        "leverage": account.leverage,
        "currency": account.currency
    }
    
    mt5.shutdown()
    return result

def get_positions():
    """Get all open positions"""
    connect()
    positions = mt5.positions_get()
    
    if positions is None:
        print(error_response("Failed to get positions", "POSITIONS_ERROR"))
        mt5.shutdown()
        sys.exit(1)
    
    result = []
    for pos in positions:
        result.append({
            "ticket": pos.ticket,
            "symbol": pos.symbol,
            "type": "BUY" if pos.type == 0 else "SELL",
            "volume": pos.volume,
            "open_price": pos.price_open,
            "current_price": pos.price_current,
            "sl": pos.sl,
            "tp": pos.tp,
            "profit": pos.profit,
            "open_time": datetime.fromtimestamp(pos.time).isoformat()
        })
    
    mt5.shutdown()
    return {"positions": result, "count": len(result)}

def trade(symbol, qty, side, sl=None, tp=None):
    """
    Execute a market trade
    
    Args:
        symbol: Trading pair (e.g., EURUSD, GBPUSD)
        qty: Volume in lots (e.g., 0.1, 1.0)
        side: 'buy' or 'sell'
        sl: Stop loss price (optional)
        tp: Take profit price (optional)
    """
    connect()
    
    # Normalize symbol
    symbol = symbol.upper()
    
    # Get symbol info
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(error_response(f"Symbol {symbol} not found", "SYMBOL_NOT_FOUND"))
        mt5.shutdown()
        sys.exit(1)
    
    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            print(error_response(f"Failed to select symbol {symbol}", "SYMBOL_SELECT_FAILED"))
            mt5.shutdown()
            sys.exit(1)
    
    # Get current price
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(error_response(f"Failed to get tick for {symbol}", "TICK_ERROR"))
        mt5.shutdown()
        sys.exit(1)
    
    # Determine order type and price
    order_type = mt5.ORDER_TYPE_BUY if side.lower() == "buy" else mt5.ORDER_TYPE_SELL
    price = tick.ask if side.lower() == "buy" else tick.bid
    
    # Prepare request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(qty),
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": "BentleyBudgetBot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    # Add SL/TP if provided
    if sl:
        request["sl"] = float(sl)
    if tp:
        request["tp"] = float(tp)
    
    # Send order
    result = mt5.order_send(request)
    
    # Check result
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(error_response(
            f"Order failed: {result.comment}",
            f"TRADE_ERROR_{result.retcode}"
        ))
        mt5.shutdown()
        sys.exit(1)
    
    # Success response
    response_data = {
        "broker": "mt5",
        "orderId": result.order,
        "ticket": result.order,
        "symbol": symbol,
        "side": side.upper(),
        "volume": result.volume,
        "price": result.price,
        "retcode": result.retcode,
        "comment": result.comment,
        "request_id": result.request_id
    }
    
    mt5.shutdown()
    return response_data

if __name__ == "__main__":
    try:
        # Check arguments
        if len(sys.argv) < 2:
            print(error_response(
                "Usage: python mt5_bridge.py SYMBOL QTY SIDE [SL] [TP]\n"
                "   or: python mt5_bridge.py --account-info\n"
                "   or: python mt5_bridge.py --positions",
                "INVALID_ARGS"
            ))
            sys.exit(1)
        
        # Handle special commands
        if sys.argv[1] == "--account-info":
            result = get_account_info()
            print(success_response(result))
            sys.exit(0)
        
        if sys.argv[1] == "--positions":
            result = get_positions()
            print(success_response(result))
            sys.exit(0)
        
        # Handle trade
        if len(sys.argv) < 4:
            print(error_response("Trade requires: SYMBOL QTY SIDE", "INVALID_ARGS"))
            sys.exit(1)
        
        symbol = sys.argv[1]
        qty = sys.argv[2]
        side = sys.argv[3]
        sl = sys.argv[4] if len(sys.argv) > 4 else None
        tp = sys.argv[5] if len(sys.argv) > 5 else None
        
        result = trade(symbol, qty, side, sl, tp)
        print(success_response(result))
        
    except Exception as e:
        print(error_response(str(e), "EXCEPTION"))
        sys.exit(1)