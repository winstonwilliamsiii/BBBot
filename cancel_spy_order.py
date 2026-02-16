#!/usr/bin/env python3
"""
Cancel SPY test order - keeping only TURB and SUPX positions
"""

import os
from dotenv import load_dotenv
from frontend.components.alpaca_connector import AlpacaConnector

load_dotenv()

def main():
    print("=" * 70)
    print("CANCEL SPY ORDER")
    print("=" * 70)
    
    api_key = os.getenv('ALPACA_API_KEY', '').strip()
    secret_key = os.getenv('ALPACA_SECRET_KEY', '').strip()
    alpaca = AlpacaConnector(api_key, secret_key, paper=True)
    
    # Get all orders
    orders = alpaca.get_orders(status="open")
    
    # Find SPY orders
    spy_orders = [o for o in orders if o.get('symbol') == 'SPY']
    
    if not spy_orders:
        print("\n✅ No SPY orders found")
        return
    
    print(f"\n🔍 Found {len(spy_orders)} SPY order(s):")
    
    for order in spy_orders:
        order_id = order.get('id')
        qty = order.get('qty')
        order_type = order.get('type')
        status = order.get('status')
        
        print(f"\n   Order ID: {order_id[:12]}...")
        print(f"   Quantity: {qty} shares")
        print(f"   Type: {order_type}")
        print(f"   Status: {status}")
        
        print(f"\n   Cancelling SPY order...")
        success = alpaca.cancel_order(order_id)
        
        if success:
            print(f"   ✅ Cancelled: {order_id[:12]}...")
        else:
            print(f"   ❌ Failed to cancel: {order_id[:12]}...")
    
    # Show final orders
    print(f"\n{'=' * 70}")
    print(f"📊 REMAINING ORDERS")
    print(f"{'=' * 70}")
    
    orders = alpaca.get_orders(status="open")
    
    if orders:
        print(f"\n✅ Active orders ({len(orders)}):")
        for order in orders:
            symbol = order.get('symbol')
            side = order.get('side', '').upper()
            qty = order.get('qty')
            print(f"   • {symbol}: {side} {qty} shares")
    else:
        print("\n   No open orders")
    
    print(f"\n{'=' * 70}")
    print(f"✅ CLEANUP COMPLETE - SPY ORDER CANCELLED")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
