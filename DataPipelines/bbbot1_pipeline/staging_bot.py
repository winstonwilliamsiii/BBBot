"""
Mansa_Bot - Staging Environment Trading Bot
Purpose: Integration testing with real broker APIs (Alpaca paper trading)
Database: bbbot1 (staging), logs to bot_decision_audit table
Author: Bentley Bot System
Date: January 27, 2026
"""

import json
import logging
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import mysql.connector
from mysql.connector import pooling
import yfinance as yf
from abc import ABC, abstractmethod


# ===================================================================
# Logging Configuration
# ===================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ===================================================================
# Enums & Data Classes
# ===================================================================

class DecisionType(Enum):
    """Trading decision types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    REBALANCE = "REBALANCE"


class OrderStatus(Enum):
    """Order execution status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIAL = "partial_fill"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class Position:
    """Portfolio position"""
    ticker: str
    quantity: float
    entry_price: float
    current_price: float
    position_value: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    
    def calculate_pnl(self):
        """Calculate P&L for position"""
        self.position_value = self.quantity * self.current_price
        self.pnl = (self.current_price - self.entry_price) * self.quantity
        self.pnl_percent = (self.pnl / (self.entry_price * self.quantity)) * 100 if self.entry_price > 0 else 0


@dataclass
class TradingSignal:
    """Technical indicator trading signal"""
    ticker: str
    signal_type: DecisionType
    timestamp: datetime
    price: float
    reason: str
    confidence: float  # 0.0-1.0
    
    # Technical indicators
    rsi: Optional[float] = None
    macd: Optional[float] = None
    bollinger_bands: Optional[Dict] = None
    volume_sma_ratio: Optional[float] = None
    
    # Risk metrics
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None


@dataclass
class TradingDecision:
    """Final trading decision to execute"""
    bot_id: str
    decision_id: str
    ticker: str
    decision_type: DecisionType
    quantity: float
    target_price: float
    reason: str
    confidence: float
    timestamp: datetime
    
    # Execution details
    order_id: Optional[str] = None
    order_status: OrderStatus = OrderStatus.PENDING
    execution_price: Optional[float] = None
    execution_qty: float = 0.0
    execution_time: Optional[datetime] = None
    
    # Outcome
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None


# ===================================================================
# Broker Integration (Abstract)
# ===================================================================

class BrokerConnector(ABC):
    """Abstract broker connector interface"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to broker"""
        pass
    
    @abstractmethod
    def get_account_info(self) -> Dict:
        """Get account details (cash, portfolio value, etc)"""
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """Get current positions"""
        pass
    
    @abstractmethod
    def submit_order(self, decision: TradingDecision) -> Tuple[bool, str]:
        """Submit order to broker"""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order"""
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> OrderStatus:
        """Get status of submitted order"""
        pass


class AlpacaBrokerConnector(BrokerConnector):
    """Alpaca paper trading broker connector"""
    
    def __init__(self, api_key: str, secret_key: str, base_url: str = None):
        """
        Initialize Alpaca connector
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            base_url: Base URL (defaults to paper trading)
        """
        try:
            from alpaca.trading.client import TradingClient
            from alpaca.trading.requests import MarketOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce
            
            self.TradingClient = TradingClient
            self.MarketOrderRequest = MarketOrderRequest
            self.OrderSide = OrderSide
            self.TimeInForce = TimeInForce
            
        except ImportError:
            logger.warning("Alpaca SDK not available - running in simulation mode")
            self.TradingClient = None
        
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url or "https://paper-api.alpaca.markets"
        self.client = None
        self.is_connected = False
    
    def connect(self) -> bool:
        """Connect to Alpaca API"""
        try:
            if self.TradingClient:
                self.client = self.TradingClient(
                    api_key=self.api_key,
                    secret_key=self.secret_key,
                    base_url=self.base_url
                )
                self.is_connected = True
                logger.info("Connected to Alpaca paper trading API")
            else:
                logger.info("Alpaca SDK not available - simulating connection")
                self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Alpaca: {e}")
            return False
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        if not self.is_connected or not self.client:
            return {"error": "Not connected"}
        
        try:
            account = self.client.get_account()
            return {
                "account_value": float(account.portfolio_value),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "equity": float(account.equity),
                "day_trade_buying_power": float(account.daytrade_buying_power),
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return {}
    
    def get_positions(self) -> List[Position]:
        """Get current positions"""
        if not self.is_connected or not self.client:
            return []
        
        try:
            alpaca_positions = self.client.get_all_positions()
            positions = []
            
            for pos in alpaca_positions:
                position = Position(
                    ticker=pos.symbol,
                    quantity=float(pos.qty),
                    entry_price=float(pos.avg_entry_price),
                    current_price=float(pos.current_price),
                )
                position.calculate_pnl()
                positions.append(position)
            
            return positions
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    def submit_order(self, decision: TradingDecision) -> Tuple[bool, str]:
        """Submit market order"""
        if not self.is_connected or not self.client:
            # Simulate order submission
            order_id = f"SIM_{decision.ticker}_{decision.decision_id}"
            logger.info(f"Simulated order submission: {order_id}")
            return True, order_id
        
        try:
            # Determine order side
            side = self.OrderSide.BUY if decision.decision_type == DecisionType.BUY else self.OrderSide.SELL
            
            # Create market order
            order_request = self.MarketOrderRequest(
                symbol=decision.ticker,
                qty=decision.quantity,
                side=side,
                time_in_force=self.TimeInForce.DAY,
            )
            
            # Submit order
            order = self.client.submit_order(order_request)
            
            decision.order_id = order.id
            decision.order_status = OrderStatus.SUBMITTED
            
            logger.info(f"Order submitted: {order.id} for {decision.ticker}")
            return True, order.id
            
        except Exception as e:
            logger.error(f"Failed to submit order: {e}")
            decision.order_status = OrderStatus.FAILED
            return False, str(e)
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order"""
        if not self.is_connected or not self.client:
            return True
        
        try:
            self.client.cancel_order(order_id)
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    def get_order_status(self, order_id: str) -> OrderStatus:
        """Get order status"""
        if not self.is_connected or not self.client:
            return OrderStatus.PENDING
        
        try:
            order = self.client.get_order_by_client_order_id(order_id)
            
            status_map = {
                "pending_new": OrderStatus.PENDING,
                "accepted": OrderStatus.SUBMITTED,
                "filled": OrderStatus.FILLED,
                "partially_filled": OrderStatus.PARTIAL,
                "canceled": OrderStatus.CANCELLED,
                "rejected": OrderStatus.FAILED,
            }
            
            return status_map.get(order.status, OrderStatus.PENDING)
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return OrderStatus.PENDING


