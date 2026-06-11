#!/usr/bin/env python3
"""
Check current position status for TURB and all open orders
"""

import os
from dotenv import load_dotenv
from frontend.components.alpaca_connector import AlpacaConnector

load_dotenv()

def main():
    print("=" * 70)
    print("TURB POSITION & ORDER STATUS CHECK")
    print("=" * 70)
    
    # Initialize
    api_key = os.getenv('ALPACA_API_KEY', '').strip()
    secret_key = os.getenv('ALPACA_SECRET_KEY', '').strip()
    alpaca = AlpacaConnector(api_key, secret_key, paper=True)
    
    # Check TURB position
    print("\n📊 CHECKING TURB POSITION:")
    print("-" * 70)
    turb_position = alpaca.get_position("TURB")
    
    if turb_position:
        qty = turb_position.get('qty', 0)
        avg_entry = float(turb_position.get('avg_entry_price', 0))
        current_price = float(turb_position.get('current_price', 0))
        unrealized_pl = float(turb_position.get('unrealized_pl', 0))
        unrealized_plpc = float(turb_position.get('unrealized_plpc', 0)) * 100
        
        print(f"✅ POSITION EXISTS")
        print(f"   Symbol: TURB")
        print(f"   Quantity: {qty} shares")
        print(f"   Avg Entry: ${avg_entry:.4f}")
        print(f"   Current Price: ${current_price:.4f}")
        print(f"   Unrealized P/L: ${unrealized_pl:.2f} ({unrealized_plpc:+.2f}%)")
    else:
        print(f"❌ NO TURB POSITION FOUND")
    
    # Check all open orders
    print("\n📋 CHECKING ALL OPEN ORDERS:")
    print("-" * 70)
    orders = alpaca.get_orders(status="open")
    
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
    
    print("\n" + "=" * 70)
    print("STATUS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
