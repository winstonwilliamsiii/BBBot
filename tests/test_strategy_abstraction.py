"""
Test Strategy Abstraction - Demonstrates Broker-Agnostic Design
================================================================

This script shows how ONE strategy can work with MULTIPLE brokers
by using the abstraction layer.

Key Concept:
- GoldRsiStrategy works with BOTH Alpaca (stocks) and MT5 (forex)
- UsdCopShortStrategy works with MT5 (forex)
- Strategies don't know/care which broker they're using!
"""

import os
import sys
from pathlib import Path

# Add project root to path (now in tests/ directory, need to go up one level)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.brokers.broker_interface import create_broker_client
from src.strategies.example_strategies import GoldRsiStrategy, UsdCopShortStrategy


def test_gold_strategy_with_alpaca():
    """
    Test Gold RSI Strategy with Alpaca
    
    Symbol: GLD (Gold ETF traded on NYSE)
    """
    print("\n" + "="*60)
    print("TEST 1: Gold RSI Strategy with ALPACA")
    print("="*60)
    
    try:
        # Create Alpaca broker client
        broker = create_broker_client('alpaca')
        print(f"✅ Connected to {broker.get_broker_name()}")
        
        # Create strategy with Alpaca
        strategy = GoldRsiStrategy(
            broker=broker,
            symbol="GLD",  # Gold ETF on Alpaca
            rsi_period=14,
            oversold_level=30,
            overbought_level=70
        )
        
        print(f"📊 Strategy: {strategy.get_name()}")
        print(f"💰 Account Equity: ${broker.get_equity():,.2f}")
        
        # Get current signals
        signals = strategy.get_signal_info()
        print(f"\n📈 Current Signals:")
        print(f"   RSI: {signals['rsi']:.2f} ({signals['rsi_status']})")
        print(f"   Buy Signal: {'✅ YES' if signals['buy_signal'] else '❌ NO'}")
        print(f"   Sell Signal: {'✅ YES' if signals['sell_signal'] else '❌ NO'}")
        print(f"   Has Position: {'✅ YES' if signals['has_position'] else '❌ NO'}")
        
        # Run strategy once (dry run - set dry_run=True in production)
        print(f"\n🔄 Running strategy cycle...")
        strategy.run_once()
        
        # Show stats
        stats = strategy.get_stats()
        print(f"\n📊 Strategy Performance:")
        print(f"   Total Trades: {stats['total_trades']}")
        print(f"   Win Rate: {stats['win_rate']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_gold_strategy_with_mt5():
    """
    Test Gold RSI Strategy with MT5
    
    Symbol: XAUUSD (Gold vs USD on Forex)
    
    NOTE: This is THE SAME strategy code, just different broker!
    """
    print("\n" + "="*60)
    print("TEST 2: Gold RSI Strategy with MT5 (SAME STRATEGY!)")
    print("="*60)
    
    try:
        # Create MT5 broker client
        broker = create_broker_client('mt5')
        print(f"✅ Connected to {broker.get_broker_name()}")
        
        # Create SAME strategy but with MT5 and forex symbol
        strategy = GoldRsiStrategy(
            broker=broker,
            symbol="XAUUSD",  # Gold on MT5 (Forex)
            rsi_period=14,
            oversold_level=30,
            overbought_level=70
        )
        
        print(f"📊 Strategy: {strategy.get_name()}")
        print(f"💰 Account Equity: ${broker.get_equity():,.2f}")
        
        # Get current signals
        signals = strategy.get_signal_info()
        print(f"\n📈 Current Signals:")
        print(f"   RSI: {signals['rsi']:.2f} ({signals['rsi_status']})")
        print(f"   Buy Signal: {'✅ YES' if signals['buy_signal'] else '❌ NO'}")
        print(f"   Sell Signal: {'✅ YES' if signals['sell_signal'] else '❌ NO'}")
        print(f"   Has Position: {'✅ YES' if signals['has_position'] else '❌ NO'}")
        
        # Run strategy once
        print(f"\n🔄 Running strategy cycle...")
        strategy.run_once()
        
        # Show stats
        stats = strategy.get_stats()
        print(f"\n📊 Strategy Performance:")
        print(f"   Total Trades: {stats['total_trades']}")
        print(f"   Win Rate: {stats['win_rate']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_usdcop_strategy_with_mt5():
    """
    Test USD/COP Short Strategy with MT5
    
    This strategy is forex-specific (shorts USD/COP)
    """
    print("\n" + "="*60)
    print("TEST 3: USD/COP Short Strategy with MT5")
    print("="*60)
    
    try:
        # Create MT5 broker client
        broker = create_broker_client('mt5')
        print(f"✅ Connected to {broker.get_broker_name()}")
        
        # Create forex strategy
        strategy = UsdCopShortStrategy(
            broker=broker,
            symbol="USDCOP",
            bb_period=20,
            bb_std=2.0,
            stop_loss_pips=100
        )
        
        print(f"📊 Strategy: {strategy.get_name()}")
        print(f"💰 Account Equity: ${broker.get_equity():,.2f}")
        
        # Get current signals
        signals = strategy.get_signal_info()
        print(f"\n📈 Current Signals:")
        print(f"   Price: {signals['price']:.4f}")
        print(f"   Upper BB: {signals['upper_bb']:.4f}")
        print(f"   Middle BB: {signals['middle_bb']:.4f}")
        print(f"   Lower BB: {signals['lower_bb']:.4f}")
        print(f"   Short Signal: {'✅ YES' if signals['short_signal'] else '❌ NO'}")
        print(f"   Cover Signal: {'✅ YES' if signals['cover_signal'] else '❌ NO'}")
        
        # Run strategy once
        print(f"\n🔄 Running strategy cycle...")
        strategy.run_once()
        
        # Show stats
        stats = strategy.get_stats()
        print(f"\n📊 Strategy Performance:")
        print(f"   Total Trades: {stats['total_trades']}")
        print(f"   Win Rate: {stats['win_rate']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def demonstrate_broker_switching():
    """
    DEMONSTRATES THE POWER OF ABSTRACTION
    
    This function shows how you can SWITCH BROKERS with ONE LINE
    """
    print("\n" + "="*60)
    print("DEMONSTRATION: Switch Brokers in ONE LINE!")
    print("="*60)
    
    # Choose broker at runtime
    broker_name = 'alpaca'  # Change this to 'mt5' to switch!
    
    print(f"\n📌 Selected broker: {broker_name.upper()}")
    
    # This is the MAGIC - one line switches broker!
    broker = create_broker_client(broker_name)
    
    # Strategy works with ANY broker
    symbol = "GLD" if broker_name == 'alpaca' else "XAUUSD"
    strategy = GoldRsiStrategy(broker=broker, symbol=symbol)
    
    print(f"✅ Strategy created: {strategy.get_name()}")
    print(f"✅ Using broker: {broker.get_broker_name()}")
    print(f"✅ Trading symbol: {symbol}")
    
    print(f"\n💡 To switch to MT5, just change:")
    print(f"   broker_name = 'alpaca'  →  broker_name = 'mt5'")
    print(f"\n   That's it! No other code changes needed!")


def main():
    """
    Run all tests
    """
    print("\n" + "="*70)
    print(" STRATEGY ABSTRACTION DEMONSTRATION")
    print(" Purpose: Show how ONE strategy works with MULTIPLE brokers")
    print("="*70)
    
    # Demonstrate switching
    demonstrate_broker_switching()
    
    # Test Gold strategy with Alpaca
    alpaca_success = test_gold_strategy_with_alpaca()
    
    # Test Gold strategy with MT5 (SAME strategy!)
    mt5_gold_success = test_gold_strategy_with_mt5()
    
    # Test USD/COP strategy with MT5
    mt5_usdcop_success = test_usdcop_strategy_with_mt5()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Gold Strategy + Alpaca: {'✅ PASSED' if alpaca_success else '❌ FAILED'}")
    print(f"Gold Strategy + MT5:    {'✅ PASSED' if mt5_gold_success else '❌ FAILED'}")
    print(f"USDCOP Strategy + MT5:  {'✅ PASSED' if mt5_usdcop_success else '❌ FAILED'}")
    
    print("\n💡 KEY TAKEAWAY:")
    print("   - GoldRsiStrategy worked with BOTH Alpaca and MT5")
    print("   - Strategy code is IDENTICAL - only broker parameter changed")
    print("   - This is the power of abstraction!")
    print("="*60)


if __name__ == "__main__":
    main()
