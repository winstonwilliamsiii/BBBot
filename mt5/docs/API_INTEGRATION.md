# MT5 & Python Integration Guide

## Overview
This guide covers integrating MT5 Expert Advisors with Python-based services (Alpaca, Discord, etc.).

## Architecture

```
┌──────────────────┐
│   MT5 Terminal   │
│  (EA Trading)    │
└────────┬─────────┘
         │
    CSV/JSON Export
         │
         ▼
┌──────────────────────────────┐
│   Python Bridge Service      │
│  • Trade Signal Processing   │
│  • Alpaca Order Submission   │
│  • Discord Notifications     │
└──────────────────────────────┘
         │
    HTTP/REST API
         │
┌────────┴────────────────────┐
│                             │
▼                             ▼
Alpaca Trading API      Discord Webhooks
```

## Integration Methods

### Method 1: File-Based Communication (CSV)

#### A. MT5 EA Exports Trades
```mql5
// In BentleyBot EA - OnTrade() callback
void ExportTradeSignal(string symbol, double price, string type)
  {
   int file_handle = FileOpen("BentleyBot_signals.csv", FILE_WRITE | FILE_CSV);
   
   if(file_handle != INVALID_HANDLE)
     {
      FileWrite(file_handle, 
        TimeCurrent(), 
        symbol, 
        price, 
        type);  // "BUY" or "SELL"
      FileClose(file_handle);
     }
  }
```

#### B. Python Script Monitors & Processes
```python
import pandas as pd
import time
from alpaca_trade_api import REST, StreamConn

class MT5TradingBridge:
    def __init__(self, alpaca_api_key, alpaca_secret_key):
        self.api = REST(alpaca_api_key, alpaca_secret_key)
        self.signal_file = r"C:\MetaTrader 5\MQL5\Experts\BentleyBot_signals.csv"
        self.processed_signals = set()
    
    def monitor_signals(self):
        """Poll for new trade signals from MT5"""
        while True:
            try:
                df = pd.read_csv(self.signal_file)
                
                for idx, row in df.iterrows():
                    signal_hash = hash((row['Time'], row['Symbol'], row['Price']))
                    
                    if signal_hash not in self.processed_signals:
                        self.process_signal(row)
                        self.processed_signals.add(signal_hash)
                
                time.sleep(5)  # Check every 5 seconds
            
            except Exception as e:
                print(f"Error monitoring signals: {e}")
                time.sleep(10)
    
    def process_signal(self, signal):
        """Execute trade on Alpaca"""
        try:
            qty = self.calculate_quantity(signal['Price'])
            
            order = self.api.submit_order(
                symbol=signal['Symbol'],
                qty=qty,
                side=signal['Type'].lower(),  # 'buy' or 'sell'
                type='market'
            )
            
            print(f"Order placed: {order}")
            
        except Exception as e:
            print(f"Error executing trade: {e}")
    
    def calculate_quantity(self, entry_price):
        """Calculate position size based on account risk"""
        account = self.api.get_account()
        risk_amount = float(account.buying_power) * 0.02  # 2% risk
        qty = int(risk_amount / entry_price)
        return max(qty, 1)

# Usage
if __name__ == "__main__":
    bridge = MT5TradingBridge(
        alpaca_api_key="YOUR_KEY",
        alpaca_secret_key="YOUR_SECRET"
    )
    bridge.monitor_signals()
```

### Method 2: REST API Integration

#### A. MT5 EA with HTTP Library (Advanced)
```mql5
// Requires: WinInet or external library for HTTP calls
// This is more complex and requires DLL imports

#import "wininet.dll"
  int InternetOpenA(string sAgent, int lAccessType, 
                    string sProxyName, string sProxyBypass, int dwFlags);
  int InternetOpenUrlA(int hInternet, string sUrl, string sHeaders,
                       int dwHeadersLength, int dwFlags, int dwContext);
  int InternetReadFile(int hFile, string sBuffer, int dwNumberOfBytesToRead,
                       int& lNumberOfBytesRead);
  int InternetCloseHandle(int hInternet);
#import

void SendTradeSignal(string symbol, double price, string type)
  {
   // HTTP POST to Python endpoint
   // Implementation requires DLL calls - complex setup
  }
```

#### B. Python REST Server
```python
from flask import Flask, request
from alpaca_trade_api import REST
import json

app = Flask(__name__)
api = REST()

@app.route('/trade_signal', methods=['POST'])
def receive_signal():
    """Endpoint for MT5 EA to POST trade signals"""
    try:
        data = request.json
        
        # Validate signal
        required_fields = ['symbol', 'price', 'type', 'sl', 'tp']
        if not all(field in data for field in required_fields):
            return {'error': 'Missing fields'}, 400
        
        # Submit to Alpaca
        order = api.submit_order(
            symbol=data['symbol'],
            qty=data['qty'],
            side=data['type'],
            type='market'
        )
        
        # Send notification
        notify_discord(f"Order placed: {data['symbol']} {data['type']}")
        
        return {'status': 'success', 'order_id': order.id}, 200
    
    except Exception as e:
        print(f"Error: {e}")
        return {'error': str(e)}, 500

def notify_discord(message):
    """Send notification to Discord"""
    webhook_url = "YOUR_DISCORD_WEBHOOK_URL"
    payload = {"content": f"🤖 BentleyBot: {message}"}
    requests.post(webhook_url, json=payload)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
```

