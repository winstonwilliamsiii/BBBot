"""
Gold RSI Strategy - Trade Gold ETF (GLD) on Alpaca
===================================================

Strategy:
- Buy when RSI < 30 (oversold)
- Sell when RSI > 70 (overbought)
- Uses 14-period RSI on daily bars

Can be used with ANY broker by changing the broker parameter!

Example:
    # Use with Alpaca
    broker = create_broker_client('alpaca')
    strategy = GoldRsiStrategy(broker)
    strategy.run_once()
    
    # Use with MT5 (symbol would be XAUUSD)
    broker = create_broker_client('mt5')
    strategy = GoldRsiStrategy(broker, symbol='XAUUSD')
    strategy.run_once()
"""

import numpy as np
from typing import List
import logging

from trading.strategies.base_strategy import BaseStrategy
from frontend.utils.broker_interface import Position, HistoricalBar

logger = logging.getLogger(__name__)


class GoldRsiStrategy(BaseStrategy):
    """
    RSI-based mean reversion strategy for Gold
    
    Entry: RSI < 30 (oversold)
    Exit: RSI > 70 (overbought) OR stop loss
    """
    
    def __init__(
        self,
        broker,
        symbol: str = "GLD",
        rsi_period: int = 14,
        oversold_level: int = 30,
        overbought_level: int = 70,
        stop_loss_pct: float = 0.02,
        **kwargs
    ):
        """
        Initialize Gold RSI Strategy
        
        Args:
            broker: BrokerClient (Alpaca, MT5, etc.)
            symbol: Gold symbol (GLD for Alpaca, XAUUSD for MT5)
            rsi_period: RSI calculation period (default: 14)
            oversold_level: Buy when RSI below this (default: 30)
            overbought_level: Sell when RSI above this (default: 70)
            stop_loss_pct: Stop loss percentage (default: 2%)
        """
        super().__init__(broker, symbol, **kwargs)
        
        self.rsi_period = rsi_period
        self.oversold_level = oversold_level
        self.overbought_level = overbought_level
        self.stop_loss_pct = stop_loss_pct
        
        logger.info(
            f"Gold RSI Strategy initialized: "
            f"RSI {rsi_period}, Buy<{oversold_level}, Sell>{overbought_level}"
        )
    
    def get_name(self) -> str:
        return f"GoldRSI_{self.symbol}"
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """
        Calculate RSI (Relative Strength Index)
        
        Args:
            prices: List of closing prices
            period: RSI period (default: 14)
        
        Returns:
            RSI value (0-100)
        """
        if len(prices) < period + 1:
            return 50.0  # Neutral if not enough data
        
        # Calculate price changes
        deltas = np.diff(prices)
        
        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gains and losses
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        # Avoid division by zero
        if avg_loss == 0:
            return 100.0
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def get_current_rsi(self) -> float:
        """Get current RSI value"""
        try:
            # Get historical data
            bars = self.broker.get_historical_prices(
                symbol=self.symbol,
                timeframe="1D",
                limit=self.rsi_period + 20  # Extra for calculation
            )
            
            if len(bars) < self.rsi_period + 1:
                logger.warning(f"Not enough data for RSI calculation: {len(bars)} bars")
                return 50.0
            
            # Extract closing prices
            closes = [bar.close for bar in bars]
            
            # Calculate RSI
            rsi = self.calculate_rsi(closes, self.rsi_period)
            
            logger.debug(f"Current RSI for {self.symbol}: {rsi:.2f}")
            return rsi
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return 50.0  # Return neutral on error
    
    def should_enter(self) -> bool:
        """
        Entry condition: RSI < oversold level
        
        Returns:
            True if RSI indicates oversold
        """
        rsi = self.get_current_rsi()
        should_buy = rsi < self.oversold_level
        
        if should_buy:
            logger.info(f"✅ ENTRY SIGNAL: RSI {rsi:.2f} < {self.oversold_level} (oversold)")
        
        return should_buy
    
    def should_exit(self, position: Position) -> bool:
        """
        Exit conditions:
        1. RSI > overbought level (take profit)
        2. Stop loss hit
        
        Args:
            position: Current position
        
        Returns:
            True if should exit
        """
        # Check RSI
        rsi = self.get_current_rsi()
        if rsi > self.overbought_level:
            logger.info(f"✅ EXIT SIGNAL: RSI {rsi:.2f} > {self.overbought_level} (overbought)")
            return True
        
        # Check stop loss
        loss_pct = (position.current_price - position.entry_price) / position.entry_price
        if loss_pct < -self.stop_loss_pct:
            logger.info(
                f"🛑 STOP LOSS: Loss {loss_pct*100:.2f}% > {self.stop_loss_pct*100:.1f}%"
            )
            return True
        
        return False
    
    def get_signal_info(self) -> dict:
        """Get current strategy signals for dashboard"""
        rsi = self.get_current_rsi()
        position = self.get_current_position()
        
        return {
            'strategy': self.get_name(),
            'symbol': self.symbol,
            'rsi': round(rsi, 2),
            'rsi_status': 'oversold' if rsi < self.oversold_level else 'overbought' if rsi > self.overbought_level else 'neutral',
            'has_position': position is not None,
            'position_pnl': position.unrealized_pnl if position else 0,
            'buy_signal': rsi < self.oversold_level,
            'sell_signal': rsi > self.overbought_level if position else False
        }


