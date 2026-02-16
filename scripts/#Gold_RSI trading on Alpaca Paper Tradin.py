"""
Gold RSI Trading Strategy on Alpaca Paper Trading Account.

Implements RSI-based trading signals for GLD (gold proxy ETF) using:
- 14-period RSI for overbought/oversold conditions
- Position sizing based on account equity
- Automated order execution on Alpaca paper trading
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import pandas as pd
from alpaca_trade_api import REST, TimeFrame
from frontend.components.alpaca_connector import AlpacaConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Alpaca API Configuration
ALPACA_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

if not ALPACA_KEY or not ALPACA_SECRET:
    logger.error("Missing Alpaca API credentials in environment variables")
    raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set")

try:
    alpaca = REST(ALPACA_KEY, ALPACA_SECRET, base_url=ALPACA_BASE_URL)
    # Initialize AlpacaConnector for bracket orders
    alpaca_connector = AlpacaConnector(ALPACA_KEY, ALPACA_SECRET, paper=True)
except Exception as e:
    logger.error(f"Failed to initialize Alpaca API client: {e}")
    raise

# Trading Parameters
GOLD_SYMBOL = "GLD"  # Gold proxy ETF (highly correlated with gold futures)
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70  # RSI threshold for selling signal
RSI_OVERSOLD = 30    # RSI threshold for buying signal
RISK_PER_TRADE = 0.01  # 1% of account equity per trade
LOOKBACK_PERIOD = 50  # Days of historical data for RSI calculation
MIN_PRICE = 1.0  # Minimum price threshold for trading

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def compute_rsi(close_series: pd.Series, period: int = RSI_PERIOD) -> float:
    """
    Compute Relative Strength Index (RSI) for a price series.
    
    Args:
        close_series: Pandas Series of closing prices
        period: RSI calculation period (default: 14)
    
    Returns:
        float: RSI value (0-100)
    
    Raises:
        ValueError: If series length is insufficient for RSI calculation
    """
    if len(close_series) < period + 1:
        raise ValueError(f"Series length ({len(close_series)}) must be > period ({period})")
    
    try:
        delta = close_series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / (avg_loss + 1e-9)  # Avoid division by zero
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1])
    except Exception as e:
        logger.error(f"Error computing RSI: {e}")
        raise


