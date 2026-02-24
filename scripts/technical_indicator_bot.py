"""
Technical Indicator Trading Bot for Alpaca Markets

Implements multi-indicator trading strategy with:
- RSI (Relative Strength Index) for momentum
- MACD (Moving Average Convergence Divergence) for trend
- Bollinger Bands for volatility
- SMA (Simple Moving Average) for overall trend
- Automated position sizing and risk management
- Configurable safety checks and execution controls
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import pandas as pd
import numpy as np
from alpaca_trade_api import REST, TimeFrame

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/technical_indicator_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class TradingConfig:
    """Trading bot configuration parameters"""
    
    # Alpaca API Configuration
    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
    ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
    ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    
    # Trading Parameters
    SYMBOLS = os.getenv("TRADING_SYMBOLS", "VOO,SQQQ,MAGS,BITI,XLF,QUTM,NUKZ,PINK,DFEN,VXX,IONZ,VIX").split(",")  # ETF tickers
    TIMEFRAME = TimeFrame.Day  # 1-day bars
    LOOKBACK_DAYS = 100  # Historical data for indicators
    
    # Technical Indicator Parameters
    RSI_PERIOD = 14
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30
    
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    
    SMA_SHORT = 20
    SMA_LONG = 50
    
    BB_PERIOD = 20
    BB_STD = 2
    
    # Risk Management
    MAX_POSITION_SIZE = 100  # Maximum shares per order
    RISK_PER_TRADE = 0.02  # 2% of account per trade
    MAX_OPEN_POSITIONS = 3
    MIN_ACCOUNT_BALANCE = 1000  # Minimum account balance required
    
    # Safety Controls
    DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
    ENABLE_TRADING = os.getenv("ENABLE_TRADING", "false").lower() == "true"
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        # Check if API keys are set (either from env or directly)
        api_key = cls.ALPACA_API_KEY or os.getenv("ALPACA_API_KEY")
        secret_key = cls.ALPACA_SECRET_KEY or os.getenv("ALPACA_SECRET_KEY")
        
        if not api_key or not secret_key:
            raise ValueError("Missing Alpaca API credentials. Set ALPACA_API_KEY and ALPACA_SECRET_KEY")
        
        # Update class attributes if they were read from env now
        cls.ALPACA_API_KEY = api_key
        cls.ALPACA_SECRET_KEY = secret_key
        
        logger.info(f"Configuration loaded:")
        logger.info(f"  Symbols: {', '.join(cls.SYMBOLS)}")
        logger.info(f"  Base URL: {cls.ALPACA_BASE_URL}")
        logger.info(f"  Dry Run: {cls.DRY_RUN}")
        logger.info(f"  Trading Enabled: {cls.ENABLE_TRADING}")


# ============================================================================
# TECHNICAL INDICATOR CALCULATIONS
# ============================================================================

class TechnicalIndicators:
    """Calculate technical indicators for trading signals"""
    
    @staticmethod
    def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        try:
            delta = series.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return pd.Series(dtype=float)
    
    @staticmethod
    def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD, Signal line, and Histogram"""
        try:
            exp1 = series.ewm(span=fast, adjust=False).mean()
            exp2 = series.ewm(span=slow, adjust=False).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=signal, adjust=False).mean()
            histogram = macd - signal_line
            return macd, signal_line, histogram
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return pd.Series(dtype=float), pd.Series(dtype=float), pd.Series(dtype=float)
    
    @staticmethod
    def compute_bollinger_bands(series: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands (upper, middle, lower)"""
        try:
            middle = series.rolling(window=period).mean()
            std = series.rolling(window=period).std()
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            return upper, middle, lower
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return pd.Series(dtype=float), pd.Series(dtype=float), pd.Series(dtype=float)
    
    @staticmethod
    def compute_sma(series: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Simple Moving Average"""
        try:
            return series.rolling(window=period).mean()
        except Exception as e:
            logger.error(f"Error calculating SMA: {e}")
            return pd.Series(dtype=float)


# ============================================================================
# TRADING BOT
# ============================================================================

class TechnicalIndicatorBot:
    """Main trading bot implementing multi-indicator strategy"""
    
    def __init__(self, config: TradingConfig):
        """Initialize the trading bot"""
        self.config = config
        self.config.validate()
        
        try:
            self.api = REST(
                config.ALPACA_API_KEY,
                config.ALPACA_SECRET_KEY,
                base_url=config.ALPACA_BASE_URL
            )
            logger.info("✓ Alpaca API connection established")
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca API: {e}")
            raise
        
        self.indicators = TechnicalIndicators()
        self.account_info = None
    
    def get_account_info(self) -> Dict:
        """Fetch and cache account information"""
        try:
            account = self.api.get_account()
            self.account_info = {
                'equity': float(account.equity),
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value)
            }
            logger.info(f"Account equity: ${self.account_info['equity']:.2f}")
            return self.account_info
        except Exception as e:
            logger.error(f"Error fetching account info: {e}")
            return {}
    
    def get_current_position(self, symbol: str) -> Optional[int]:
        """Get current position size for a symbol"""
        try:
            positions = self.api.list_positions()
            for position in positions:
                if position.symbol == symbol:
                    return int(position.qty)
            return 0
        except Exception as e:
            logger.error(f"Error getting position for {symbol}: {e}")
            return None
    
    def fetch_market_data(self, symbol: str, days: int = 100) -> pd.DataFrame:
        """Fetch historical market data"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"Fetching {days} days of data for {symbol}...")
            
            bars = self.api.get_bars(
                symbol,
                self.config.TIMEFRAME,
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                limit=10000
            ).df
            
            if bars.empty:
                logger.error(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            logger.info(f"✓ Retrieved {len(bars)} bars for {symbol}")
            return bars
        
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators on the price data"""
        try:
            # RSI
            df['RSI'] = self.indicators.compute_rsi(df['close'], self.config.RSI_PERIOD)
            
            # MACD
            macd, signal, hist = self.indicators.compute_macd(
                df['close'],
                self.config.MACD_FAST,
                self.config.MACD_SLOW,
                self.config.MACD_SIGNAL
            )
            df['MACD'] = macd
            df['MACD_Signal'] = signal
            df['MACD_Hist'] = hist
            
            # SMAs
            df['SMA_Short'] = self.indicators.compute_sma(df['close'], self.config.SMA_SHORT)
            df['SMA_Long'] = self.indicators.compute_sma(df['close'], self.config.SMA_LONG)
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self.indicators.compute_bollinger_bands(
                df['close'],
                self.config.BB_PERIOD,
                self.config.BB_STD
            )
            df['BB_Upper'] = bb_upper
            df['BB_Middle'] = bb_middle
            df['BB_Lower'] = bb_lower
            
            logger.info("✓ All technical indicators calculated")
            return df
        
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df
    
    def generate_signal(self, df: pd.DataFrame) -> str:
        """
        Generate trading signal based on multiple indicators
        
        Returns: 'BUY', 'SELL', or 'HOLD'
        """
        try:
            if df.empty or len(df) < 2:
                return 'HOLD'
            
            # Get latest values
            latest = df.iloc[-1]
            previous = df.iloc[-2]
            
            # Signal counters
            buy_signals = 0
            sell_signals = 0
            
            # RSI Signals
            if latest['RSI'] < self.config.RSI_OVERSOLD:
                buy_signals += 1
            elif latest['RSI'] > self.config.RSI_OVERBOUGHT:
                sell_signals += 1
            
            # MACD Crossover Signals
            if latest['MACD'] > latest['MACD_Signal'] and previous['MACD'] <= previous['MACD_Signal']:
                buy_signals += 1  # Bullish crossover
            elif latest['MACD'] < latest['MACD_Signal'] and previous['MACD'] >= previous['MACD_Signal']:
                sell_signals += 1  # Bearish crossover
            
            # Moving Average Signals
            if latest['close'] > latest['SMA_Short'] and latest['SMA_Short'] > latest['SMA_Long']:
                buy_signals += 1  # Uptrend
            elif latest['close'] < latest['SMA_Short'] and latest['SMA_Short'] < latest['SMA_Long']:
                sell_signals += 1  # Downtrend
            
            # Bollinger Band Signals
            if latest['close'] < latest['BB_Lower']:
                buy_signals += 1  # Oversold
            elif latest['close'] > latest['BB_Upper']:
                sell_signals += 1  # Overbought
            
            # Decision logic: require at least 2 confirming indicators
            if buy_signals >= 2 and sell_signals == 0:
                logger.info(f"BUY signal generated ({buy_signals} indicators)")
                return 'BUY'
            elif sell_signals >= 2 and buy_signals == 0:
                logger.info(f"SELL signal generated ({sell_signals} indicators)")
                return 'SELL'
            else:
                logger.info(f"HOLD signal (buy: {buy_signals}, sell: {sell_signals})")
                return 'HOLD'
        
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return 'HOLD'
    
    def calculate_position_size(self, price: float) -> int:
        """Calculate position size based on risk management rules"""
        try:
            if not self.account_info:
                self.get_account_info()
            
            # Calculate position size based on risk percentage
            max_risk_amount = self.account_info['equity'] * self.config.RISK_PER_TRADE
            position_size = int(max_risk_amount / price)
            
            # Apply maximum position size limit
            position_size = min(position_size, self.config.MAX_POSITION_SIZE)
            
            logger.info(f"Calculated position size: {position_size} shares at ${price:.2f}")
            return position_size
        
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0
    
    def execute_trade(self, symbol: str, signal: str, price: float):
        """Execute trade based on signal"""
        try:
            # Safety checks
            if not self.config.ENABLE_TRADING:
                logger.warning("Trading is disabled. Set ENABLE_TRADING=true to execute real orders.")
                return
            
            if self.config.DRY_RUN:
                logger.info(f"[DRY RUN] Would execute {signal} order for {symbol} at ${price:.2f}")
                return
            
            current_position = self.get_current_position(symbol)
            
            if signal == 'BUY' and current_position == 0:
                qty = self.calculate_position_size(price)
                
                if qty > 0:
                    order = self.api.submit_order(
                        symbol=symbol,
                        qty=qty,
                        side='buy',
                        type='market',
                        time_in_force='gtc'
                    )
                    logger.info(f"✓ BUY order submitted: {qty} shares of {symbol} (Order ID: {order.id})")
                else:
                    logger.warning("Calculated position size is 0, skipping order")
            
            elif signal == 'SELL' and current_position > 0:
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=current_position,
                    side='sell',
                    type='market',
                    time_in_force='gtc'
                )
                logger.info(f"✓ SELL order submitted: {current_position} shares of {symbol} (Order ID: {order.id})")
            
            else:
                logger.info(f"No action taken for {signal} signal (Current position: {current_position})")
        
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
    
    def run(self):
        """Main execution loop - processes all configured symbols"""
        try:
            logger.info("=" * 80)
            logger.info("TECHNICAL INDICATOR TRADING BOT - STARTING")
            logger.info("=" * 80)
            
            # Get account info
            self.get_account_info()
            
            # Check minimum balance
            if self.account_info['equity'] < self.config.MIN_ACCOUNT_BALANCE:
                logger.error(f"Account balance (${self.account_info['equity']:.2f}) below minimum (${self.config.MIN_ACCOUNT_BALANCE})")
                return
            
            # Process each symbol
            for symbol in self.config.SYMBOLS:
                try:
                    logger.info(f"\n{'='*60}")
                    logger.info(f"Processing {symbol}")
                    logger.info(f"{'='*60}")
                    
                    # Fetch market data
                    df = self.fetch_market_data(symbol, self.config.LOOKBACK_DAYS)
                    
                    if df.empty:
                        logger.warning(f"No market data available for {symbol}, skipping...")
                        continue
                    
                    # Calculate indicators
                    df = self.calculate_all_indicators(df)
                    
                    # Display latest indicator values
                    latest = df.iloc[-1]
                    logger.info("Latest Indicator Values:")
                    logger.info(f"  Price: ${latest['close']:.2f}")
                    logger.info(f"  RSI: {latest['RSI']:.2f}")
                    logger.info(f"  MACD: {latest['MACD']:.4f}, Signal: {latest['MACD_Signal']:.4f}")
                    logger.info(f"  SMA Short: ${latest['SMA_Short']:.2f}, SMA Long: ${latest['SMA_Long']:.2f}")
                    logger.info(f"  BB Upper: ${latest['BB_Upper']:.2f}, Lower: ${latest['BB_Lower']:.2f}")
                    
                    # Generate signal
                    signal = self.generate_signal(df)
                    logger.info(f"Signal for {symbol}: {signal}")
                    
                    # Execute trade
                    if signal != 'HOLD':
                        self.execute_trade(symbol, signal, latest['close'])
                    else:
                        logger.info(f"No action for {symbol} - holding position")
                        
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}", exc_info=True)
                    continue
            
            logger.info("\n" + "=" * 80)
            logger.info("TECHNICAL INDICATOR TRADING BOT - COMPLETED")
            logger.info("=" * 80)
        
        except Exception as e:
            logger.error(f"Error in main execution loop: {e}", exc_info=True)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Initialize and run bot
        config = TradingConfig()
        bot = TechnicalIndicatorBot(config)
        bot.run()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
