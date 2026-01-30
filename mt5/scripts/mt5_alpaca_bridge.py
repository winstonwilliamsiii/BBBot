#!/usr/bin/env python3
"""
MT5 & Alpaca Trading Bridge

Monitors MT5 trade signals and syncs with Alpaca API.
Requires: pandas, alpaca_trade_api

Usage:
    python mt5_alpaca_bridge.py --config config/trading_config.json
"""

import json
import csv
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import argparse

try:
    import pandas as pd
    from alpaca_trade_api import REST, StreamConn
except ImportError:
    print("ERROR: Required packages not installed")
    print("Install with: pip install alpaca-trade-api pandas")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MT5AlpacaBridge:
    """Bridge between MT5 and Alpaca APIs"""

    def __init__(self, alpaca_key: str, alpaca_secret: str, signal_file: Path):
        """Initialize bridge"""
        self.api = REST(alpaca_key, alpaca_secret, base_url='https://paper-api.alpaca.markets')
        self.signal_file = signal_file
        self.processed_signals = set()

    def monitor_signals(self, check_interval: int = 10):
        """
        Monitor MT5 signals file and process new trades

        Args:
            check_interval: Seconds between checks
        """
        logger.info(f"Starting signal monitor (checking every {check_interval}s)")

        while True:
            try:
                if not self.signal_file.exists():
                    logger.warning(f"Signal file not found: {self.signal_file}")
                    time.sleep(check_interval)
                    continue

                # Read signals
                signals = self._read_signals()

                # Process new signals
                for signal in signals:
                    signal_hash = hash((
                        signal['timestamp'],
                        signal['symbol'],
                        signal['price']
                    ))

                    if signal_hash not in self.processed_signals:
                        self._process_signal(signal)
                        self.processed_signals.add(signal_hash)

                time.sleep(check_interval)

            except KeyboardInterrupt:
                logger.info("Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(check_interval)

    def _read_signals(self) -> List[Dict]:
        """Read trade signals from CSV file"""
        try:
            df = pd.read_csv(self.signal_file)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error reading signals file: {e}")
            return []

    def _process_signal(self, signal: Dict):
        """
        Process individual trade signal

        Args:
            signal: Dictionary with keys: timestamp, symbol, price, type, sl, tp
        """
        try:
            # Validate signal
            required_fields = ['symbol', 'price', 'type']
            if not all(field in signal for field in required_fields):
                logger.warning(f"Invalid signal format: {signal}")
                return

            # Calculate position size
            qty = self._calculate_quantity(float(signal['price']))

            if qty <= 0:
                logger.warning(f"Invalid quantity calculated: {qty}")
                return

            # Submit order
            order = self.api.submit_order(
                symbol=signal['symbol'],
                qty=qty,
                side=signal['type'].lower(),  # 'buy' or 'sell'
                type='market'
            )

            logger.info(f"Order placed: {order.symbol} {order.side} {order.qty} @ {order.filled_avg_price}")

            # Send notification
            self._notify(f"✅ Order placed: {order.symbol} {order.side.upper()} {order.qty}")

        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            self._notify(f"❌ Order failed: {e}")

    def _calculate_quantity(self, entry_price: float) -> int:
        """
        Calculate position size based on account risk

        Args:
            entry_price: Entry price in USD

        Returns:
            Quantity to trade
        """
        try:
            account = self.api.get_account()
            buying_power = float(account.buying_power)
            risk_amount = buying_power * 0.02  # 2% risk

            qty = int(risk_amount / entry_price)
            return max(qty, 1)

        except Exception as e:
            logger.error(f"Error calculating quantity: {e}")
            return 0

    def _notify(self, message: str):
        """Send notification (placeholder for Discord/email)"""
        logger.info(f"[NOTIFICATION] {message}")


class StrategyTester:
    """Backtest strategy from CSV file"""

    def __init__(self, trades_file: Path):
        """Initialize tester"""
        self.trades_file = trades_file

    def run_backtest(self) -> Dict:
        """
        Run backtest analysis

        Returns:
            Dictionary with metrics
        """
        try:
            df = pd.read_csv(self.trades_file)

            if df.empty:
                logger.warning("No trades in file")
                return {}

            # Calculate metrics
            metrics = {
                'total_trades': len(df),
                'winning_trades': len(df[df['profit'] > 0]),
                'losing_trades': len(df[df['profit'] < 0]),
                'win_rate': len(df[df['profit'] > 0]) / len(df) * 100 if len(df) > 0 else 0,
                'total_profit': df['profit'].sum(),
                'avg_profit': df['profit'].mean(),
                'max_profit': df['profit'].max(),
                'max_loss': df['profit'].min(),
                'profit_factor': self._calculate_profit_factor(df)
            }

            return metrics

        except Exception as e:
            logger.error(f"Error in backtest: {e}")
            return {}

    @staticmethod
    def _calculate_profit_factor(df: pd.DataFrame) -> float:
        """Calculate profit factor"""
        wins = df[df['profit'] > 0]['profit'].sum()
        losses = abs(df[df['profit'] < 0]['profit'].sum())

        if losses == 0:
            return float('inf') if wins > 0 else 0

        return wins / losses


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='MT5 Alpaca Trading Bridge')
    parser.add_argument('--config', type=Path, required=True, help='Config file path')
    parser.add_argument('--signal-file', type=Path, help='Signal file path')
    parser.add_argument('--key', type=str, help='Alpaca API key')
    parser.add_argument('--secret', type=str, help='Alpaca secret key')
    parser.add_argument('--backtest', type=Path, help='Run backtest on trades file')
    parser.add_argument('--interval', type=int, default=10, help='Check interval (seconds)')

    args = parser.parse_args()

    # Load config
    with open(args.config) as f:
        config = json.load(f)

    # Backtest mode
    if args.backtest:
        logger.info(f"Running backtest on {args.backtest}")
        tester = StrategyTester(args.backtest)
        metrics = tester.run_backtest()

        logger.info("=" * 50)
        for key, value in metrics.items():
            logger.info(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
        logger.info("=" * 50)

        return

    # Monitor mode
    if not args.key or not args.secret:
        logger.error("Alpaca credentials required (--key, --secret)")
        return

    signal_file = args.signal_file or Path('mt5/signals.csv')

    bridge = MT5AlpacaBridge(args.key, args.secret, signal_file)
    bridge.monitor_signals(check_interval=args.interval)


if __name__ == '__main__':
    main()
