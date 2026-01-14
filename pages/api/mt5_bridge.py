"""
MT5 Bridge - CLI Interface for MetaTrader 5
===========================================

Purpose:
- Provides command-line interface to MT5 for external integrations
- Enables Node.js child_process.spawn() to call MT5 functions
- Handles FOREX, Commodities, and Futures trading

Asset Classes Supported by MT5:
✅ FOREX (EURUSD, GBPUSD, USDCOP, etc.)
✅ Commodities (XAUUSD - Gold, XAGUSD - Silver, etc.)
✅ Futures (ES, NQ, YM, etc.)
❌ US Equities (use Alpaca instead - ALPACA_KEY_ID)
❌ Crypto (use Binance instead)

Usage:
    python mt5_bridge.py connect
    python mt5_bridge.py account_info
    python mt5_bridge.py get_positions
    python mt5_bridge.py trade --symbol=EURUSD --action=buy --volume=1.0 --price=1.0850
    python mt5_bridge.py close_position --ticket=123456
    python mt5_bridge.py modify_order --ticket=123456 --stop_loss=1.0800 --take_profit=1.0900

Node.js Integration:
    const { spawn } = require('child_process');
    const child = spawn('python', ['mt5_bridge.py', 'trade', '--symbol=XAUUSD', '--action=buy']);
    child.stdout.on('data', (data) => console.log(JSON.parse(data)));
"""

import sys
import json
import argparse
import os
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

try:
    from frontend.components.mt5_connector import MT5Connector
    MT5_AVAILABLE = True
except ImportError:
    logger.warning("MT5Connector not available")
    MT5_AVAILABLE = False


def error_response(message: str, code: int = 1) -> str:
    """Return standardized error response as JSON"""
    return json.dumps({
        'success': False,
        'error': message,
        'code': code,
        'timestamp': datetime.now().isoformat()
    })


def success_response(data: dict, message: str = "Success") -> str:
    """Return standardized success response as JSON"""
    return json.dumps({
        'success': True,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })


