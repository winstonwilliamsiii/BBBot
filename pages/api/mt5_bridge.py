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

        self.base_url = os.getenv('MT5_API_URL', 'http://localhost:8080')
        self.connector = MT5Connector(self.base_url)
        self.connected = False
        self.startup_health_ok = self._check_service_health()

    def _check_service_health(self) -> bool:
        try:
            return self.connector.health_check()
        except Exception as exc:
            logger.warning(f"MT5 health check failed: {exc}")
            return False

    def _service_guard(self) -> str | None:
        if self._check_service_health():
            return None

        return (
            f"MT5 bridge service is unavailable at {self.base_url}. "
            "Start the MT5 REST server, ensure MT5 terminal is running and logged in, "
            "then retry."
        )

    @staticmethod
    def _position_to_dict(position) -> dict:
        return {
            'ticket': position.ticket,
            'symbol': position.symbol,
            'type': position.type,
            'volume': position.volume,
            'open_price': position.open_price,
            'current_price': position.current_price,
            'profit': position.profit,
            'open_time': position.open_time.isoformat() if position.open_time else None,
        }

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
            guard_message = self._service_guard()
            if guard_message:
                return error_response(guard_message)

            user = user or os.getenv('MT5_USER')
            password = password or os.getenv('MT5_PASSWORD')
            host = host or os.getenv('MT5_HOST')
            port = int(os.getenv('MT5_PORT', '443'))

            if not all([user, password, host]):
                return error_response("Missing MT5 credentials in .env or arguments")

            logger.info(f"Connecting to MT5: {user}@{host}:{port}")

            success = self.connector.connect(user, password, host, port)

            if success:
                self.connected = True
                return success_response({
                    'user': user,
                    'host': host,
                    'port': port,
                    'base_url': self.base_url,
                    'timestamp': datetime.now().isoformat()
                }, "Connected to MT5")

            detail = getattr(self.connector, 'last_connect_error', '')
            if detail:
                return error_response(f"Failed to connect to MT5: {detail}")
            return error_response("Failed to connect to MT5")

        except Exception as e:
            logger.error(f"Connection error: {e}")
            return error_response(str(e))

    def disconnect(self) -> str:
        """Disconnect from MT5"""
        try:
            success = self.connector.disconnect()
            self.connected = False
            if success:
                return success_response({}, "Disconnected from MT5")
            return error_response("Disconnect request failed")
        except Exception as e:
            return error_response(str(e))

    def get_account_info(self) -> str:
        """Get MT5 account information"""
        try:
            if not self.connected:
                return error_response("Not connected to MT5")

            info = self.connector.get_account_info()
            if info is None:
                return error_response("Failed to retrieve account information")
            return success_response(info, "Account information retrieved")

        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return error_response(str(e))

    def get_positions(self) -> str:
        """Get all open positions"""
        try:
            if not self.connected:
                return error_response("Not connected to MT5")

            positions = self.connector.get_positions() or []
            position_dicts = [self._position_to_dict(pos) for pos in positions]
            return success_response({
                'positions': position_dicts,
                'count': len(position_dicts)
            }, f"Retrieved {len(position_dicts)} positions")

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return error_response(str(e))

    def get_position(self, symbol: str) -> str:
        """Get position for specific symbol"""
        try:
            if not self.connected:
                return error_response("Not connected to MT5")

            positions = self.connector.get_positions() or []
            for position in positions:
                if str(position.symbol).upper() == str(symbol).upper():
                    return success_response(self._position_to_dict(position), f"Position for {symbol} retrieved")

            return error_response(f"No position for {symbol}")

        except Exception as e:
            return error_response(str(e))

    def get_symbol_info(self, symbol: str) -> str:
        """Get symbol information"""
        try:
            if not self.connected:
                return error_response("Not connected to MT5")

            info = self.connector.get_symbol_info(symbol)
            if info is None:
                return error_response(f"Failed to retrieve symbol info for {symbol}")
            return success_response(info, f"Symbol info for {symbol} retrieved")

        except Exception as e:
            return error_response(str(e))

    def get_market_data(self, symbol: str, timeframe: str = "H1", limit: int = 100) -> str:
        """Get market data (OHLCV bars)"""
        try:
            if not self.connected:
                return error_response("Not connected to MT5")

            market_data = self.connector.get_market_data(symbol, timeframe, limit)
            if market_data is None:
                return error_response(f"Failed to retrieve market data for {symbol}")

            bars = market_data.get('bars', []) if isinstance(market_data, dict) else []
            return success_response({
                'market_data': market_data,
                'count': len(bars)
            }, f"Retrieved {len(bars)} bars for {symbol}")

        except Exception as e:
            return error_response(str(e))

    def place_trade(
        self,
        symbol: str,
        action: str,
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

            order_type = action.upper()
            result = self.connector.place_trade(
                symbol=symbol,
                order_type=order_type,
                volume=volume,
                price=price if price > 0 else None,
                sl=stop_loss if stop_loss > 0 else None,
                tp=take_profit if take_profit > 0 else None,
                comment=comment
            )

            if result and result.get('success'):
                return success_response({
                    'ticket': result.get('ticket'),
                    'symbol': symbol,
                    'action': action,
                    'volume': volume,
                    'price': price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'raw_result': result
                }, f"Order placed: {symbol} {action} x{volume}")

            error_msg = result.get('error', 'Order placement failed') if isinstance(result, dict) else 'Order placement failed'
            return error_response(error_msg)

        except Exception as e:
            logger.error(f"Error placing trade: {e}")
            return error_response(str(e))

    def close_position(self, symbol: str = None, volume: float = 0.0, ticket: int = None) -> str:
        """
        Close position by ticket or by symbol lookup.

        Args:
            symbol: Symbol to close (optional if ticket provided)
            volume: Retained for compatibility
            ticket: Position ticket number

        Returns:
            JSON response
        """
        try:
            if not self.connected:
                return error_response("Not connected to MT5")

            resolved_ticket = ticket
            resolved_symbol = symbol

            if resolved_ticket is None:
                if not symbol:
                    return error_response("Either symbol or ticket is required")

                positions = self.connector.get_positions() or []
                matching = [p for p in positions if str(p.symbol).upper() == str(symbol).upper()]
                if not matching:
                    return error_response(f"No open position found for {symbol}")

                resolved_ticket = matching[0].ticket
                resolved_symbol = matching[0].symbol

            logger.info(f"Closing position ticket {resolved_ticket}")
            success = self.connector.close_position(int(resolved_ticket))

            if success:
                return success_response({
                    'symbol': resolved_symbol,
                    'volume': volume,
                    'ticket': resolved_ticket
                }, f"Position closed: {resolved_ticket}")

            return error_response("Close failed")

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

            success = self.connector.modify_position(
                ticket,
                stop_loss if stop_loss > 0 else None,
                take_profit if take_profit > 0 else None
            )

            if success:
                return success_response({
                    'ticket': ticket,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                }, f"Order {ticket} modified")

            return error_response("Modification failed")

        except Exception as e:
            return error_response(str(e))

    def get_current_price(self, symbol: str) -> str:
        """Get current bid/ask price"""
        try:
            if not self.connected:
                return error_response("Not connected to MT5")

            info = self.connector.get_symbol_info(symbol)
            if not info:
                return error_response(f"Unable to fetch price for {symbol}")

            bid = info.get('bid')
            ask = info.get('ask')

            if bid is None or ask is None:
                return error_response(f"Price data unavailable for {symbol}")

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
  python mt5_bridge.py close_position --ticket=123456
  python mt5_bridge.py modify_order --ticket=123456 --stop_loss=1.0800 --take_profit=1.0900

""")
        sys.exit(0)

    try:
        bridge = MT5Bridge()
    except Exception as e:
        print(error_response(f"Failed to initialize MT5: {e}"))
        sys.exit(1)

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
            if not args.symbol and not args.ticket:
                print(error_response("--symbol or --ticket is required"))
                sys.exit(1)
            print(bridge.close_position(symbol=args.symbol, volume=args.volume or 0.0, ticket=args.ticket))

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