# ============================================================
# USD/COP SHORT STRATEGY (for MT5 Forex)
# ============================================================

class UsdCopShortStrategy(BaseStrategy):
    """
    Mean reversion strategy for USD/COP (Colombian Peso)
    
    Strategy:
    - Short when price > upper Bollinger Band
    - Cover when price < lower Bollinger Band
    
    This works on MT5 for FOREX pairs
    """
    
    def __init__(
        self,
        broker,
        symbol: str = "USDCOP",
        bb_period: int = 20,
        bb_std: float = 2.0,
        stop_loss_pips: int = 100,
        **kwargs
    ):
        """
        Initialize USD/COP Short Strategy
        
        Args:
            broker: BrokerClient (MT5 for FOREX)
            symbol: Forex pair (USDCOP)
            bb_period: Bollinger Bands period (default: 20)
            bb_std: Standard deviations for bands (default: 2.0)
            stop_loss_pips: Stop loss in pips (default: 100)
        """
        super().__init__(broker, symbol, **kwargs)
        
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.stop_loss_pips = stop_loss_pips
        
        logger.info(f"USD/COP Short Strategy initialized: BB({bb_period}, {bb_std})")
    
    def get_name(self) -> str:
        return f"USDCOPShort_{self.symbol}"
    
    def calculate_bollinger_bands(self, prices: List[float]) -> tuple:
        """Calculate Bollinger Bands"""
        if len(prices) < self.bb_period:
            return (0, 0, 0)
        
        recent_prices = prices[-self.bb_period:]
        sma = np.mean(recent_prices)
        std = np.std(recent_prices)
        
        upper_band = sma + (self.bb_std * std)
        lower_band = sma - (self.bb_std * std)
        
        return (upper_band, sma, lower_band)
    
    def get_bollinger_bands(self) -> tuple:
        """Get current Bollinger Bands"""
        try:
            bars = self.broker.get_historical_prices(
                symbol=self.symbol,
                timeframe="H1",  # 1-hour bars for forex
                limit=self.bb_period + 10
            )
            
            closes = [bar.close for bar in bars]
            return self.calculate_bollinger_bands(closes)
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return (0, 0, 0)
    
    def should_enter(self) -> bool:
        """
        Entry: Price > upper Bollinger Band (mean reversion short)
        """
        upper, middle, lower = self.get_bollinger_bands()
        if upper == 0:
            return False
        
        current_price = self.broker.get_current_price(self.symbol)
        should_short = current_price > upper
        
        if should_short:
            logger.info(
                f"✅ SHORT SIGNAL: Price {current_price:.4f} > Upper BB {upper:.4f}"
            )
        
        return should_short
    
    def should_exit(self, position: Position) -> bool:
        """
        Exit: Price < lower Bollinger Band OR stop loss
        """
        upper, middle, lower = self.get_bollinger_bands()
        if lower == 0:
            return False
        
        # Check profit target (lower band)
        if position.current_price < lower:
            logger.info(
                f"✅ COVER SIGNAL: Price {position.current_price:.4f} < Lower BB {lower:.4f}"
            )
            return True
        
        # Check stop loss (for short position, loss increases when price goes up)
        pip_value = 0.0001  # For most forex pairs
        pips_loss = (position.current_price - position.entry_price) / pip_value
        
        if pips_loss > self.stop_loss_pips:
            logger.info(f"🛑 STOP LOSS: {pips_loss:.0f} pips > {self.stop_loss_pips} pips")
            return True
        
        return False
    
    def get_signal_info(self) -> dict:
        """Get current strategy signals"""
        upper, middle, lower = self.get_bollinger_bands()
        current_price = self.broker.get_current_price(self.symbol)
        position = self.get_current_position()
        
        return {
            'strategy': self.get_name(),
            'symbol': self.symbol,
            'price': round(current_price, 4),
            'upper_bb': round(upper, 4),
            'middle_bb': round(middle, 4),
            'lower_bb': round(lower, 4),
            'has_position': position is not None,
            'position_pnl': position.unrealized_pnl if position else 0,
            'short_signal': current_price > upper,
            'cover_signal': current_price < lower if position else False
        }
