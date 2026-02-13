"""
MT5 Paper Trading Example
=========================
Simple example script showing how to use the MT5 REST API for paper trading.

Prerequisites:
1. MT5 terminal running and logged in
2. MT5 REST server running (START_MT5_PAPER_TRADING.ps1)
3. Server accessible at http://localhost:8080

Usage:
    python example_paper_trade.py
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8080"
SYMBOL = "EURUSD"  # Change to your preferred symbol
LOT_SIZE = 0.01  # Micro lot (safest for testing)

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def make_request(method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
    """Make HTTP request to MT5 REST API"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {"success": False, "error": str(e)}

def main():
    print_section("🚀 MT5 Paper Trading Example")
    
    # Step 1: Health Check
    print_section("1️⃣  Health Check")
    health = make_request("GET", "/health")
    if health.get("status") == "ok":
        print("✅ Server is running")
    else:
        print("❌ Server is not responding")
        return
    
    # Step 2: Connect to MT5
    print_section("2️⃣  Connect to MT5")
    connect = make_request("POST", "/connect")
    if connect.get("success"):
        print("✅ Connected to MT5 terminal")
    else:
        print(f"❌ Connection failed: {connect.get('error')}")
        return
    
    # Step 3: Get Account Info
    print_section("3️⃣  Account Information")
    account = make_request("GET", "/account")
    if account.get("success"):
        data = account["data"]
        print(f"📊 Account: {data.get('login')}")
        print(f"💰 Balance: ${data.get('balance'):,.2f}")
        print(f"📈 Equity: ${data.get('equity'):,.2f}")
        print(f"💵 Free Margin: ${data.get('free_margin'):,.2f}")
        print(f"🎯 Leverage: 1:{data.get('leverage')}")
        print(f"💱 Currency: {data.get('currency')}")
    else:
        print(f"❌ Failed to get account info: {account.get('error')}")
        return
    
    # Step 4: Get Current Price
    print_section(f"4️⃣  Current Price for {SYMBOL}")
    price_data = make_request("GET", f"/price/{SYMBOL}")
    if price_data.get("success"):
        data = price_data["data"]
        bid = data.get("bid", 0)
        ask = data.get("ask", 0)
        spread = ask - bid
        print(f"📉 Bid: {bid:.5f}")
        print(f"📈 Ask: {ask:.5f}")
        print(f"📊 Spread: {spread:.5f} ({spread*10000:.1f} pips)")
    else:
        print(f"❌ Failed to get price: {price_data.get('error')}")
        return
    
    # Step 5: Check Current Positions
    print_section("5️⃣  Current Open Positions")
    positions = make_request("GET", "/positions")
    if positions.get("success"):
        pos_list = positions.get("data", [])
        if pos_list:
            print(f"📋 You have {len(pos_list)} open position(s):")
            for pos in pos_list:
                print(f"  • {pos.get('symbol')} - {pos.get('type')} - "
                      f"Volume: {pos.get('volume')} - "
                      f"Profit: ${pos.get('profit', 0):.2f}")
        else:
            print("✅ No open positions")
    
    # Step 6: Place a Paper Trade (Interactive)
    print_section("6️⃣  Place Paper Trade")
    print(f"\n⚠️  WARNING: This will place a REAL trade on your demo account!")
    print(f"Symbol: {SYMBOL}")
    print(f"Volume: {LOT_SIZE} lot (micro lot)")
    print(f"Type: BUY")
    
    # Calculate stop loss and take profit (20 pips SL, 30 pips TP)
    stop_loss = round(bid - 0.0020, 5)  # 20 pips below
    take_profit = round(ask + 0.0030, 5)  # 30 pips above
    
    print(f"Stop Loss: {stop_loss:.5f}")
    print(f"Take Profit: {take_profit:.5f}")
    
    user_input = input("\n➡️  Proceed with trade? (yes/no): ").strip().lower()
    if user_input not in ["yes", "y"]:
        print("❌ Trade cancelled")
        return
    
    # Place the trade
    trade_data = {
        "symbol": SYMBOL,
        "action": "buy",
        "volume": LOT_SIZE,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "comment": "Paper trade example"
    }
    
    trade_result = make_request("POST", "/trade", trade_data)
    if trade_result.get("success"):
        data = trade_result["data"]
        print(f"✅ Trade placed successfully!")
        print(f"   Ticket: {data.get('order')}")
        print(f"   Price: {data.get('price'):.5f}")
        print(f"   Volume: {data.get('volume')} lot")
    else:
        print(f"❌ Trade failed: {trade_result.get('error')}")
        return
    
    # Step 7: Monitor Position
    print_section("7️⃣  Monitoring Position (5 seconds)")
    time.sleep(5)
    
    position = make_request("GET", f"/position/{SYMBOL}")
    if position.get("success"):
        data = position["data"]
        profit = data.get("profit", 0)
        profit_emoji = "📈" if profit > 0 else "📉" if profit < 0 else "➖"
        print(f"{profit_emoji} Current Profit: ${profit:.2f}")
        print(f"   Price now: {data.get('price_current', 0):.5f}")
    
    # Step 8: Close Position (Interactive)
    print_section("8️⃣  Close Position")
    user_input = input("➡️  Close this position now? (yes/no): ").strip().lower()
    if user_input in ["yes", "y"]:
        close_data = {"symbol": SYMBOL}
        close_result = make_request("POST", "/close", close_data)
        if close_result.get("success"):
            print("✅ Position closed successfully!")
            data = close_result.get("data", {})
            print(f"   Price: {data.get('price', 0):.5f}")
        else:
            print(f"❌ Failed to close: {close_result.get('error')}")
    else:
        print("⏸️  Position remains open")
        print("   You can close it manually in MT5 terminal or via API later")
    
    print_section("✅ Example Complete!")
    print("\nNext steps:")
    print("  • Check your MT5 terminal for trade history")
    print("  • Modify this script for your trading strategy")
    print("  • Review QUICK_START_MT5_TRADING.md for more API examples")

if __name__ == "__main__":
    main()
