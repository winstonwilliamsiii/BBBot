#!/usr/bin/env python3
"""
Place orders for TURB (new position) and add protection to SUPX (existing position)

TURB: 2,000 shares limit order at $0.6881 with 10% stop loss and 20% take profit
SUPX: Add 10% stop loss and 20% take profit to existing position
"""

import os
from dotenv import load_dotenv
from frontend.components.alpaca_connector import AlpacaConnector

load_dotenv()

def main():
    print("=" * 70)
    print("TURB & SUPX ORDER PLACEMENT")
    print("=" * 70)
    
    # Initialize Alpaca
    api_key = os.getenv('ALPACA_API_KEY', '').strip()
    secret_key = os.getenv('ALPACA_SECRET_KEY', '').strip()
    paper = os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
    
    if not api_key or not secret_key:
        print("❌ Missing Alpaca credentials!")
        return
    
    alpaca = AlpacaConnector(api_key, secret_key, paper=paper)
    
    print(f"\n{'PAPER' if paper else 'LIVE'} Trading Mode\n")
    
    # Get account info
    account = alpaca.get_account()
    if not account:
        print("❌ Could not connect to Alpaca")
        return
    
    buying_power = float(account.get('buying_power', 0))
    print(f"✅ Connected!")
    print(f"   Buying Power: ${buying_power:,.2f}\n")
    
    # ========================================================================
    # ORDER 1: TURB - New Bracket Order (Limit Entry)
    # ========================================================================
    
    print("=" * 70)
    print("ORDER 1: TURB - NEW POSITION")
    print("=" * 70)
    
    turb_symbol = "TURB"
    turb_qty = 2000
    turb_entry = 0.6881
    turb_stop_loss = round(turb_entry * 0.90, 4)  # 10% below
    turb_take_profit = round(turb_entry * 1.20, 4)  # 20% above
    turb_cost = turb_qty * turb_entry
    turb_risk = turb_qty * (turb_entry - turb_stop_loss)
    turb_reward = turb_qty * (turb_take_profit - turb_entry)
    
    print(f"\n📋 TURB Order Details:")
    print(f"   Symbol: {turb_symbol}")
    print(f"   Quantity: {turb_qty:,} shares")
    print(f"   Entry: ${turb_entry:.4f} (LIMIT order)")
    print(f"   Stop Loss: ${turb_stop_loss:.4f} (-10%)")
    print(f"   Take Profit: ${turb_take_profit:.4f} (+20%)")
    print(f"\n   Cost: ${turb_cost:,.2f}")
    print(f"   Risk: ${turb_risk:,.2f}")
    print(f"   Reward: ${turb_reward:,.2f}")
    print(f"   R/R Ratio: {turb_reward/turb_risk:.2f}:1")
    
    if turb_cost > buying_power:
        print(f"\n⚠️  WARNING: Order cost (${turb_cost:,.2f}) exceeds buying power (${buying_power:,.2f})")
    
    print(f"\n⚠️  This will place a REAL limit order on your {'PAPER' if paper else 'LIVE'} account!")
    response = input("   Place TURB order? (yes/no): ").strip().lower()
    
    if response == 'yes':
        print(f"\n🚀 Placing TURB bracket order (limit entry at ${turb_entry:.4f})...")
        
        turb_order = alpaca.place_bracket_order(
            symbol=turb_symbol,
            qty=turb_qty,
            side="buy",
            order_type="limit",
            limit_price=turb_entry,
            take_profit_limit_price=turb_take_profit,
            stop_loss_stop_price=turb_stop_loss,
            time_in_force="gtc"
        )
        
        if turb_order:
            print(f"\n✅ TURB order placed successfully!")
            print(f"   Order ID: {turb_order.get('id')}")
            print(f"   Status: {turb_order.get('status')}")
            print(f"   Entry: ${turb_entry:.4f} (limit)")
            print(f"   Stop Loss: ${turb_stop_loss:.4f}")
            print(f"   Take Profit: ${turb_take_profit:.4f}")
            
            if 'legs' in turb_order:
                print(f"\n   📋 Bracket legs created:")
                for leg in turb_order['legs']:
                    if leg.get('stop_price'):
                        print(f"      🛑 Stop Loss leg: ${leg.get('stop_price')}")
                    if leg.get('limit_price') and not leg.get('stop_price'):
                        print(f"      ✅ Take Profit leg: ${leg.get('limit_price')}")
        else:
            print(f"\n❌ TURB order FAILED")
            print("   Check error messages above")
    else:
        print(f"\n❌ TURB order cancelled by user")
    
    # ========================================================================
    # ORDER 2: SUPX - Add Protection to Existing Position
    # ========================================================================
    
    print(f"\n{'=' * 70}")
    print("ORDER 2: SUPX - ADD PROTECTION TO EXISTING POSITION")
    print("=" * 70)
    
    # Get current SUPX position
    supx_position = alpaca.get_position("SUPX")
    
    if not supx_position:
        print(f"\n⚠️  No SUPX position found")
        print("   Cannot add protection to non-existent position")
    else:
        supx_qty = abs(float(supx_position.get('qty', 0)))
        supx_current_price = float(supx_position.get('current_price', 0))
        supx_avg_entry = float(supx_position.get('avg_entry_price', 0))
        supx_unrealized_pl = float(supx_position.get('unrealized_pl', 0))
        
        # Calculate stop loss and take profit from current price
        supx_stop_loss = round(supx_current_price * 0.90, 2)  # 10% below current
        supx_take_profit = round(supx_current_price * 1.20, 2)  # 20% above current
        
        print(f"\n📊 Current SUPX Position:")
        print(f"   Quantity: {supx_qty:.0f} shares")
        print(f"   Avg Entry: ${supx_avg_entry:.2f}")
        print(f"   Current Price: ${supx_current_price:.2f}")
        print(f"   Unrealized P/L: ${supx_unrealized_pl:.2f}")
        
        print(f"\n🛡️  Proposed Protection:")
        print(f"   Stop Loss: ${supx_stop_loss:.2f} (-10% from current)")
        print(f"   Take Profit: ${supx_take_profit:.2f} (+20% from current)")
        
        supx_risk = supx_qty * (supx_current_price - supx_stop_loss)
        supx_reward = supx_qty * (supx_take_profit - supx_current_price)
        
        print(f"\n   Risk: ${supx_risk:.2f}")
        print(f"   Reward: ${supx_reward:.2f}")
        print(f"   R/R Ratio: {supx_reward/supx_risk:.2f}:1")
        
        print(f"\n⚠️  NOTE: For existing positions, we need to place separate orders")
        print(f"   - One stop order (stop loss)")
        print(f"   - One limit order (take profit)")
        print(f"   These will act as OCO (One-Cancels-Other) orders")
        
        response = input(f"\n   Add protection to SUPX? (yes/no): ").strip().lower()
        
        if response == 'yes':
            print(f"\n🚀 Placing SUPX protection orders...")
            
            # Place stop loss order (stops are sell orders for long positions)
            print(f"\n   1/2: Placing stop loss order...")
            stop_order = alpaca.place_order(
                symbol="SUPX",
                qty=supx_qty,
                side="sell",
                order_type="stop",
                stop_price=supx_stop_loss,
                time_in_force="gtc"
            )
            
            if stop_order:
                print(f"   ✅ Stop loss order placed: ${supx_stop_loss:.2f}")
                print(f"      Order ID: {stop_order.get('id')}")
            else:
                print(f"   ❌ Stop loss order FAILED")
            
            # Place take profit order (limit sell)
            print(f"\n   2/2: Placing take profit order...")
            profit_order = alpaca.place_order(
                symbol="SUPX",
                qty=supx_qty,
                side="sell",
                order_type="limit",
                limit_price=supx_take_profit,
                time_in_force="gtc"
            )
            
            if profit_order:
                print(f"   ✅ Take profit order placed: ${supx_take_profit:.2f}")
                print(f"      Order ID: {profit_order.get('id')}")
            else:
                print(f"   ❌ Take profit order FAILED")
            
            if stop_order and profit_order:
                print(f"\n✅ SUPX protection COMPLETE!")
                print(f"   🛑 Stop Loss: ${supx_stop_loss:.2f} (Order: {stop_order.get('id')[:12]}...)")
                print(f"   ✅ Take Profit: ${supx_take_profit:.2f} (Order: {profit_order.get('id')[:12]}...)")
                print(f"\n   ⚠️  IMPORTANT: These are separate orders, not true OCO")
                print(f"   If one fills, you'll need to manually cancel the other")
        else:
            print(f"\n❌ SUPX protection cancelled by user")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    
    print(f"\n{'=' * 70}")
    print("📊 OPEN ORDERS SUMMARY")
    print("=" * 70)
    
    orders = alpaca.get_orders(status="open")
    if orders:
        print(f"\n✅ You have {len(orders)} open order(s):")
        for ord in orders:
            symbol = ord.get('symbol')
            side = ord.get('side', '').upper()
            qty = ord.get('qty')
            order_type = ord.get('type')
            status = ord.get('status')
            order_class = ord.get('order_class', 'simple')
            
            print(f"\n   {symbol}: {side} {qty} shares")
            print(f"   Type: {order_type} | Status: {status}")
            
            if order_class == 'bracket':
                print(f"   🎯 BRACKET ORDER (includes stop loss & take profit)")
                if ord.get('limit_price'):
                    print(f"   Entry: ${float(ord.get('limit_price')):.4f}")
            elif order_type == 'stop':
                print(f"   🛑 Stop Price: ${float(ord.get('stop_price', 0)):.2f}")
            elif order_type == 'limit':
                print(f"   ✅ Limit Price: ${float(ord.get('limit_price', 0)):.2f}")
    else:
        print(f"\n   No open orders")
    
    print(f"\n{'=' * 70}")
    print("✅ ORDER PLACEMENT COMPLETE")
    print("=" * 70)
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Monitor orders in Alpaca dashboard")
    print(f"   2. TURB will fill when price reaches ${turb_entry:.4f}")
    print(f"   3. SUPX stop/profit orders are active")
    print(f"   4. Remember to cancel remaining order if one fills (SUPX)")


if __name__ == "__main__":
    main()