class MT5Bridge:
    """Bridge interface to MT5"""
    
    def __init__(self):
        if not MT5_AVAILABLE:
            raise Exception("MT5Connector not available")
        
        self.connector = MT5Connector()
        self.connected = False
    
    def connect(self, user: str = None, password: str = None, host: str = None) -> str:
        """
        Connect to MT5
        
        Args:
            user: MT5 account number (from .env if not provided)
            password: MT5 password (from .env if not provided)
            host: MT5 server (from .env if not provided)
        
        Returns:
            JSON response
        """
        try:
            user = user or os.getenv('MT5_USER')
            password = password or os.getenv('MT5_PASSWORD')
            host = host or os.getenv('MT5_HOST')
            
            if not all([user, password, host]):
                return error_response("Missing MT5 credentials in .env or arguments")
            
            logger.info(f"Connecting to MT5: {user}@{host}")
            
            success = self.connector.initialize_and_login(user, password, host)
            
            if success:
                self.connected = True
                return success_response({
                    'user': user,
                    'host': host,
                    'timestamp': datetime.now().isoformat()
                }, "Connected to MT5")
            else:
                return error_response("Failed to connect to MT5")
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return error_response(str(e))
    
    def disconnect(self) -> str:
        """Disconnect from MT5"""
        try:
            self.connector.disconnect()
            self.connected = False
            return success_response({}, "Disconnected from MT5")
        except Exception as e:
            return error_response(str(e))
    
    def get_account_info(self) -> str:
        """Get MT5 account information"""
        try:
            if not self.connected:
                return error_response("Not connected to MT5")
            
            info = self.connector.get_account_info()
            return success_response(info, "Account information retrieved")
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return error_response(str(e))
    
    def get_positions(self) -> str:
        """Get all open positions"""
        try:
            if not self.connected:
                return error_response("Not connected to MT5")
            
            positions = self.connector.get_positions()
            return success_response({
                'positions': positions,
                'count': len(positions)
            }, f"Retrieved {len(positions)} positions")
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return error_response(str(e))
    
    def get_position(self, symbol: str) -> str:
        """Get position for specific symbol"""
        try:
            if not self.connected:
                return error_response("Not connected to MT5")
            
            position = self.connector.get_position(symbol)
            if position:
                return success_response(position, f"Position for {symbol} retrieved")
            else:
                return error_response(f"No position for {symbol}")
                
        except Exception as e:
            return error_response(str(e))
    
    def get_symbol_info(self, symbol: str) -> str:
        """Get symbol information"""
        try:
            if not self.connected:
                return error_response("Not connected to MT5")
            
            info = self.connector.get_symbol_info(symbol)
            return success_response(info, f"Symbol info for {symbol} retrieved")
            
        except Exception as e:
            return error_response(str(e))
    
    def get_market_data(self, symbol: str, timeframe: str = "H1", limit: int = 100) -> str:
        """Get market data (OHLCV bars)"""
        try:
            if not self.connected:
                return error_response("Not connected to MT5")
            
            bars = self.connector.get_market_data(symbol, timeframe, limit)
            return success_response({
                'bars': bars,
                'count': len(bars)
            }, f"Retrieved {len(bars)} bars for {symbol}")
            
        except Exception as e:
            return error_response(str(e))
    
    def place_trade(
        self,
        symbol: str,
        action: str,  # 'buy' or 'sell'
        volume: float,
        price: float = 0.0,
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        comment: str = ""
    ) -> str:
        """
        Place a trade order
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD', 'XAUUSD')
            action: 'buy' or 'sell'
            volume: Lot size
            price: Order price (0 = market order)
            stop_loss: Stop loss level
            take_profit: Take profit level
            comment: Order comment
        
        Returns:
            JSON response with ticket number
        """
        try:
            if not self.connected:
                return error_response("Not connected to MT5")
            
            logger.info(f"Placing {action} order: {symbol} x{volume}")
            
            result = self.connector.place_order(
                symbol=symbol,
                order_type=action.upper(),  # BUY or SELL
                volume=volume,
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                comment=comment
            )
            
            if result.get('success'):
                return success_response({
                    'ticket': result.get('ticket'),
                    'symbol': symbol,
                    'action': action,
                    'volume': volume,
                    'price': price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                }, f"Order placed: {symbol} {action} x{volume}")
            else:
                return error_response(result.get('error', 'Order placement failed'))
                
        except Exception as e:
            logger.error(f"Error placing trade: {e}")
            return error_response(str(e))
    
    def close_position(self, symbol: str, volume: float = 0.0) -> str:
        """
        Close position for symbol
        
        Args:
            symbol: Symbol to close
            volume: Volume to close (0 = all)
        
        Returns:
            JSON response
        """
        try:
            if not self.connected:
                return error_response("Not connected to MT5")
            
            logger.info(f"Closing position: {symbol}")
            
            result = self.connector.close_position(symbol, volume)
            
            if result.get('success'):
                return success_response({
                    'symbol': symbol,
                    'volume': volume,
                    'ticket': result.get('ticket')
                }, f"Position closed: {symbol}")
            else:
                return error_response(result.get('error', 'Close failed'))
                
        except Exception as e:
            return error_response(str(e))
    
    def modify_order(
        self,
        ticket: int,
        stop_loss: float = 0.0,
        take_profit: float = 0.0
    ) -> str:
        """
        Modify order stop loss and take profit
        
        Args:
            ticket: Order ticket number
            stop_loss: New stop loss level
            take_profit: New take profit level
        
        Returns:
            JSON response
        """
        try:
            if not self.connected:
                return error_response("Not connected to MT5")
            
            logger.info(f"Modifying order {ticket}: SL={stop_loss}, TP={take_profit}")
            
            result = self.connector.modify_order(ticket, stop_loss, take_profit)
            
            if result.get('success'):
                return success_response({
                    'ticket': ticket,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                }, f"Order {ticket} modified")
            else:
                return error_response(result.get('error', 'Modification failed'))
                
        except Exception as e:
            return error_response(str(e))
    
    def get_current_price(self, symbol: str) -> str:
        """Get current bid/ask price"""
        try:
            if not self.connected:
                return error_response("Not connected to MT5")
            
            bid, ask = self.connector.get_current_price(symbol)
            
            return success_response({
                'symbol': symbol,
                'bid': bid,
                'ask': ask,
                'mid': (bid + ask) / 2
            }, f"Current price for {symbol}")
            
        except Exception as e:
            return error_response(str(e))


