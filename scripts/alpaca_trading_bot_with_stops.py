#!/usr/bin/env python3
"""
Simple Alpaca Trading Bot with Automatic Stop Loss & Take Profit
This replaces basic orders with bracket orders for better risk management
"""

import os
from dotenv import load_dotenv
from frontend.components.alpaca_connector import AlpacaConnector

load_dotenv()


def place_trade_with_risk_management(
    alpaca: AlpacaConnector,
    symbol: str,
    qty: float,
    entry_price: float,
    stop_loss_percent: float = 0.02,   # 2% stop loss
    take_profit_percent: float = 0.04  # 4% take profit (2:1 reward/risk)
):
    """
    Place a BUY order with automatic stop loss and take profit
    
    Args:
        alpaca: AlpacaConnector instance
        symbol: Stock symbol (e.g., "AAPL")
        qty: Number of shares
        entry_price: Current market price
        stop_loss_percent: Percentage below entry for stop loss (0.02 = 2%)
        take_profit_percent: Percentage above entry for take profit (0.04 = 4%)
    
    Returns:
        Order dict or None
    """
    # Calculate stop loss and take profit prices
    stop_loss_price = round(entry_price * (1 - stop_loss_percent), 2)
    take_profit_price = round(entry_price * (1 + take_profit_percent), 2)
    
    # Calculate dollar amounts
    risk_amount = (entry_price - stop_loss_price) * qty
    reward_amount = (take_profit_price - entry_price) * qty
    reward_risk_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"📈 PLACING TRADE: {symbol}")
    print(f"{'='*60}")
    print(f"Entry Price: ${entry_price:.2f}")
    print(f"Quantity: {qty} shares")
    print(f"Stop Loss: ${stop_loss_price:.2f} (-{stop_loss_percent*100:.1f}%)")
    print(f"Take Profit: ${take_profit_price:.2f} (+{take_profit_percent*100:.1f}%)")
    print(f"\nRisk: ${risk_amount:.2f}")
    print(f"Reward: ${reward_amount:.2f}")
    print(f"Reward/Risk Ratio: {reward_risk_ratio:.2f}:1")
    print(f"{'='*60}\n")
    
    # Place bracket order
    order = alpaca.place_bracket_order(
        symbol=symbol,
        qty=qty,
        side="buy",
        order_type="market",
        take_profit_limit_price=take_profit_price,
        stop_loss_stop_price=stop_loss_price,
        time_in_force="gtc"
    )
    
    if order:
        print(f"✅ Order placed successfully!")
        print(f"   Order ID: {order.get('id')}")
        print(f"   Status: {order.get('status')}")
        print(f"\n💡 Stop Loss and Take Profit are now ACTIVE")
        print(f"   The position will automatically close when:")
        print(f"   • Price drops to ${stop_loss_price:.2f} (stop loss)")
        print(f"   • Price rises to ${take_profit_price:.2f} (take profit)")
    else:
        print(f"❌ Failed to place order")
    
    return order


def main():
    """Main trading bot logic"""
    
    # Initialize Alpaca
    api_key = os.getenv('ALPACA_API_KEY', '').strip()
    secret_key = os.getenv('ALPACA_SECRET_KEY', '').strip()
    paper = os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
    
    if not api_key or not secret_key:
        print("❌ Missing Alpaca credentials!")
        return
    
    alpaca = AlpacaConnector(api_key, secret_key, paper=paper)
    
    print(f"\n🤖 ALPACA TRADING BOT")
    print(f"Mode: {'PAPER' if paper else 'LIVE'} Trading\n")
    
    # Get account info
    account = alpaca.get_account()
    if not account:
        print("❌ Could not connect to Alpaca")
        return
    
    buying_power = float(account.get('buying_power', 0))
    print(f"✅ Connected!")
    print(f"   Buying Power: ${buying_power:,.2f}\n")
    
    # Example: Buy SPY with auto stop loss/take profit
    symbol = "SPY"
    
    # Get current price
    try:
        quote = alpaca.get_latest_quote(symbol)
        current_price = float(quote['quote']['ap'])
    except Exception as e:
        print(f"❌ Could not get price for {symbol}: {e}")
        return
    
    # Calculate position size (risk 1% of buying power)
    risk_amount = buying_power * 0.01
    stop_loss_percent = 0.02  # 2% stop loss
    price_drop = current_price * stop_loss_percent
    qty = int(risk_amount / price_drop)
    
    if qty < 1:
        print(f"❌ Insufficient buying power for this trade")
        return
    
    print(f"💰 Current {symbol} price: ${current_price:.2f}")
    print(f"📊 Position size: {qty} shares (${qty * current_price:.2f})")
    print(f"🎯 Risk per trade: ${risk_amount:.2f} (1% of buying power)\n")
    
    # Place trade with risk management
    order = place_trade_with_risk_management(
        alpaca=alpaca,
        symbol=symbol,
        qty=qty,
        entry_price=current_price,
        stop_loss_percent=0.02,   # 2% stop loss
        take_profit_percent=0.04  # 4% take profit
    )
    
    if order:
        print(f"\n✅ TRADE EXECUTED WITH PROTECTION")
        print(f"   Your risk is LIMITED to 2%")
        print(f"   Your profit target is 4%")
        print(f"   Set and forget - Alpaca handles the rest! 🎯")


if __name__ == "__main__":
    main()
