#!/usr/bin/env python3
"""
Check current position status for TURB and all open orders - Direct API version
"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

def get_alpaca_headers():
    api_key = os.getenv('ALPACA_API_KEY', '').strip()
    secret_key = os.getenv('ALPACA_SECRET_KEY', '').strip()
    
    return {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': secret_key,
        'Content-Type': 'application/json'
    }

def main():
    print("=" * 70)
    print("TURB POSITION & ORDER STATUS CHECK")
    print("=" * 70)
    
    base_url = "https://paper-api.alpaca.markets/v2"
    headers = get_alpaca_headers()
    
    # Check TURB position
    print("\n📊 CHECKING TURB POSITION:")
    print("-" * 70)
    
    try:
        response = requests.get(f"{base_url}/positions/TURB", headers=headers)
        
        if response.status_code == 200:
            position = response.json()
            qty = position.get('qty', 0)
            avg_entry = float(position.get('avg_entry_price', 0))
            current_price = float(position.get('current_price', 0))
            unrealized_pl = float(position.get('unrealized_pl', 0))
            unrealized_plpc = float(position.get('unrealized_plpc', 0)) * 100
            
            print(f"✅ POSITION EXISTS")
            print(f"   Symbol: TURB")
            print(f"   Quantity: {qty} shares")
            print(f"   Avg Entry: ${avg_entry:.4f}")
            print(f"   Current Price: ${current_price:.4f}")
            print(f"   Unrealized P/L: ${unrealized_pl:.2f} ({unrealized_plpc:+.2f}%)")
        elif response.status_code == 404:
            print(f"❌ NO TURB POSITION FOUND")
        else:
            print(f"⚠️  API Error: {response.status_code}")
            print(f"   {response.text}")
    except Exception as e:
        print(f"❌ Error checking position: {e}")
    
    # Check all open orders
    print("\n📋 CHECKING ALL OPEN ORDERS:")
    print("-" * 70)
    
    try:
        response = requests.get(f"{base_url}/orders?status=open", headers=headers)
        
        if response.status_code == 200:
            orders = response.json()
            
            if not orders:
                print("✅ No open orders")
            else:
                print(f"Found {len(orders)} open order(s):\n")
                
                for i, order in enumerate(orders, 1):
                    symbol = order.get('symbol')
                    order_id = order.get('id')
                    side = order.get('side', '').upper()
                    qty = order.get('qty')
                    order_type = order.get('type', '')
                    order_class = order.get('order_class', 'simple')
                    status = order.get('status')
                    limit_price = order.get('limit_price')
                    stop_price = order.get('stop_price')
                    created = order.get('created_at', '')[:19]
                    
                    print(f"{i}. {symbol} - {side} {qty} shares")
                    print(f"   ID: {order_id}")
                    print(f"   Type: {order_type} ({order_class})")
                    print(f"   Status: {status}")
                    
                    if limit_price:
                        print(f"   Limit Price: ${float(limit_price):.4f}")
                    if stop_price:
                        print(f"   Stop Price: ${float(stop_price):.4f}")
                    
                    print(f"   Created: {created}")
                    print()
                
                # Check TURB orders specifically
                turb_orders = [o for o in orders if o.get('symbol') == 'TURB']
                
                if turb_orders:
                    print("\n⚠️  TURB-SPECIFIC ORDERS:")
                    print("-" * 70)
                    print(f"Found {len(turb_orders)} TURB order(s):\n")
                    
                    for order in turb_orders:
                        order_id = order.get('id')
                        side = order.get('side', '').upper()
                        qty = order.get('qty')
                        order_class = order.get('order_class', 'simple')
                        status = order.get('status')
                        
                        print(f"   {side} {qty} shares ({order_class})")
                        print(f"   ID: {order_id}")
                        print(f"   Status: {status}")
        else:
            print(f"⚠️  API Error: {response.status_code}")
            print(f"   {response.text}")
    except Exception as e:
        print(f"❌ Error checking orders: {e}")
    
    print("\n" + "=" * 70)
    print("STATUS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
