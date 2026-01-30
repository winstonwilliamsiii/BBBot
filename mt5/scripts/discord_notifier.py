#!/usr/bin/env python3
"""
MT5 Discord Notifier

Sends MT5 trade signals to Discord in real-time.

Usage:
    python discord_notifier.py --webhook-url "YOUR_WEBHOOK_URL" --signal-file signals.csv
"""

import json
import csv
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import argparse

try:
    import requests
except ImportError:
    print("ERROR: requests library required")
    print("Install with: pip install requests")
    exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Send notifications to Discord"""

    def __init__(self, webhook_url: str):
        """Initialize notifier"""
        self.webhook_url = webhook_url

    def send_embed(self, title: str, description: str, color: int,
                   fields: Optional[Dict] = None, footer: str = "BentleyBot") -> bool:
        """
        Send embedded message to Discord

        Args:
            title: Embed title
            description: Embed description
            color: Embed color (hex)
            fields: Optional dictionary of fields to add
            footer: Footer text

        Returns:
            True if successful
        """
        try:
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "footer": {"text": footer},
                "timestamp": datetime.utcnow().isoformat()
            }

            if fields:
                embed['fields'] = [
                    {"name": k, "value": str(v), "inline": True}
                    for k, v in fields.items()
                ]

            payload = {"embeds": [embed]}

            response = requests.post(self.webhook_url, json=payload, timeout=5)
            return response.status_code == 204

        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
            return False

    def notify_trade(self, signal: Dict):
        """
        Send trade signal notification

        Args:
            signal: Trade signal dictionary
        """
        try:
            symbol = signal.get('symbol', 'UNKNOWN')
            trade_type = signal.get('type', 'BUY').upper()
            price = signal.get('price', 0)
            sl = signal.get('sl', 0)
            tp = signal.get('tp', 0)

            # Determine colors
            title_color = 3066993 if trade_type == 'BUY' else 15158332  # Green or Red
            title = f"🤖 {trade_type} {symbol}"
            description = f"Entry: ${price:.5f}"

            fields = {
                "Stop Loss": f"${sl:.5f}",
                "Take Profit": f"${tp:.5f}",
                "Risk": f"{signal.get('risk_percent', 2)}%"
            }

            if 'rr_ratio' in signal:
                fields['R/R Ratio'] = f"{signal['rr_ratio']:.2f}:1"

            self.send_embed(title, description, title_color, fields)
            logger.info(f"Trade notification sent: {symbol} {trade_type}")

        except Exception as e:
            logger.error(f"Error notifying trade: {e}")

    def notify_error(self, error_message: str):
        """Send error notification"""
        self.send_embed(
            "⚠️ EA Error",
            error_message,
            15158332,  # Red
            footer="BentleyBot Error"
        )
        logger.error(f"Error notification sent: {error_message}")

    def notify_status(self, status_message: str):
        """Send status update notification"""
        self.send_embed(
            "ℹ️ BentleyBot Status",
            status_message,
            3066993,  # Blue
            footer="BentleyBot Status"
        )
        logger.info(f"Status notification sent: {status_message}")


class SignalMonitor:
    """Monitor signal file and send notifications"""

    def __init__(self, signal_file: Path, notifier: DiscordNotifier):
        """Initialize monitor"""
        self.signal_file = signal_file
        self.notifier = notifier
        self.processed_signals = set()

    def start(self, check_interval: int = 10):
        """
        Start monitoring signals

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
                        signal.get('timestamp'),
                        signal.get('symbol'),
                        signal.get('price')
                    ))

                    if signal_hash not in self.processed_signals:
                        self.notifier.notify_trade(signal)
                        self.processed_signals.add(signal_hash)

                time.sleep(check_interval)

            except KeyboardInterrupt:
                logger.info("Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                self.notifier.notify_error(f"Monitor error: {e}")
                time.sleep(check_interval)

    def _read_signals(self) -> list:
        """Read signals from CSV file"""
        try:
            signals = []
            with open(self.signal_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    signals.append(row)
            return signals
        except Exception as e:
            logger.error(f"Error reading signals: {e}")
            return []


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='MT5 Discord Notifier')
    parser.add_argument('--webhook-url', type=str, required=True, help='Discord webhook URL')
    parser.add_argument('--signal-file', type=Path, default=Path('mt5/signals.csv'),
                        help='Signal file path')
    parser.add_argument('--interval', type=int, default=10, help='Check interval (seconds)')
    parser.add_argument('--test', action='store_true', help='Send test notification')

    args = parser.parse_args()

    notifier = DiscordNotifier(args.webhook_url)

    # Test mode
    if args.test:
        logger.info("Sending test notification...")
        notifier.notify_status("✅ BentleyBot is online and monitoring")
        return

    # Monitor mode
    monitor = SignalMonitor(args.signal_file, notifier)
    monitor.start(check_interval=args.interval)


if __name__ == '__main__':
    main()
