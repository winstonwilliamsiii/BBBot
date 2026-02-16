"""
Simple MT5 REST API Server - No Debug Mode
Runs on port 8002 (8000 is used by Airbyte)
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import MetaTrader5 as mt5
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

mt5_connected = False

@app.route('/Health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'mt5_initialized': mt5.initialize(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/Connect', methods=['GET'])
def connect():
    """Connect to MT5"""
    global mt5_connected
    try:
        user = request.args.get('user')
        password = request.args.get('password')
        host = request.args.get('host')
        
        if not mt5.initialize():
            return jsonify({'success': False, 'error': 'MT5 initialization failed'}), 500
        
        authorized = mt5.login(login=int(user), password=password, server=host)
        
        if authorized:
            mt5_connected = True
            account = mt5.account_info()
            return jsonify({
                'success': True,
                'connected': True,
                'account': {
                    'login': account.login,
                    'balance': account.balance,
                    'equity': account.equity
                }
            })
        else:
            return jsonify({'success': False, 'error': f'Login failed: {mt5.last_error()}'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/AccountInfo', methods=['GET'])
def account_info():
    """Get account info"""
    if not mt5_connected:
        return jsonify({'error': 'Not connected'}), 401
    
    account = mt5.account_info()
    if not account:
        return jsonify({'error': 'Failed to get account info'}), 500
    
    return jsonify({
        'login': account.login,
        'balance': account.balance,
        'equity': account.equity,
        'profit': account.profit,
        'margin': account.margin,
        'free_margin': account.margin_free
    })

@app.route('/Positions', methods=['GET'])
def positions():
    """Get open positions"""
    if not mt5_connected:
        return jsonify({'error': 'Not connected'}), 401
    
    positions = mt5.positions_get()
    if not positions:
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
            'profit': pos.profit
        })
    
    return jsonify({'positions': result})

if __name__ == '__main__':
    port = int(os.getenv('PORT', '8002'))
    print(f"\n🚀 MT5 REST API Server starting on http://localhost:{port}")
    print("📡 Endpoints: /Health, /Connect, /AccountInfo, /Positions\n")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