### Method 3: Database Sync

#### A. MT5 EA Writes to Local Database
```mql5
// Export trades to SQLite via Python
void LogTradeToDatabase(string symbol, double price, string type)
  {
   // Write to CSV which Python monitors
   // Or use SQLite DLL (advanced)
  }
```

#### B. Python Reads & Syncs
```python
import sqlite3
from datetime import datetime

class MT5DatabaseBridge:
    def __init__(self, db_path):
        self.db = sqlite3.connect(db_path)
        self.cursor = self.db.cursor()
        self.setup_db()
    
    def setup_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS mt5_trades (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME,
                symbol TEXT,
                price REAL,
                type TEXT,
                status TEXT,
                alpaca_order_id TEXT
            )
        ''')
        self.db.commit()
    
    def sync_trades(self):
        """Sync new trades to Alpaca"""
        self.cursor.execute(
            'SELECT * FROM mt5_trades WHERE status = ?', 
            ('pending',)
        )
        
        for row in self.cursor.fetchall():
            try:
                order = api.submit_order(...)
                self.update_trade_status(row[0], 'submitted', order.id)
            except Exception as e:
                self.update_trade_status(row[0], 'failed', str(e))
    
    def update_trade_status(self, trade_id, status, alpaca_order_id):
        self.cursor.execute(
            'UPDATE mt5_trades SET status = ?, alpaca_order_id = ? WHERE id = ?',
            (status, alpaca_order_id, trade_id)
        )
        self.db.commit()
```

## Discord Notifications

### Python Setup
```python
import discord
from discord.ext import commands, tasks
import aiohttp

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user}')
    monitor_mt5_trades.start()

@tasks.loop(seconds=10)
async def monitor_mt5_trades():
    """Monitor MT5 trades and post to Discord"""
    try:
        channel = bot.get_channel(YOUR_CHANNEL_ID)
        
        # Read latest MT5 signals
        signals = read_mt5_signals()
        
        for signal in signals:
            embed = discord.Embed(
                title="🤖 BentleyBot Trade Signal",
                description=f"{signal['type'].upper()} {signal['symbol']}",
                color=discord.Color.green() if signal['type'] == 'buy' else discord.Color.red()
            )
            embed.add_field(name="Entry Price", value=f"${signal['price']:.5f}")
            embed.add_field(name="Stop Loss", value=f"${signal['sl']:.5f}")
            embed.add_field(name="Take Profit", value=f"${signal['tp']:.5f}")
            embed.add_field(name="Risk/Reward", value=f"{signal['rr_ratio']:.2f}:1")
            
            await channel.send(embed=embed)
    
    except Exception as e:
        print(f"Error: {e}")

bot.run(DISCORD_TOKEN)
```

### Webhook Alternative (Simpler)
```python
import requests

def send_discord_notification(signal):
    webhook_url = "YOUR_WEBHOOK_URL"
    
    embed = {
        "title": f"🤖 {signal['type'].upper()} {signal['symbol']}",
        "description": f"Entry: ${signal['price']:.5f}",
        "color": 3066993 if signal['type'] == 'buy' else 15158332,
        "fields": [
            {"name": "SL", "value": f"${signal['sl']:.5f}", "inline": True},
            {"name": "TP", "value": f"${signal['tp']:.5f}", "inline": True},
            {"name": "R/R", "value": f"{signal['rr_ratio']:.2f}:1", "inline": True}
        ]
    }
    
    payload = {"embeds": [embed]}
    requests.post(webhook_url, json=payload)
```

## CI/CD for MT5 Deployment

### GitHub Actions Workflow
```yaml
name: MT5 Deploy

on:
  push:
    branches: [main]
    paths:
      - 'mt5/experts/**'

jobs:
  deploy:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Compile MQL5
        run: |
          $metaeditor = "C:\Program Files\MetaTrader 5\metaeditor64.exe"
          & $metaeditor /compile:"mt5\experts\BentleyBot_GBP_JPY_EA.mq5"
      
      - name: Copy to MT5 Directory
        run: |
          Copy-Item "mt5\experts\*.ex5" `
                    "C:\Users\$env:USERNAME\AppData\Roaming\MetaQuotes\Terminal\Common\Files\MQL5\Experts"
      
      - name: Notify Discord
        run: |
          python scripts/notify_deployment.py
```

## Setup Checklist

- [ ] MT5 Terminal installed with demo account
- [ ] MetaEditor accessible
- [ ] Python environment configured with Alpaca SDK
- [ ] Discord webhook created (if using notifications)
- [ ] File monitoring system running (or REST server)
- [ ] Test signal transmission end-to-end
- [ ] Validate Alpaca orders placed correctly
- [ ] Monitor logs for errors
- [ ] Run overnight test (8+ hours)
- [ ] Ready for production

## Troubleshooting

### EA Not Exporting Signals
- Check file permissions in MT5 data folder
- Verify FileOpen() calls aren't failing
- Check Windows Event Viewer for errors

### Python Not Detecting Signals
- Verify file path is correct
- Check CSV formatting
- Add logging/debugging to Python script

### Alpaca Orders Not Executing
- Verify API credentials
- Check account buying power
- Validate symbol names (use correct format)
- Check market hours

### Discord Not Receiving Messages
- Test webhook URL manually
- Verify channel permissions
- Check network connectivity