def get_historical_data(symbol: str, lookback: int = LOOKBACK_PERIOD) -> Optional[pd.DataFrame]:
    """
    Fetch historical OHLC data from Alpaca API.
    
    Args:
        symbol: Trading symbol (e.g., 'GLD')
        lookback: Number of days of historical data
    
    Returns:
        DataFrame with OHLC data or None on failure
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback)
        
        bars = alpaca.get_bars(
            symbol,
            TimeFrame.Day,
            start=start_date.isoformat(),
            end=end_date.isoformat()
        )
        
        if bars is None or len(bars) == 0:
            logger.warning(f"No historical data available for {symbol}")
            return None
        
        df = bars.df
        logger.info(f"Retrieved {len(df)} bars for {symbol}")
        return df
    
    except Exception as e:
        logger.error(f"Failed to fetch historical data for {symbol}: {e}")
        return None


def get_account_info() -> Optional[dict]:
    """
    Retrieve current account information.
    
    Returns:
        Dictionary with account details or None on failure
    """
    try:
        account = alpaca.get_account()
        return {
            'buying_power': float(account.buying_power),
            'portfolio_value': float(account.portfolio_value),
            'cash': float(account.cash),
            'equity': float(account.equity)
        }
    except Exception as e:
        logger.error(f"Failed to fetch account info: {e}")
        return None


def get_current_position(symbol: str) -> Optional[float]:
    """
    Get current position quantity for a symbol.
    
    Args:
        symbol: Trading symbol
    
    Returns:
        Position quantity or None if no position exists
    """
    try:
        position = alpaca.get_position(symbol)
        return float(position.qty)
    except Exception:
        return None


def calculate_position_size(equity: float, current_price: float) -> int:
    """
    Calculate position size based on risk management rules.
    
    Args:
        equity: Account equity
        current_price: Current asset price
    
    Returns:
        Position size in shares (rounded down to nearest integer)
    """
    risk_amount = equity * RISK_PER_TRADE
    position_size = int(risk_amount / current_price)
    return max(1, position_size)  # Ensure at least 1 share


def place_order(symbol: str, qty: int, side: str, current_price: Optional[float] = None) -> Optional[dict]:
    """
    Place a bracket order with automatic stop loss and take profit.
    
    Args:
        symbol: Trading symbol
        qty: Order quantity
        side: 'buy' or 'sell'
        current_price: Current market price (required for bracket orders)
    
    Returns:
        Order details or None on failure
    """
    if qty <= 0:
        logger.warning(f"Invalid order quantity: {qty}")
        return None
    
    try:
        # For BUY orders with bracket protection
        if side.lower() == 'buy':
            if current_price is None:
                # Get current price from latest trade (more accurate than quote)
                try:
                    latest_trade = alpaca_connector.get_latest_trade(symbol)
                    current_price = float(latest_trade['trade']['p'])
                except:
                    # Fallback to bar close price
                    latest_bar = alpaca.get_latest_bar(symbol)
                    current_price = float(latest_bar.c)
            
            # Calculate stop loss and take profit (2% stop, 4% profit)
            stop_loss_price = round(current_price * 0.98, 2)
            take_profit_price = round(current_price * 1.04, 2)
            
            logger.info(f"Placing bracket order: {symbol} {side.upper()} {qty}")
            logger.info(f"  Entry: ~${current_price:.2f}")
            logger.info(f"  Stop Loss: ${stop_loss_price:.2f} (-2%)")
            logger.info(f"  Take Profit: ${take_profit_price:.2f} (+4%)")
            
            # Place bracket order
            order = alpaca_connector.place_bracket_order(
                symbol=symbol,
                qty=qty,
                side=side,
                order_type='market',
                take_profit_limit_price=take_profit_price,
                stop_loss_stop_price=stop_loss_price,
                time_in_force='gtc'
            )
            
            if order:
                logger.info(f"✅ Bracket order placed: {symbol} {side.upper()} {qty} - Order ID: {order.get('id')}")
                return {
                    'id': order.get('id'),
                    'symbol': order.get('symbol'),
                    'qty': float(order.get('qty', qty)),
                    'side': order.get('side'),
                    'status': order.get('status'),
                    'stop_loss': stop_loss_price,
                    'take_profit': take_profit_price
                }
        else:
            # For SELL orders (close position), use simple market order
            order = alpaca.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='day'
            )
            logger.info(f"Order placed: {side.upper()} {qty} {symbol} - Order ID: {order.id}")
            return {
                'id': order.id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side,
                'status': order.status
            }
    except Exception as e:
        logger.error(f"Failed to place {side} order for {symbol}: {e}")
        return None


# ============================================================================
# MAIN TRADING LOGIC
# ============================================================================

def execute_trading_strategy(symbol: str = GOLD_SYMBOL) -> Tuple[bool, str]:
    """
    Execute the RSI-based trading strategy.
    
    Args:
        symbol: Trading symbol (default: GLD)
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    logger.info(f"Executing trading strategy for {symbol}")
    
    # Get account info
    account = get_account_info()
    if not account:
        return False, "Failed to retrieve account information"
    
    logger.info(f"Account equity: ${account['equity']:.2f}, Buying power: ${account['buying_power']:.2f}")
    
    # Get current price
    try:
        latest_bar = alpaca.get_latest_bar(symbol)
        current_price = float(latest_bar.c)
        logger.info(f"Current {symbol} price: ${current_price:.2f}")
    except Exception as e:
        return False, f"Failed to fetch current price: {e}"
    
    if current_price < MIN_PRICE:
        return False, f"Price ${current_price:.2f} below minimum threshold of ${MIN_PRICE}"
    
    # Get historical data and compute RSI
    hist_data = get_historical_data(symbol)
    if hist_data is None or len(hist_data) < RSI_PERIOD + 1:
        return False, f"Insufficient historical data for RSI calculation"
    
    try:
        rsi = compute_rsi(hist_data['close'], RSI_PERIOD)
        logger.info(f"{symbol} RSI(14): {rsi:.2f}")
    except Exception as e:
        return False, f"Failed to compute RSI: {e}"
    
    # Check for trading signals
    current_position = get_current_position(symbol)
    position_qty = float(current_position) if current_position else 0.0
    
    # SELL SIGNAL: RSI > 70 (overbought)
    if rsi > RSI_OVERBOUGHT and position_qty > 0:
        logger.info(f"SELL SIGNAL: RSI {rsi:.2f} > {RSI_OVERBOUGHT}")
        order = place_order(symbol, int(position_qty), 'sell')
        if order:
            return True, f"Sell order executed: {order['qty']} shares at RSI {rsi:.2f}"
        else:
            return False, "Failed to execute sell order"
    
    # BUY SIGNAL: RSI < 30 (oversold)
    elif rsi < RSI_OVERSOLD and position_qty == 0:
        logger.info(f"BUY SIGNAL: RSI {rsi:.2f} < {RSI_OVERSOLD}")
        position_size = calculate_position_size(account['equity'], current_price)
        order = place_order(symbol, position_size, 'buy', current_price)
        if order:
            return True, f"Buy order executed: {order['qty']} shares at RSI {rsi:.2f}"
        else:
            return False, "Failed to execute buy order"
    
    else:
        status = f"No signal: RSI {rsi:.2f}, Position: {position_qty} shares"
        logger.info(status)
        return True, status