def main():
    """Main entry point for CLI"""
    
    parser = argparse.ArgumentParser(description='MT5 Bridge - CLI Interface')
    parser.add_argument('command', nargs='?', default='help',
                       help='Command to execute: connect, disconnect, account_info, get_positions, '
                            'get_position, get_symbol_info, get_market_data, trade, close_position, '
                            'modify_order, get_price')
    
    # Optional arguments
    parser.add_argument('--user', help='MT5 account number')
    parser.add_argument('--password', help='MT5 password')
    parser.add_argument('--host', help='MT5 server')
    parser.add_argument('--symbol', help='Trading symbol')
    parser.add_argument('--action', help='Trade action (buy/sell)')
    parser.add_argument('--volume', type=float, help='Trade volume')
    parser.add_argument('--price', type=float, default=0.0, help='Order price')
    parser.add_argument('--stop_loss', type=float, default=0.0, help='Stop loss level')
    parser.add_argument('--take_profit', type=float, default=0.0, help='Take profit level')
    parser.add_argument('--ticket', type=int, help='Order ticket number')
    parser.add_argument('--timeframe', default='H1', help='Chart timeframe')
    parser.add_argument('--limit', type=int, default=100, help='Number of bars')
    parser.add_argument('--comment', default='', help='Order comment')
    
    args = parser.parse_args()
    
    # Handle help
    if args.command == 'help' or args.command is None:
        print("""
MT5 Bridge - Command Line Interface
===================================

Available Commands:
  connect                   Connect to MT5
  disconnect                Disconnect from MT5
  account_info              Get account information
  get_positions             Get all open positions
  get_position --symbol=EURUSD    Get position for symbol
  get_symbol_info --symbol=EURUSD Get symbol information
  get_market_data --symbol=EURUSD Get OHLCV bars
  get_price --symbol=EURUSD       Get current bid/ask
  trade                     Place trade order
  close_position            Close position
  modify_order              Modify order SL/TP

Examples:
  python mt5_bridge.py connect
  python mt5_bridge.py trade --symbol=EURUSD --action=buy --volume=1.0
  python mt5_bridge.py close_position --symbol=XAUUSD --volume=0.5
  python mt5_bridge.py modify_order --ticket=123456 --stop_loss=1.0800 --take_profit=1.0900

""")
        sys.exit(0)
    
    # Initialize bridge
    try:
        bridge = MT5Bridge()
    except Exception as e:
        print(error_response(f"Failed to initialize MT5: {e}"))
        sys.exit(1)
    
    # Route commands
    try:
        if args.command == 'connect':
            print(bridge.connect(args.user, args.password, args.host))
        
        elif args.command == 'disconnect':
            print(bridge.disconnect())
        
        elif args.command == 'account_info':
            print(bridge.get_account_info())
        
        elif args.command == 'get_positions':
            print(bridge.get_positions())
        
        elif args.command == 'get_position':
            if not args.symbol:
                print(error_response("--symbol is required"))
                sys.exit(1)
            print(bridge.get_position(args.symbol))
        
        elif args.command == 'get_symbol_info':
            if not args.symbol:
                print(error_response("--symbol is required"))
                sys.exit(1)
            print(bridge.get_symbol_info(args.symbol))
        
        elif args.command == 'get_market_data':
            if not args.symbol:
                print(error_response("--symbol is required"))
                sys.exit(1)
            print(bridge.get_market_data(args.symbol, args.timeframe, args.limit))
        
        elif args.command == 'get_price':
            if not args.symbol:
                print(error_response("--symbol is required"))
                sys.exit(1)
            print(bridge.get_current_price(args.symbol))
        
        elif args.command == 'trade':
            if not all([args.symbol, args.action, args.volume]):
                print(error_response("--symbol, --action, and --volume are required"))
                sys.exit(1)
            print(bridge.place_trade(
                symbol=args.symbol,
                action=args.action,
                volume=args.volume,
                price=args.price,
                stop_loss=args.stop_loss,
                take_profit=args.take_profit,
                comment=args.comment
            ))
        
        elif args.command == 'close_position':
            if not args.symbol:
                print(error_response("--symbol is required"))
                sys.exit(1)
            print(bridge.close_position(args.symbol, args.volume or 0.0))
        
        elif args.command == 'modify_order':
            if not args.ticket:
                print(error_response("--ticket is required"))
                sys.exit(1)
            print(bridge.modify_order(
                ticket=args.ticket,
                stop_loss=args.stop_loss,
                take_profit=args.take_profit
            ))
        
        else:
            print(error_response(f"Unknown command: {args.command}"))
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(error_response(str(e)))
        sys.exit(1)


if __name__ == '__main__':
    main()
