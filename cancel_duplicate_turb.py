#!/usr/bin/env python3
"""
Cancel duplicate TURB order and show final order status
"""

import os
from dotenv import load_dotenv
from frontend.components.alpaca_connector import AlpacaConnector

load_dotenv()

def main():
    print("=" * 70)
    print("CANCEL DUPLICATE TURB ORDER")
    print("=" * 70)
    
    # Initialize
    api_key = os.getenv('ALPACA_API_KEY', '').strip()
    secret_key = os.getenv('ALPACA_SECRET_KEY', '').strip()
    alpaca = AlpacaConnector(api_key, secret_key, paper=True)
    
    # Get all orders
    orders = alpaca.get_orders(status="open")
    
    # Find TURB orders
    turb_orders = [o for o in orders if o.get('symbol') == 'TURB']
    
    print(f"\n🔍 Found {len(turb_orders)} TURB order(s):")
    
    if len(turb_orders) < 2:
        print(f"\n✅ No duplicate orders found!")
        print(f"   You have {len(turb_orders)} TURB order, which is correct.")
        return
    
    # Show all TURB orders
    for i, order in enumerate(turb_orders, 1):
        order_id = order.get('id')
        qty = order.get('qty')
        limit_price = order.get('limit_price')
        status = order.get('status')
        created = order.get('created_at', '')[:19]
        
        print(f"\n   Order {i}:")
        print(f"   ID: {order_id}")
        print(f"   Quantity: {qty} shares")
        print(f"   Limit Price: ${float(limit_price):.4f}")
        print(f"   Status: {status}")
        print(f"   Created: {created}")
    
    # Cancel the older one (keep the newer one)
    turb_orders.sort(key=lambda x: x.get('created_at', ''))
    order_to_cancel = turb_orders[0]  # Cancel oldest
    
    print(f"\n⚠️  To avoid buying {len(turb_orders) * 2000} shares instead of 2,000:")
    print(f"   I'll cancel the OLDER duplicate order")
    print(f"\n   Cancelling: {order_to_cancel.get('id')}")
    print(f"   Created at: {order_to_cancel.get('created_at', '')[:19]}")
    
    response = input(f"\n   Proceed with cancellation? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print(f"\n❌ Cancellation aborted")
        return
    
    # Cancel the order
    success = alpaca.cancel_order(order_to_cancel.get('id'))
    
    if success:
        print(f"\n✅ Duplicate order cancelled successfully!")
        print(f"   Cancelled: {order_to_cancel.get('id')[:12]}...")
        
        # Show remaining orders
        remaining_turb = [o for o in turb_orders if o.get('id') != order_to_cancel.get('id')]
        if remaining_turb:
            remaining = remaining_turb[0]
            print(f"\n📋 Remaining TURB order:")
            print(f"   Order ID: {remaining.get('id')[:12]}...")
            print(f"   Quantity: {remaining.get('qty')} shares")
            print(f"   Entry: ${float(remaining.get('limit_price')):.4f}")
            print(f"   Status: {remaining.get('status')}")
    else:
        print(f"\n❌ Failed to cancel order")
    
    # Final summary
    print(f"\n{'=' * 70}")
    print(f"📊 FINAL ORDER SUMMARY")
    print(f"{'=' * 70}")
    
    orders = alpaca.get_orders(status="open")
    
    print(f"\n✅ You have {len(orders)} open order(s):")
    
    for order in orders:
        symbol = order.get('symbol')
        side = order.get('side', '').upper()
        qty = order.get('qty')
        order_type = order.get('type')
        order_class = order.get('order_class', 'simple')
        
        print(f"\n   {symbol}: {side} {qty} shares ({order_type})")
        
        if order_class == 'bracket':
            limit_price = order.get('limit_price')
            if limit_price:
                print(f"   🎯 Entry: ${float(limit_price):.4f}")
            print(f"   🎯 BRACKET (auto stop loss & take profit)")
        elif order_type == 'stop':
            print(f"   🛑 Stop: ${float(order.get('stop_price', 0)):.2f}")
        elif order_type == 'limit':
            print(f"   ✅ Limit: ${float(order.get('limit_price', 0)):.2f}")
    
    print(f"\n{'=' * 70}")
    print(f"✅ CLEANUP COMPLETE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