def main():
    """Main entry point for the trading bot."""
    logger.info("=" * 70)
    logger.info("Gold RSI Trading Strategy - Paper Trading")
    logger.info("=" * 70)
    
    success, message = execute_trading_strategy(GOLD_SYMBOL)
    
    if success:
        logger.info(f"✓ Strategy execution successful: {message}")
    else:
        logger.error(f"✗ Strategy execution failed: {message}")
    
    logger.info("=" * 70)


# ============================================================================
# STRATEGY FRAMEWORK - Generalized for Mansa/Bentley Orchestration
# ============================================================================

class TradingStrategy:
    """
    Base class for RSI-based trading strategies.
    Designed for easy extension to multiple symbols and data sources.
    """
    
    def __init__(self, symbol: str, rsi_period: int = 14, 
                 overbought: float = 70, oversold: float = 30):
        self.symbol = symbol
        self.rsi_period = rsi_period
        self.overbought = overbought
        self.oversold = oversold
        self.last_signal: Optional[str] = None
        self.last_rsi: Optional[float] = None
        self.data_source: str = "unknown"
    
    def compute_signal(self, rsi: float) -> str:
        """
        Generate trading signal based on RSI value.
        
        Args:
            rsi: RSI value (0-100)
        
        Returns:
            Signal: 'BUY', 'SELL', or 'HOLD'
        """
        if rsi > self.overbought:
            return "SELL"
        elif rsi < self.oversold:
            return "BUY"
        else:
            return "HOLD"
    
    def execute_signal(self, signal: str, current_price: float, 
                      account_equity: float) -> bool:
        """
        Execute trading action based on signal.
        Override for custom execution logic per strategy.
        
        Args:
            signal: Trading signal
            current_price: Current asset price
            account_equity: Current account equity
        
        Returns:
            bool: True if execution successful
        """
        raise NotImplementedError("Subclasses must implement execute_signal()")


class AlpacaRSIStrategy(TradingStrategy):
    """
    RSI trading strategy for Alpaca-listed assets (stocks, ETFs).
    """
    
    def __init__(self, symbol: str, **kwargs):
        super().__init__(symbol, **kwargs)
        self.data_source = "alpaca"
    
    def execute_signal(self, signal: str, current_price: float, 
                      account_equity: float) -> bool:
        """
        Execute signal on Alpaca API.
        """
        current_position = get_current_position(self.symbol)
        position_qty = float(current_position) if current_position else 0.0
        
        try:
            if signal == "BUY" and position_qty == 0:
                position_size = calculate_position_size(account_equity, current_price)
                order = place_order(self.symbol, position_size, 'buy', current_price)
                if order:
                    logger.info(f"[{self.symbol}] BUY signal executed: {order['qty']} shares")
                    return True
            
            elif signal == "SELL" and position_qty > 0:
                order = place_order(self.symbol, int(position_qty), 'sell')
                if order:
                    logger.info(f"[{self.symbol}] SELL signal executed: {order['qty']} shares")
                    return True
            
            elif signal == "HOLD":
                logger.debug(f"[{self.symbol}] HOLD signal - no action taken")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"[{self.symbol}] Failed to execute signal: {e}")
            return False


class MT5RSIStrategy(TradingStrategy):
    """
    RSI trading strategy for MetaTrader5 instruments (FX, commodities).
    Placeholder for MT5 integration - extends when MT5 is online.
    """
    
    def __init__(self, symbol: str, **kwargs):
        super().__init__(symbol, **kwargs)
        self.data_source = "mt5"
        logger.warning(f"[{symbol}] MT5 strategy initialized but MT5 connection not yet available")
    
    def get_mt5_data(self, lookback: int = 50) -> Optional[pd.DataFrame]:
        """
        Fetch OHLC data from MetaTrader5.
        TODO: Implement when MT5 SDK is installed and configured.
        """
        logger.warning(f"[{self.symbol}] MT5 data fetch not yet implemented")
        raise NotImplementedError("MT5 integration coming soon")
    
    def execute_signal(self, signal: str, current_price: float, 
                      account_equity: float) -> bool:
        """
        Execute signal on MetaTrader5.
        TODO: Implement MT5 order submission.
        """
        logger.warning(f"[{self.symbol}] MT5 signal execution not yet implemented")
        logger.info(f"[{self.symbol}] Signal: {signal}, Price: ${current_price:.2f}")
        return False  # No-op for now


