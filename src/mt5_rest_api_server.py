"""
Simple MT5 REST API Server
Provides REST endpoints for MetaTrader 5 trading

Requirements:
- MetaTrader5 package
- Flask for REST API
- Active MT5 terminal running

Installation:
pip install MetaTrader5 flask flask-cors

Usage:
python mt5_rest_api_server.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import MetaTrader5 as mt5
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global connection state
mt5_connected = False
mt5_account_info = {}


@app.route('/Health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'mt5_initialized': mt5_connected,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/Connect', methods=['GET'])
def connect():
    """
    Connect to MT5 account
    Query params: user, password, host, port
    """
    global mt5_connected, mt5_account_info
    
    try:
        user = request.args.get('user')
        password = request.args.get('password')
        host = request.args.get('host')
        port = int(request.args.get('port', 443))
        
        if not all([user, password, host]):
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400
        
        # Initialize MT5 with timeout so API doesn't hang indefinitely.
        # Use MT5_PATH to target a specific terminal install (fixes IPC when multiple installs exist).
        mt5_path = os.getenv('MT5_PATH') or None
        if not mt5.initialize(path=mt5_path, timeout=10000):
            error = mt5.last_error()
            return jsonify({
                'success': False,
                'error': f'MT5 initialization failed: {error}'
            }), 500
        
        # Login to account
        authorized = mt5.login(
            login=int(user),
            password=password,
            server=host,
            timeout=10000,
        )
        
        if authorized:
            mt5_connected = True
            account = mt5.account_info()
            mt5_account_info = {
                'login': account.login,
                'server': account.server,
                'balance': account.balance,
                'equity': account.equity,
                'margin': account.margin,
                'free_margin': account.margin_free
            }
            
            logger.info(f"Connected to MT5 account {user}")
            
            return jsonify({
                'success': True,
                'connected': True,
                'account': mt5_account_info
            })
        else:
            error = mt5.last_error()
            return jsonify({
                'success': False,
                'error': f'Login failed: {error}'
            }), 401
            
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/Disconnect', methods=['GET'])
def disconnect():
    """Disconnect from MT5"""
    global mt5_connected
    
    try:
        mt5.shutdown()
        mt5_connected = False
        logger.info("Disconnected from MT5")
        
        return jsonify({
            'success': True,
            'message': 'Disconnected successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/AccountInfo', methods=['GET'])
def account_info():
    """Get account information"""
    if not mt5_connected:
        return jsonify({'error': 'Not connected'}), 401
    
    try:
        account = mt5.account_info()
        
        if account is None:
            return jsonify({'error': 'Failed to get account info'}), 500
        
        return jsonify({
            'login': account.login,
            'server': account.server,
            'name': account.name,
            'balance': account.balance,
            'equity': account.equity,
            'profit': account.profit,
            'margin': account.margin,
            'free_margin': account.margin_free,
            'margin_level': account.margin_level,
            'leverage': account.leverage,
            'currency': account.currency
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/Positions', methods=['GET'])
def get_positions():
    """Get all open positions"""
    if not mt5_connected:
        return jsonify({'error': 'Not connected'}), 401
    
    try:
        positions = mt5.positions_get()
        
        if positions is None:
            return jsonify({'positions': []})
        
        result = []
        for pos in positions:
            result.append({
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'type': 'BUY' if pos.type == 0 else 'SELL',
                'volume': pos.volume,
                'open_price': pos.price_open,
                'current_price': pos.price_current,
                'sl': pos.sl,
                'tp': pos.tp,
                'profit': pos.profit,
                'open_time': datetime.fromtimestamp(pos.time).isoformat()
            })
        
        return jsonify({'positions': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/MarketData', methods=['GET'])
def market_data():
    """Get market data (OHLCV bars)"""
    if not mt5_connected:
        return jsonify({'error': 'Not connected'}), 401
    
    try:
        symbol = request.args.get('symbol')
        timeframe = request.args.get('timeframe', 'H1')
        count = int(request.args.get('count', 100))
        
        # Map timeframe strings to MT5 constants
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1
        }
        
        tf = timeframe_map.get(timeframe, mt5.TIMEFRAME_H1)
        
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        
        if rates is None:
            return jsonify({'error': f'Failed to get data for {symbol}'}), 500
        
        bars = []
        for rate in rates:
            bars.append({
                'time': datetime.fromtimestamp(rate['time']).isoformat(),
                'open': float(rate['open']),
                'high': float(rate['high']),
                'low': float(rate['low']),
                'close': float(rate['close']),
                'volume': int(rate['tick_volume'])
            })
        
        return jsonify({'bars': bars, 'symbol': symbol, 'timeframe': timeframe})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/SymbolInfo', methods=['GET'])
def symbol_info():
    """Get symbol information"""
    if not mt5_connected:
        return jsonify({'error': 'Not connected'}), 401
    
    try:
        symbol = request.args.get('symbol')
        
        tick = mt5.symbol_info_tick(symbol)
        info = mt5.symbol_info(symbol)
        
        if tick is None or info is None:
            return jsonify({'error': f'Symbol {symbol} not found'}), 404
        
        return jsonify({
            'symbol': symbol,
            'bid': tick.bid,
            'ask': tick.ask,
            'last': tick.last,
            'volume': tick.volume,
            'spread': info.spread,
            'point': info.point,
            'digits': info.digits
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/PlaceTrade', methods=['POST'])
def place_trade():
    """Place a trade order"""
    if not mt5_connected:
        return jsonify({'error': 'Not connected'}), 401
    
    try:
        data = request.json
        
        symbol = data.get('symbol')
        order_type = data.get('type', 'BUY')
        volume = float(data.get('volume'))
        price = data.get('price')
        sl = data.get('sl', 0.0)
        tp = data.get('tp', 0.0)
        comment = data.get('comment', '')
        
        # Prepare order
        point = mt5.symbol_info(symbol).point
        
        # Determine order type
        if order_type == 'BUY':
            order_type_mt5 = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask
        elif order_type == 'SELL':
            order_type_mt5 = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        else:
            return jsonify({'error': 'Invalid order type'}), 400
        
        request_dict = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'volume': volume,
            'type': order_type_mt5,
            'price': price,
            'sl': sl,
            'tp': tp,
            'deviation': 20,
            'magic': 234000,
            'comment': comment,
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
        }
        
        # Send order
        result = mt5.order_send(request_dict)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return jsonify({
                'success': False,
                'error': f'Order failed: {result.comment}'
            }), 400
        
        return jsonify({
            'success': True,
            'ticket': result.order,
            'volume': result.volume,
            'price': result.price,
            'comment': result.comment
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/ClosePosition', methods=['POST'])
def close_position():
    """Close a position"""
    if not mt5_connected:
        return jsonify({'error': 'Not connected'}), 401
    
    try:
        data = request.json
        ticket = int(data.get('ticket'))
        
        # Get position
        positions = mt5.positions_get(ticket=ticket)
        
        if not positions:
            return jsonify({'error': 'Position not found'}), 404
        
        position = positions[0]
        
        # Prepare close request
        close_type = mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(position.symbol).bid if position.type == 0 else mt5.symbol_info_tick(position.symbol).ask
        
        request_dict = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': position.symbol,
            'volume': position.volume,
            'type': close_type,
            'position': ticket,
            'price': price,
            'deviation': 20,
            'magic': 234000,
            'comment': 'Position closed',
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request_dict)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return jsonify({
                'success': False,
                'error': f'Close failed: {result.comment}'
            }), 400
        
        return jsonify({
            'success': True,
            'ticket': ticket,
            'message': 'Position closed successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/ModifyPosition', methods=['POST'])
def modify_position():
    """Modify position SL/TP"""
    if not mt5_connected:
        return jsonify({'error': 'Not connected'}), 401
    
    try:
        data = request.json
        ticket = int(data.get('ticket'))
        sl = float(data.get('sl', 0.0))
        tp = float(data.get('tp', 0.0))
        
        # Get position
        positions = mt5.positions_get(ticket=ticket)
        
        if not positions:
            return jsonify({'error': 'Position not found'}), 404
        
        position = positions[0]
        
        request_dict = {
            'action': mt5.TRADE_ACTION_SLTP,
            'symbol': position.symbol,
            'position': ticket,
            'sl': sl,
            'tp': tp
        }
        
        result = mt5.order_send(request_dict)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return jsonify({
                'success': False,
                'error': f'Modify failed: {result.comment}'
            }), 400
        
        return jsonify({
            'success': True,
            'ticket': ticket,
            'message': 'Position modified successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("MT5 REST API Server")
    # Get port from environment or use 8002 (8000 is used by Airbyte)
    import os
    port = int(os.getenv('PORT', '8002'))
    host = os.getenv('HOST', '0.0.0.0')
    
    print("=" * 60)
    print(f"Starting MT5 REST API server on http://localhost:{port}")
    print("\nMake sure MetaTrader 5 terminal is running!")
    print("\nAvailable endpoints:")
    print("  GET  /Health           - Health check")
    print("  GET  /Connect          - Connect to MT5 account")
    print("  GET  /Disconnect       - Disconnect")
    print("  GET  /AccountInfo      - Get account info")
    print("  GET  /Positions        - Get open positions")
    print("  GET  /MarketData       - Get OHLCV data")
    print("  GET  /SymbolInfo       - Get symbol info")
    print("  POST /PlaceTrade       - Place order")
    print("  POST /ClosePosition    - Close position")
    print("  POST /ModifyPosition   - Modify SL/TP")
    print("=" * 60)
    
    # Disable debug mode and use_reloader to prevent restart loop
    app.run(host=host, port=port, debug=False, use_reloader=False)
