"""
Base Trading Strategy - Abstract strategy interface
====================================================

All trading strategies inherit from this base class.
Strategies only use the BrokerClient interface, so they
work with ANY broker (Alpaca, MT5, IBKR, Webull).

Example strategies:
- GoldRsiStrategy: Trade gold ETF (GLD) on Alpaca
- UsdCopShortStrategy: Trade USD/COP on MT5
- Both use the SAME base strategy code!
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import logging

from src.brokers.broker_interface import BrokerClient, Position

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    Your strategies implement:
    - should_enter(): Check if we should enter a trade
    - should_exit(): Check if we should exit a trade
    - calculate_position_size(): How much to trade
    
    The base class handles:
    - Execution via broker client
    - Position tracking
    - Error handling
    - Logging
    """
    
    def __init__(
        self,
        broker: BrokerClient,
        symbol: str,
        max_position_size: float = 1000.0,
        risk_per_trade: float = 0.02
    ):
        """
        Initialize strategy
        
        Args:
            broker: BrokerClient implementation (Alpaca, MT5, etc.)
            symbol: Trading symbol
            max_position_size: Maximum dollar amount per position
            risk_per_trade: Risk percentage per trade (0.02 = 2%)
        """
        self.broker = broker
        self.symbol = symbol
        self.max_position_size = max_position_size
        self.risk_per_trade = risk_per_trade
        
        self.is_running = False
        self.last_check_time = None
        self.trade_count = 0
        self.win_count = 0
        
        logger.info(f"Initialized {self.get_name()} for {symbol} on {broker.get_broker_name()}")
    
    @abstractmethod
    def get_name(self) -> str:
        """Return strategy name"""
        pass
    
    @abstractmethod
    def should_enter(self) -> bool:
        """
        Check if we should enter a new position
        
        Returns:
            True if entry conditions met
        """
        pass
    
    @abstractmethod
    def should_exit(self, position: Position) -> bool:
        """
        Check if we should exit an existing position
        
        Args:
            position: Current position
        
        Returns:
            True if exit conditions met
        """
        pass
    
    def calculate_position_size(self) -> float:
        """
        Calculate position size based on account equity and risk
        
        Returns:
            Number of shares/lots to trade
        """
        equity = self.broker.get_equity()
        risk_amount = equity * self.risk_per_trade
        
        # Simple position sizing - can be overridden
        current_price = self.broker.get_current_price(self.symbol)
        
        # Don't exceed max position size
        max_qty = self.max_position_size / current_price
        risk_qty = risk_amount / current_price
        
        return min(max_qty, risk_qty)
    
    def get_current_position(self) -> Optional[Position]:
        """Get current position for this symbol"""
        return self.broker.get_position(self.symbol)
    
    def enter_position(self) -> bool:
        """
        Enter a new position if conditions are met
        
        Returns:
            True if position entered successfully
        """
        try:
            # Check if we already have a position
            existing_position = self.get_current_position()
            if existing_position:
                logger.warning(f"Already have position in {self.symbol}")
                return False
            
            # Check if we should enter
            if not self.should_enter():
                logger.debug(f"Entry conditions not met for {self.symbol}")
                return False
            
            # Calculate position size
            qty = self.calculate_position_size()
            if qty <= 0:
                logger.warning(f"Invalid position size: {qty}")
                return False
            
            # Place order
            logger.info(f"ENTERING {self.symbol}: {qty} shares")
            order = self.broker.place_order(
                symbol=self.symbol,
                qty=qty,
                side='buy',
                order_type='market'
            )
            
            self.trade_count += 1
            logger.info(f"Position entered: {order}")
            return True
            
        except Exception as e:
            logger.error(f"Error entering position: {e}")
            return False
    
    def exit_position(self) -> bool:
        """
        Exit existing position if conditions are met
        
        Returns:
            True if position exited successfully
        """
        try:
            # Get current position
            position = self.get_current_position()
            if not position:
                logger.debug(f"No position to exit for {self.symbol}")
                return False
            
            # Check if we should exit
            if not self.should_exit(position):
                logger.debug(f"Exit conditions not met for {self.symbol}")
                return False
            
            # Close position
            logger.info(f"EXITING {self.symbol}: {position.qty} shares, P&L: ${position.unrealized_pnl:.2f}")
            order = self.broker.close_position(self.symbol)
            
            # Track wins
            if position.unrealized_pnl > 0:
                self.win_count += 1
            
            logger.info(f"Position exited: {order}")
            return True
            
        except Exception as e:
            logger.error(f"Error exiting position: {e}")
            return False
    
    def run_once(self) -> Dict:
        """
        Execute one strategy cycle (check entry/exit)
        
        Returns:
            Status dictionary with actions taken
        """
        self.last_check_time = datetime.now()
        
        result = {
            'timestamp': self.last_check_time.isoformat(),
            'strategy': self.get_name(),
            'symbol': self.symbol,
            'broker': self.broker.get_broker_name(),
            'entered': False,
            'exited': False,
            'position': None
        }
        
        # Check for exit first (if we have a position)
        position = self.get_current_position()
        if position:
            result['position'] = {
                'qty': position.qty,
                'entry_price': position.entry_price,
                'current_price': position.current_price,
                'pnl': position.unrealized_pnl
            }
            result['exited'] = self.exit_position()
        else:
            # Try to enter if no position
            result['entered'] = self.enter_position()
        
        return result
    
    def get_stats(self) -> Dict:
        """Get strategy performance statistics"""
        win_rate = (self.win_count / self.trade_count * 100) if self.trade_count > 0 else 0
        
        return {
            'name': self.get_name(),
            'symbol': self.symbol,
            'broker': self.broker.get_broker_name(),
            'trades': self.trade_count,
            'wins': self.win_count,
            'win_rate': f"{win_rate:.1f}%",
            'last_check': self.last_check_time.isoformat() if self.last_check_time else None
        }