# ===================================================================
# Mansa Bot - Main Trading Bot
# ===================================================================

class MansaBot:
    """
    Mansa Bot - Staging trading bot with broker integration
    
    Features:
    - Integration with Alpaca broker (paper trading)
    - Technical analysis for signal generation
    - Risk management and position sizing
    - Audit logging to MySQL database
    """
    
    def __init__(
        self,
        bot_id: str,
        broker: BrokerConnector,
        db_config: Dict,
        tickers: List[str],
    ):
        """
        Initialize Mansa Bot
        
        Args:
            bot_id: Unique bot identifier
            broker: Broker connector instance
            db_config: Database connection config
            tickers: List of tickers to trade
        """
        self.bot_id = bot_id
        self.broker = broker
        self.db_config = db_config
        self.tickers = tickers
        self.portfolio: Dict[str, Position] = {}
        self.decisions: List[TradingDecision] = []
        
        # Database connection pool
        self.db_pool = None
        self.initialize_db_pool()
    
    def initialize_db_pool(self):
        """Initialize database connection pool"""
        try:
            self.db_pool = pooling.MySQLConnectionPool(
                pool_name="mansa_bot_pool",
                pool_size=5,
                pool_reset_session=True,
                **self.db_config,
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
    
    def get_db_connection(self):
        """Get database connection from pool"""
        try:
            return self.db_pool.get_connection()
        except Exception as e:
            logger.error(f"Failed to get database connection: {e}")
            return None
    
    def initialize(self) -> bool:
        """Initialize bot (connect to broker, load positions)"""
        try:
            # Connect to broker
            if not self.broker.connect():
                logger.error("Failed to connect to broker")
                return False
            
            # Get account info
            account_info = self.broker.get_account_info()
            logger.info(f"Account info: {account_info}")
            
            # Load positions
            positions = self.broker.get_positions()
            for position in positions:
                self.portfolio[position.ticker] = position
            
            logger.info(f"Loaded {len(self.portfolio)} positions")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            return False
    
    def generate_signal(self, ticker: str, current_price: float) -> Optional[TradingSignal]:
        """
        Generate trading signal using technical analysis
        
        Args:
            ticker: Stock ticker
            current_price: Current stock price
            
        Returns:
            TradingSignal or None if no signal
        """
        try:
            # Get historical data
            df = yf.download(ticker, period="60d", progress=False)
            
            if df.empty:
                logger.warning(f"No data available for {ticker}")
                return None
            
            # Calculate RSI
            rsi = self._calculate_rsi(df['Close'])
            
            # Calculate MACD
            macd, signal_line = self._calculate_macd(df['Close'])
            
            # Determine signal
            signal_type = DecisionType.HOLD
            confidence = 0.0
            reason = ""
            
            if rsi < 30 and macd > signal_line:
                signal_type = DecisionType.BUY
                confidence = min(0.9, (30 - rsi) / 30 + 0.1)
                reason = f"RSI oversold ({rsi:.2f}) + MACD bullish crossover"
            
            elif rsi > 70 and macd < signal_line:
                signal_type = DecisionType.SELL
                confidence = min(0.9, (rsi - 70) / 30 + 0.1)
                reason = f"RSI overbought ({rsi:.2f}) + MACD bearish crossover"
            
            elif rsi > 50:
                signal_type = DecisionType.HOLD
                confidence = min(rsi - 50) / 20
                reason = "Positive momentum, holding"
            
            else:
                signal_type = DecisionType.HOLD
                confidence = 0.5
                reason = "Neutral signal"
            
            return TradingSignal(
                ticker=ticker,
                signal_type=signal_type,
                timestamp=datetime.now(),
                price=current_price,
                reason=reason,
                confidence=confidence,
                rsi=rsi,
                macd=macd,
            )
            
        except Exception as e:
            logger.error(f"Failed to generate signal for {ticker}: {e}")
            return None
    
    def _calculate_rsi(self, prices, period=14) -> float:
        """Calculate RSI indicator"""
        try:
            deltas = prices.diff()
            seed = deltas[:period+1]
            up = seed[seed >= 0].sum() / period
            down = -seed[seed < 0].sum() / period
            rs = up / down if down != 0 else 0
            rsi = 100 - 100 / (1 + rs)
            return rsi
        except:
            return 50.0
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9) -> Tuple[float, float]:
        """Calculate MACD indicator"""
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            return float(macd_line.iloc[-1]), float(signal_line.iloc[-1])
        except:
            return 0.0, 0.0
    
    def execute_trading_round(self) -> bool:
        """Execute one trading round"""
        try:
            logger.info(f"Starting trading round for {len(self.tickers)} tickers")
            
            for ticker in self.tickers:
                try:
                    # Get current price
                    data = yf.download(ticker, period="1d", progress=False)
                    current_price = float(data['Close'].iloc[-1])
                    
                    # Generate signal
                    signal = self.generate_signal(ticker, current_price)
                    
                    if not signal or signal.signal_type == DecisionType.HOLD:
                        continue
                    
                    # Create trading decision
                    decision = TradingDecision(
                        bot_id=self.bot_id,
                        decision_id=f"{ticker}_{datetime.now().timestamp()}",
                        ticker=ticker,
                        decision_type=signal.signal_type,
                        quantity=self._calculate_position_size(ticker, current_price),
                        target_price=current_price * 1.02 if signal.signal_type == DecisionType.BUY else current_price * 0.98,
                        reason=signal.reason,
                        confidence=signal.confidence,
                        timestamp=datetime.now(),
                    )
                    
                    # Submit order
                    success, order_id = self.broker.submit_order(decision)
                    
                    if success:
                        self.decisions.append(decision)
                        self.log_decision_to_db(decision)
                        logger.info(f"Decision logged: {decision.decision_id}")
                    
                except Exception as e:
                    logger.error(f"Error processing {ticker}: {e}")
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"Trading round failed: {e}")
            return False
    
    def _calculate_position_size(self, ticker: str, price: float) -> float:
        """Calculate position size using risk management"""
        # Simple: 1% of portfolio per position
        account = self.broker.get_account_info()
        portfolio_value = account.get("account_value", 10000)
        position_value = portfolio_value * 0.01  # 1% risk per trade
        quantity = position_value / price if price > 0 else 0
        return max(1, int(quantity))  # At least 1 share
    
    def log_decision_to_db(self, decision: TradingDecision):
        """Log trading decision to MySQL database"""
        conn = self.get_db_connection()
        
        if not conn:
            logger.error("Cannot log to database - no connection")
            return
        
        try:
            cursor = conn.cursor()
            
            insert_query = """
                INSERT INTO bbbot1.bot_decision_audit (
                    bot_id, decision_type, ticker, quantity, target_price,
                    reason, ml_confidence, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                decision.bot_id,
                decision.decision_type.value,
                decision.ticker,
                decision.quantity,
                decision.target_price,
                decision.reason,
                decision.confidence,
                decision.timestamp,
            ))
            
            conn.commit()
            logger.info(f"Decision logged to database: {decision.decision_id}")
            
        except Exception as e:
            logger.error(f"Failed to log decision to database: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()


# ===================================================================
# Main Entry Point
# ===================================================================

def main():
    """Main entry point for Mansa Bot"""
    
    # Configuration
    BOT_ID = "mansa_bot_staging_v1"
    TICKERS = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
    
    # Database configuration
    db_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3307")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", "root"),
        "database": "bbbot1",
    }
    
    # Broker configuration
    alpaca_key = os.getenv("ALPACA_API_KEY", "")
    alpaca_secret = os.getenv("ALPACA_SECRET_KEY", "")
    
    # Initialize broker
    broker = AlpacaBrokerConnector(alpaca_key, alpaca_secret)
    
    # Initialize bot
    bot = MansaBot(BOT_ID, broker, db_config, TICKERS)
    
    # Initialize and run
    if bot.initialize():
        logger.info("Bot initialized successfully")
        bot.execute_trading_round()
    else:
        logger.error("Failed to initialize bot")


if __name__ == "__main__":
    main()
