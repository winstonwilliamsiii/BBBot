"""
Simple Diagram: Strategy Abstraction Pattern
=============================================

This shows how ONE strategy works with MULTIPLE brokers
"""

print("""
╔══════════════════════════════════════════════════════════════╗
║  THE PROBLEM: Different brokers have different APIs          ║
╚══════════════════════════════════════════════════════════════╝

❌ Without Abstraction (Code Duplication):

    [GoldStrategy]
         │
    ┌────┴────┐
    │         │
[Alpaca]   [MT5]     ← Each needs different code!
    │         │
alpaca_api  mt5.order_send()  ← Different API calls


╔══════════════════════════════════════════════════════════════╗
║  THE SOLUTION: Abstract broker interface                     ║
╚══════════════════════════════════════════════════════════════╝

✅ With Abstraction (One Strategy, Any Broker):

              [GoldStrategy]
                    │
                    │ Uses generic methods:
                    │ • broker.place_order()
                    │ • broker.get_positions()
                    │ • broker.get_historical_prices()
                    │
              [BrokerClient]  ← Universal Interface
                    │
        ┌───────────┼───────────┐
        │           │           │
    [Alpaca]     [MT5]      [IBKR]    ← Translate to specific APIs
        │           │           │
  alpaca_api   mt5.order  ibkr_api


╔══════════════════════════════════════════════════════════════╗
║  CODE COMPARISON                                             ║
╚══════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────┐
│ Strategy Code (Broker-Agnostic)                              │
└─────────────────────────────────────────────────────────────┘

class GoldRsiStrategy(BaseStrategy):
    def should_enter(self):
        # Get data (works with ANY broker!)
        bars = self.broker.get_historical_prices(self.symbol, "1D")
        rsi = calculate_rsi(bars)
        return rsi < 30  # Oversold

    def should_exit(self, position):
        bars = self.broker.get_historical_prices(self.symbol, "1D")
        rsi = calculate_rsi(bars)
        return rsi > 70  # Overbought


┌─────────────────────────────────────────────────────────────┐
│ Using Strategy with Alpaca                                   │
└─────────────────────────────────────────────────────────────┘

broker = create_broker_client('alpaca')  ← Choose Alpaca
strategy = GoldRsiStrategy(broker, symbol="GLD")
strategy.run_once()


┌─────────────────────────────────────────────────────────────┐
│ Using SAME Strategy with MT5 (Only 1 line changed!)         │
└─────────────────────────────────────────────────────────────┘

broker = create_broker_client('mt5')  ← Choose MT5
strategy = GoldRsiStrategy(broker, symbol="XAUUSD")
strategy.run_once()  # ← Same code!


╔══════════════════════════════════════════════════════════════╗
║  KEY BENEFITS                                                ║
╚══════════════════════════════════════════════════════════════╝

✅ Write strategy ONCE → Works with ALL brokers
✅ Switch brokers by changing ONE line
✅ Test with paper trading → Deploy to live account easily
✅ Add new broker → All strategies work automatically


╔══════════════════════════════════════════════════════════════╗
║  EXAMPLE: Switching Brokers                                  ║
╚══════════════════════════════════════════════════════════════╝

# Development (Paper Trading)
broker = create_broker_client('alpaca')  # ← Paper account
strategy = GoldRsiStrategy(broker, "GLD")

# Production (Live Trading)
broker = create_broker_client('mt5')  # ← Change this line only!
strategy = GoldRsiStrategy(broker, "XAUUSD")


╔══════════════════════════════════════════════════════════════╗
║  FILES YOU CREATED                                           ║
╚══════════════════════════════════════════════════════════════╝

📁 frontend/utils/
   └── broker_interface.py  ← Abstraction layer
       ├── BrokerClient (ABC)  ← Interface definition
       ├── AlpacaBrokerClient  ← Wraps Alpaca API
       └── MT5BrokerClient     ← Wraps MT5 API

📁 trading/strategies/
   ├── base_strategy.py  ← Strategy framework
   └── example_strategies.py  ← Your strategies
       ├── GoldRsiStrategy  ← Works with any broker!
       └── UsdCopShortStrategy  ← Works with any broker!


╔══════════════════════════════════════════════════════════════╗
║  TRY IT YOURSELF                                             ║
╚══════════════════════════════════════════════════════════════╝

Run this command to see it in action:

    python test_strategy_abstraction.py

You'll see:
• GoldRsiStrategy running on ALPACA (stocks)
• GoldRsiStrategy running on MT5 (forex)
• Same strategy code, different brokers!

""")