# ============================================================================
# ORCHESTRATED BOT LOOP - Supports Multiple Strategies
# ============================================================================

def run_orchestrated_bot(strategies: List[TradingStrategy], sleep_sec: int = 60):
    """
    Main bot loop that orchestrates multiple trading strategies.
    Designed for Mansa/Bentley multi-symbol portfolio management.
    
    Args:
        strategies: List of TradingStrategy instances to run
        sleep_sec: Sleep duration between strategy cycles (seconds)
    """
    logger.info(f"Starting orchestrated bot with {len(strategies)} strategies")
    logger.info(f"Strategies: {[s.symbol for s in strategies]}")
    
    cycle = 0
    while True:
        cycle += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            logger.info(f"\n{'='*70}")
            logger.info(f"CYCLE {cycle} - {timestamp}")
            logger.info(f"{'='*70}")
            
            # Get account info once per cycle
            account = get_account_info()
            if not account:
                logger.error("Failed to retrieve account info; skipping cycle")
                time.sleep(sleep_sec)
                continue
            
            # Execute each strategy
            for strategy in strategies:
                try:
                    logger.info(f"\nProcessing {strategy.symbol} ({strategy.data_source})...")
                    
                    # Skip MT5 strategies until MT5 is online
                    if isinstance(strategy, MT5RSIStrategy):
                        logger.warning(f"[{strategy.symbol}] Skipping - MT5 not online yet")
                        continue
                    
                    # Get current price
                    try:
                        latest_bar = alpaca.get_latest_bar(strategy.symbol)
                        current_price = float(latest_bar.c)
                    except Exception as e:
                        logger.error(f"[{strategy.symbol}] Failed to fetch price: {e}")
                        continue
                    
                    # Get historical data and compute RSI
                    hist_data = get_historical_data(strategy.symbol)
                    if hist_data is None or len(hist_data) < strategy.rsi_period + 1:
                        logger.warning(f"[{strategy.symbol}] Insufficient data for RSI")
                        continue
                    
                    rsi = compute_rsi(hist_data['close'], strategy.rsi_period)
                    strategy.last_rsi = rsi
                    
                    # Compute signal
                    signal = strategy.compute_signal(rsi)
                    strategy.last_signal = signal
                    
                    logger.info(f"[{strategy.symbol}] RSI={rsi:.2f} | Signal={signal} | Price=${current_price:.2f}")
                    
                    # Execute signal
                    if signal != "HOLD":
                        strategy.execute_signal(signal, current_price, account['equity'])
                
                except Exception as e:
                    logger.error(f"[{strategy.symbol}] Strategy execution error: {e}", exc_info=True)
            
            logger.info(f"\nCycle {cycle} complete. Next check in {sleep_sec}s")
        
        except Exception as e:
            logger.error(f"[ORCHESTRATOR ERROR] {e}", exc_info=True)
        
        time.sleep(sleep_sec)


def run_simple_bot(symbol: str = GOLD_SYMBOL, sleep_sec: int = 60):
    """
    Simplified single-strategy bot (backward compatible).
    
    Args:
        symbol: Asset symbol to trade
        sleep_sec: Sleep duration between checks
    """
    strategy = AlpacaRSIStrategy(symbol)
    run_orchestrated_bot([strategy], sleep_sec)


if __name__ == "__main__":
    main()
    
    # Uncomment below to run bot loop:
    # ========================================
    # gold_strategy = AlpacaRSIStrategy(
    #     GOLD_SYMBOL,
    #     rsi_period=14,
    #     overbought=70,
    #     oversold=30
    # )
    # 
    # # Placeholder for USD/COP once MT5 is online
    # # usd_cop_strategy = MT5RSIStrategy(
    # #     "USDCOP",
    # #     rsi_period=14,
    # #     overbought=70,
    # #     oversold=30
    # # )
    # 
    # strategies = [gold_strategy]  # Add usd_cop_strategy when MT5 is ready
    # 
    # run_orchestrated_bot(strategies, sleep_sec=60)