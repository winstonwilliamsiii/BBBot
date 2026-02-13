#!/usr/bin/env python3
"""
Add take profit order for SUPX position
"""

import os
from dotenv import load_dotenv
from frontend.components.alpaca_connector import AlpacaConnector

load_dotenv()

def main():
    print("=" * 70)
    print("FIXING SUPX TAKE PROFIT ORDER")
    print("=" * 70)
    
    # Initialize Alpaca
    api_key = os.getenv('ALPACA_API_KEY', '').strip()
    secret_key = os.getenv('ALPACA_SECRET_KEY', '').strip()
    
    alpaca = AlpacaConnector(api_key, secret_key, paper=True)
    
    # Check position
    supx_position = alpaca.get_position("SUPX")
    if not supx_position:
        print("\n❌ No SUPX position found")
        return
    
    supx_qty = abs(float(supx_position.get('qty', 0)))
    supx_current_price = float(supx_position.get('current_price', 0))
    
    print(f"\n📊 SUPX Position: {supx_qty} shares @ ${supx_current_price:.2f}")
    
    # Check existing sell orders
    print(f"\n🔍 Checking existing SUPX orders...")
    orders = alpaca.get_orders(status="open")
    supx_sell_orders = [o for o in orders if o.get('symbol') == 'SUPX' and o.get('side') == 'sell']
    
    if supx_sell_orders:
        print(f"\n   Found {len(supx_sell_orders)} existing SUPX sell order(s):")
        total_pending_qty = 0
        for ord in supx_sell_orders:
            qty = float(ord.get('qty', 0))
            total_pending_qty += qty
            print(f"   - {ord.get('type')}: {qty} shares @ ${float(ord.get('stop_price') or ord.get('limit_price') or 0):.2f}")
        
        remaining_qty = supx_qty - total_pending_qty
        print(f"\n   Total pending: {total_pending_qty}")
        print(f"   Remaining available: {remaining_qty}")
        
        if remaining_qty <= 0:
            print(f"\n✅ All shares already have pending sell orders!")
            print(f"   No additional take profit order needed.")
            return
    else:
        remaining_qty = supx_qty
    
    # Place take profit for remaining shares
    take_profit_price = round(supx_current_price * 1.20, 2)
    
    print(f"\n🎯 Placing take profit order:")
    print(f"   Quantity: {remaining_qty} shares")
    print(f"   Take Profit: ${take_profit_price:.2f} (+20%)")
    
    response = input(f"\n   Proceed? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Cancelled")
        return
    
    # Place order
    profit_order = alpaca.place_order(
        symbol="SUPX",
        qty=remaining_qty,
        side="sell",
        order_type="limit",
        limit_price=take_profit_price,
        time_in_force="gtc"
    )
    
    if profit_order:
        print(f"\n✅ Take profit order placed!")
        print(f"   Order ID: {profit_order.get('id')}")
        print(f"   Price: ${take_profit_price:.2f}")
    else:
        print(f"\n❌ Failed to place order")
    
    # Show all orders
    print(f"\n📊 All SUPX Orders:")
    orders = alpaca.get_orders(status="open")
    supx_orders = [o for o in orders if o.get('symbol') == 'SUPX']
    
    for ord in supx_orders:
        order_type = ord.get('type')
        qty = ord.get('qty')
        if order_type == 'stop':
            price = ord.get('stop_price')
            print(f"   🛑 Stop Loss: {qty} shares @ ${float(price):.2f}")
        elif order_type == 'limit':
            price = ord.get('limit_price')
            print(f"   ✅ Take Profit: {qty} shares @ ${float(price):.2f}")


if __name__ == "__main__":
    main()
