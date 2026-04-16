"""
Rigel Multi-Pair Forex Trading Bot
===================================

Production-ready mean reversion forex bot with:
- Multi-pair orchestration (7 major forex pairs)
- Advanced risk management and position sizing
- Liquidity discipline controls
- ML prediction hooks for future integration
- Session-based trading (EST 9am-4pm)
- Alpaca API integration

Compatible with: Alpaca Markets (Paper/Live Trading)
Future: MT5 via companion EA script

Author: Bentley Budget Bot Team
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
import requests
from alpaca_trade_api import REST, TimeFrame
from dotenv import load_dotenv

try:
    from scripts.bot_mlflow_benchmark import log_bot_benchmark_run
except ModuleNotFoundError:
    from bot_mlflow_benchmark import log_bot_benchmark_run

load_dotenv(override=True)

try:
    from frontend.components.mt5_connector import MT5Connector
except Exception:
    MT5Connector = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rigel_forex_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def _notify_discord_trade(
    side: str,
    symbol: str,
    qty: float,
    broker: str = "unknown",
    order_id: Optional[str] = None,
) -> None:
    webhook = (
        os.getenv("DISCORD_BOT_TALK_WEBHOOK", "").strip()
        or os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        or os.getenv("DISCORD_WEBHOOK", "").strip()
        or os.getenv("DISCORD_WEBHOOK_PROD", "").strip()
    )
    if not webhook:
        return
    color = 3066993 if str(side).lower() == "buy" else 15158332
    order_label = f" | order: {order_id}" if order_id else ""
    embed = {
        "title": f"🤖 Rigel Trade: {side.upper()} {symbol}",
        "description": f"Qty: {qty} via {broker}{order_label}",
        "color": color,
    }
    try:
        requests.post(webhook, json={"embeds": [embed]}, timeout=5)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Discord trade notification failed: %s", exc)


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"


class MLPrediction(Enum):
    """ML Model predictions"""
    MEAN_REVERT = "mean_revert"
    TREND_CONTINUATION = "trend_continuation"
    NEUTRAL = "neutral"
    HIGH_VOLATILITY = "high_volatility"


@dataclass
class TradingSignal:
    """Trading signal with metadata"""
    symbol: str
    signal_type: SignalType
    confidence: float
    price: float
    timestamp: datetime
    indicators: Dict
    ml_prediction: Optional[MLPrediction] = None
    
    def __str__(self):
        return (f"{self.signal_type.value} {self.symbol} @ ${self.price:.5f} "
                f"(Confidence: {self.confidence:.1%})")


@dataclass
class RiskMetrics:
    """Risk management metrics"""
    account_equity: float
    available_cash: float
    open_positions_value: float
    liquidity_ratio: float
    max_position_size: float
    position_count: int
    max_positions_allowed: int
    
    def can_open_position(self) -> bool:
        """Check if new position can be opened"""
        return (self.position_count < self.max_positions_allowed and
                self.liquidity_ratio >= 0.20 and  # Maintain 20% cash minimum
                self.available_cash > self.max_position_size)


# ============================================================================
# CONFIGURATION
# ============================================================================

class ForexConfig:
    """Rigel Forex Bot Configuration"""
    
    # ===== API Configuration =====
    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
    ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
    ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    BROKER_PLATFORM = os.getenv("BROKER_PLATFORM", "alpaca").lower()

    # ===== MT5 Configuration =====
    MT5_API_URL = os.getenv("MT5_API_URL", "http://localhost:8002")
    MT5_USER = os.getenv("MT5_USER")
    MT5_PASSWORD = os.getenv("MT5_PASSWORD")
    MT5_HOST = os.getenv("MT5_HOST")
    MT5_PORT = int(os.getenv("MT5_PORT", "443"))
    
    # ===== Trading Pairs =====
    # Major forex pairs with good liquidity
    FOREX_PAIRS = [
        "EUR/USD",  # Euro / US Dollar
        "GBP/USD",  # British Pound / US Dollar
        "USD/JPY",  # US Dollar / Japanese Yen
        "USD/CHF",  # US Dollar / Swiss Franc
        "AUD/USD",  # Australian Dollar / US Dollar
        "NZD/USD",  # New Zealand Dollar / US Dollar
        "USD/CAD",  # US Dollar / Canadian Dollar
    ]
    
    # ===== Trading Session =====
    SESSION_START_HOUR = 9   # 9 AM EST
    SESSION_END_HOUR = 16    # 4 PM EST
    TIMEZONE = "America/New_York"
    
    # ===== Technical Indicators =====
    EMA_FAST = 20
    EMA_SLOW = 50
    RSI_PERIOD = 14
    RSI_OVERSOLD = 45  # Mean reversion threshold for longs
    RSI_OVERBOUGHT = 55  # Mean reversion threshold for shorts
    BB_PERIOD = 20
    BB_STD = 2
    ATR_PERIOD = 14
    
    # ===== Risk Management =====
    RISK_PER_TRADE = 0.01  # 1% of account per trade
    MAX_OPEN_POSITIONS = 3  # Liquidity discipline
    LIQUIDITY_BUFFER = 0.25  # 25% cash reserve minimum
    MIN_ACCOUNT_BALANCE = 1000  # Safety threshold
    
    # Position sizing limits (in units for forex)
    MIN_POSITION_SIZE = 1000   # Micro lot (0.01 standard lot)
    MAX_POSITION_SIZE = 100000  # 1 standard lot
    
    # ===== Stop Loss / Take Profit (in pips) =====
    STOP_LOSS_PIPS = {
        "long": 50,   # For long positions
        "short": 30,  # For short positions
    }
    TAKE_PROFIT_PIPS = {
        "long": 100,
        "short": 60,
    }
    
    # ===== ML Integration =====
    ENABLE_ML = os.getenv("ENABLE_ML", "false").lower() == "true"
    ML_MODEL_PATH = os.getenv("ML_MODEL_PATH", "models/rigel_forex_model.pkl")
    ML_CONFIDENCE_THRESHOLD = 0.70  # Only trade on high-confidence ML signals
    
    # ===== Safety Controls =====
    DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
    ENABLE_TRADING = os.getenv("ENABLE_TRADING", "false").lower() == "true"
    MAX_DAILY_LOSS = 0.05  # 5% max daily loss
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if cls.BROKER_PLATFORM not in {"alpaca", "mt5"}:
            raise ValueError("BROKER_PLATFORM must be 'alpaca' or 'mt5'")

        if cls.BROKER_PLATFORM == "alpaca":
            if not cls.ALPACA_API_KEY or not cls.ALPACA_SECRET_KEY:
                raise ValueError("Missing Alpaca API credentials")
        elif not cls.MT5_API_URL:
            raise ValueError("Missing MT5_API_URL for MT5 broker platform")
        
        logger.info("=" * 70)
        logger.info("RIGEL FOREX BOT CONFIGURATION")
        logger.info("=" * 70)
        logger.info(f"Trading Pairs: {len(cls.FOREX_PAIRS)} pairs")
        logger.info(f"Broker Platform: {cls.BROKER_PLATFORM.upper()}")
        logger.info(f"Session Hours: {cls.SESSION_START_HOUR}:00 - {cls.SESSION_END_HOUR}:00 EST")
        logger.info(f"Risk Per Trade: {cls.RISK_PER_TRADE * 100}%")
        logger.info(f"Max Positions: {cls.MAX_OPEN_POSITIONS}")
        logger.info(f"Liquidity Buffer: {cls.LIQUIDITY_BUFFER * 100}%")
        logger.info(f"ML Enabled: {cls.ENABLE_ML}")
        logger.info(f"Dry Run: {cls.DRY_RUN}")
        logger.info(f"Trading Enabled: {cls.ENABLE_TRADING}")
        logger.info("=" * 70)


# ============================================================================
# TECHNICAL INDICATORS
# ============================================================================

class TechnicalIndicators:
    """Calculate technical indicators for trading signals"""
    
    @staticmethod
    def calculate_ema(data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_bollinger_bands(data: pd.Series, period: int = 20, std: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = data.rolling(window=period).mean()
        std_dev = data.rolling(window=period).std()
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        return upper_band, sma, lower_band
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def analyze_indicators(df: pd.DataFrame, config: ForexConfig) -> Dict:
        """Analyze all technical indicators"""
        close = df['close']
        
        # Calculate indicators
        ema_fast = TechnicalIndicators.calculate_ema(close, config.EMA_FAST)
        ema_slow = TechnicalIndicators.calculate_ema(close, config.EMA_SLOW)
        rsi = TechnicalIndicators.calculate_rsi(close, config.RSI_PERIOD)
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.calculate_bollinger_bands(
            close, config.BB_PERIOD, config.BB_STD
        )
        
        # Get latest values
        current_price = close.iloc[-1]
        current_ema_fast = ema_fast.iloc[-1]
        current_ema_slow = ema_slow.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_bb_upper = bb_upper.iloc[-1]
        current_bb_lower = bb_lower.iloc[-1]
        
        return {
            'price': current_price,
            'ema_fast': current_ema_fast,
            'ema_slow': current_ema_slow,
            'rsi': current_rsi,
            'bb_upper': current_bb_upper,
            'bb_middle': bb_middle.iloc[-1],
            'bb_lower': current_bb_lower,
            'trend': 'bullish' if current_ema_fast > current_ema_slow else 'bearish',
            'near_lower_band': (current_price - current_bb_lower) / current_bb_lower < 0.01,
            'near_upper_band': (current_bb_upper - current_price) / current_bb_upper < 0.01,
        }


# ============================================================================
# ML PREDICTION ENGINE (LSTM + XGBoost Hybrid)
# ============================================================================

class MLPredictor:
    """
    Hybrid ML prediction engine combining:
    - LSTM: Sequential price forecasting (short-term patterns)
    - XGBoost: Feature-driven predictions (technical + macro factors)
    
    Ensemble logic provides robust signals
    """
    
    def __init__(self, model_path: str = None, enabled: bool = False):
        self.enabled = enabled
        self.model_path = model_path
        self.lstm_model = None
        self.xgb_model = None
        self.scaler = None
        
        # Sequence length for LSTM
        self.sequence_length = 60  # 60 hours of data
        
        # Recent data cache for LSTM
        self.price_history = {}  # symbol -> deque of recent prices
        
        if self.enabled and model_path:
            self._load_models()
    
    def _load_models(self):
        """Load LSTM and XGBoost models from disk"""
        try:
            import joblib
            import os
            import glob
            
            # Model paths
            base_path = os.path.dirname(self.model_path)
            lstm_path = os.path.join(base_path, 'rigel_lstm_model.h5')
            xgb_path = os.path.join(base_path, 'rigel_xgb_model.pkl')
            scaler_path = os.path.join(base_path, 'rigel_scaler.pkl')

            # Fallback: use latest symbol-specific artifacts if canonical names are missing.
            if not os.path.exists(lstm_path):
                lstm_candidates = glob.glob(os.path.join(base_path, '*_lstm_model.h5'))
                if lstm_candidates:
                    lstm_path = max(lstm_candidates, key=os.path.getmtime)
            if not os.path.exists(xgb_path):
                xgb_candidates = glob.glob(os.path.join(base_path, '*_xgb_model.pkl'))
                if xgb_candidates:
                    xgb_path = max(xgb_candidates, key=os.path.getmtime)
            if not os.path.exists(scaler_path):
                scaler_candidates = glob.glob(os.path.join(base_path, '*_scaler.pkl'))
                if scaler_candidates:
                    scaler_path = max(scaler_candidates, key=os.path.getmtime)
            
            # Try to load models
            if os.path.exists(lstm_path):
                try:
                    from tensorflow import keras
                    self.lstm_model = keras.models.load_model(lstm_path)
                    logger.info(f"LSTM model loaded from {lstm_path}")
                except ImportError:
                    logger.warning("TensorFlow not installed - LSTM disabled")
            
            if os.path.exists(xgb_path):
                try:
                    import xgboost
                    self.xgb_model = joblib.load(xgb_path)
                    logger.info(f"XGBoost model loaded from {xgb_path}")
                except ImportError:
                    logger.warning("XGBoost not installed - XGBoost disabled")
            
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                logger.info("Feature scaler loaded")
            
            # If no models loaded, disable ML
            if not self.lstm_model and not self.xgb_model:
                logger.warning("No ML models found - using fallback logic")
                self.enabled = False
            
        except Exception as e:
            logger.error(f"Failed to load ML models: {e}")
            self.enabled = False
    
    def _prepare_lstm_features(self, symbol: str, recent_prices: List[float]) -> Optional[np.ndarray]:
        """
        Prepare sequential features for LSTM
        
        Args:
            symbol: Trading pair
            recent_prices: List of recent close prices
        
        Returns:
            Normalized sequence array shape (1, sequence_length, 1) or None
        """
        try:
            from collections import deque
            
            # Initialize price history for symbol if needed
            if symbol not in self.price_history:
                self.price_history[symbol] = deque(maxlen=self.sequence_length)
            
            # Add new prices to history
            for price in recent_prices:
                self.price_history[symbol].append(price)
            
            # Check if we have enough data
            if len(self.price_history[symbol]) < self.sequence_length:
                return None
            
            # Convert to array and normalize
            sequence = np.array(list(self.price_history[symbol]))
            
            # Min-max normalization for LSTM
            min_val = sequence.min()
            max_val = sequence.max()
            
            if max_val > min_val:
                normalized = (sequence - min_val) / (max_val - min_val)
            else:
                normalized = sequence
            
            # Reshape for LSTM: (batch_size, timesteps, features)
            return normalized.reshape(1, self.sequence_length, 1)
            
        except Exception as e:
            logger.error(f"LSTM feature preparation error: {e}")
            return None
    
    def _prepare_xgb_features(self, indicators: Dict) -> Optional[np.ndarray]:
        """
        Prepare feature vector for XGBoost
        
        Args:
            indicators: Dictionary of technical indicators
        
        Returns:
            Feature array or None
        """
        try:
            # Extract features in consistent order
            features = [
                indicators['price'],
                indicators['ema_fast'],
                indicators['ema_slow'],
                indicators['rsi'],
                indicators['bb_upper'],
                indicators['bb_middle'],
                indicators['bb_lower'],
                
                # Derived features
                indicators['ema_fast'] - indicators['ema_slow'],  # EMA diff
                indicators['price'] - indicators['bb_middle'],    # Price deviation from middle
                (indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle'],  # BB width
                
                # Normalized position in BB
                (indicators['price'] - indicators['bb_lower']) / 
                (indicators['bb_upper'] - indicators['bb_lower']) if 
                (indicators['bb_upper'] - indicators['bb_lower']) > 0 else 0.5,
            ]
            
            features_array = np.array(features).reshape(1, -1)
            
            # Apply scaler if available
            if self.scaler is not None:
                features_array = self.scaler.transform(features_array)
            
            return features_array
            
        except Exception as e:
            logger.error(f"XGBoost feature preparation error: {e}")
            return None
    
    def _lstm_predict(self, symbol: str, recent_prices: List[float]) -> Optional[str]:
        """
        LSTM prediction: "revert", "trend", or None
        
        Predicts next price movement based on sequential patterns
        """
        if not self.lstm_model:
            return None
        
        try:
            # Prepare features
            X = self._prepare_lstm_features(symbol, recent_prices)
            if X is None:
                return None
            
            # Make prediction
            prediction = self.lstm_model.predict(X, verbose=0)[0][0]
            
            # Interpret prediction
            # prediction > 0.6: price will increase (trend continuation or revert up)
            # prediction < 0.4: price will decrease (trend continuation or revert down)
            # 0.4 <= prediction <= 0.6: neutral
            
            current_price = recent_prices[-1]
            recent_avg = np.mean(recent_prices[-10:]) if len(recent_prices) >= 10 else current_price
            
            # If price below average and predicting increase = mean revert
            # If price above average and predicting decrease = mean revert
            if prediction > 0.6 and current_price < recent_avg:
                return "revert"
            elif prediction < 0.4 and current_price > recent_avg:
                return "revert"
            elif prediction > 0.6 or prediction < 0.4:
                return "trend"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"LSTM prediction error: {e}")
            return None
    
    def _xgb_predict(self, indicators: Dict) -> Optional[str]:
        """
        XGBoost prediction: "revert", "trend", or None
        
        Predicts market behavior based on technical indicators
        """
        if not self.xgb_model:
            return None
        
        try:
            # Prepare features
            X = self._prepare_xgb_features(indicators)
            if X is None:
                return None
            
            # Make prediction
            # XGBoost model output: 0=neutral, 1=revert, 2=trend
            prediction = self.xgb_model.predict(X)[0]
            
            prediction_map = {
                0: "neutral",
                1: "revert",
                2: "trend"
            }
            
            return prediction_map.get(int(prediction), "neutral")
            
        except Exception as e:
            logger.error(f"XGBoost prediction error: {e}")
            return None
    
    def predict(self, symbol: str, indicators: Dict, recent_prices: List[float] = None) -> MLPrediction:
        """
        Hybrid ensemble prediction combining LSTM and XGBoost
        
        Args:
            symbol: Trading pair symbol
            indicators: Technical indicator values
            recent_prices: List of recent close prices for LSTM
        
        Returns:
            MLPrediction enum
        """
        if not self.enabled:
            return MLPrediction.NEUTRAL
        
        try:
            # Get predictions from both models
            lstm_signal = self._lstm_predict(symbol, recent_prices) if recent_prices else None
            xgb_signal = self._xgb_predict(indicators)
            
            # Ensemble logic
            # Both agree on mean revert = high confidence mean revert
            if lstm_signal == "revert" and xgb_signal == "revert":
                return MLPrediction.MEAN_REVERT
            
            # One predicts revert, other neutral = medium confidence revert
            elif (lstm_signal == "revert" and xgb_signal == "neutral") or \
                 (lstm_signal == "neutral" and xgb_signal == "revert"):
                return MLPrediction.MEAN_REVERT
            
            # Both agree on trend = trend continuation
            elif lstm_signal == "trend" and xgb_signal == "trend":
                return MLPrediction.TREND_CONTINUATION
            
            # One predicts trend, other neutral = medium confidence trend
            elif (lstm_signal == "trend" and xgb_signal == "neutral") or \
                 (lstm_signal == "neutral" and xgb_signal == "trend"):
                return MLPrediction.TREND_CONTINUATION
            
            # Disagreement or both neutral = neutral
            else:
                return MLPrediction.NEUTRAL
                
        except Exception as e:
            logger.error(f"Hybrid prediction error for {symbol}: {e}")
            return MLPrediction.NEUTRAL
    
    def get_confidence(self, prediction: MLPrediction, lstm_signal: str = None, xgb_signal: str = None) -> float:
        """
        Calculate confidence score based on model agreement
        
        Higher confidence when both models agree
        """
        if not self.enabled:
            return 0.50
        
        # Base confidence levels
        base_confidence = {
            MLPrediction.MEAN_REVERT: 0.75,
            MLPrediction.TREND_CONTINUATION: 0.70,
            MLPrediction.HIGH_VOLATILITY: 0.65,
            MLPrediction.NEUTRAL: 0.50,
        }
        
        confidence = base_confidence.get(prediction, 0.50)
        
        # Boost confidence if both models available and agreeing
        if self.lstm_model and self.xgb_model:
            if lstm_signal and xgb_signal and lstm_signal == xgb_signal:
                confidence = min(0.95, confidence + 0.15)  # +15% for agreement
        
        return confidence


# ============================================================================
# RISK & LIQUIDITY MANAGER
# ============================================================================

class RiskManager:
    """Manage risk and liquidity for multi-pair trading"""
    
    def __init__(self, config: ForexConfig):
        self.config = config
    
    def get_risk_metrics(self, account: Dict, positions: List) -> RiskMetrics:
        """Calculate current risk metrics"""
        equity = float(account.get('equity', 0))
        cash = float(account.get('cash', 0))
        portfolio_value = float(account.get('portfolio_value', 0))
        
        # Calculate open positions value
        positions_value = portfolio_value - cash
        
        # Liquidity ratio
        liquidity_ratio = cash / portfolio_value if portfolio_value > 0 else 0
        
        # Available cash after buffer
        target_reserve = portfolio_value * self.config.LIQUIDITY_BUFFER
        available_cash = max(0, cash - target_reserve)
        
        # Max position size based on risk
        max_position_size = equity * self.config.RISK_PER_TRADE
        
        return RiskMetrics(
            account_equity=equity,
            available_cash=available_cash,
            open_positions_value=positions_value,
            liquidity_ratio=liquidity_ratio,
            max_position_size=max_position_size,
            position_count=len(positions),
            max_positions_allowed=self.config.MAX_OPEN_POSITIONS
        )
    
    def calculate_position_size(
        self,
        risk_metrics: RiskMetrics,
        entry_price: float,
        stop_loss_pips: int,
        pip_value: float = 0.0001
    ) -> int:
        """
        Calculate optimal position size based on risk
        
        Args:
            risk_metrics: Current risk metrics
            entry_price: Entry price for position
            stop_loss_pips: Stop loss in pips
            pip_value: Value of 1 pip (default 0.0001 for most pairs)
        
        Returns:
            Position size in units
        """
        # Risk amount in dollars
        risk_amount = risk_metrics.max_position_size
        
        # Calculate position size
        # Risk = Position Size * Stop Loss Distance
        stop_loss_distance = stop_loss_pips * pip_value
        
        if stop_loss_distance > 0:
            position_size = risk_amount / stop_loss_distance
        else:
            position_size = 0
        
        # Apply min/max limits
        position_size = max(self.config.MIN_POSITION_SIZE, position_size)
        position_size = min(self.config.MAX_POSITION_SIZE, position_size)
        
        # Round to nearest 1000 (micro lot)
        position_size = round(position_size / 1000) * 1000
        
        return int(position_size)
    
    def check_daily_loss_limit(self, account: Dict) -> bool:
        """Check if daily loss limit has been exceeded"""
        # TODO: Track daily P&L
        # For now, check if account is above minimum
        equity = float(account.get('equity', 0))
        return equity >= self.config.MIN_ACCOUNT_BALANCE


# ============================================================================
# TRADING STRATEGY
# ============================================================================

class MeanReversionStrategy:
    """Mean reversion strategy for forex pairs"""
    
    def __init__(self, config: ForexConfig, ml_predictor: MLPredictor):
        self.config = config
        self.ml_predictor = ml_predictor
    
    def generate_signal(
        self,
        symbol: str,
        indicators: Dict,
        risk_metrics: RiskMetrics,
        recent_prices: List[float] = None
    ) -> Optional[TradingSignal]:
        """
        Generate trading signal based on mean reversion logic + ML predictions
        
        Long Signal:
        - EMA Fast > EMA Slow (uptrend confirmed)
        - RSI < 45 (oversold, mean revert up expected)
        - Price near lower Bollinger Band
        - ML prediction confirms (optional)
        
        Short Signal:
        - EMA Fast < EMA Slow (downtrend confirmed)
        - RSI > 55 (overbought, mean revert down expected)
        - Price near upper Bollinger Band
        - ML prediction confirms (optional)
        """
        
        # Check if we can open new position
        if not risk_metrics.can_open_position():
            logger.info(f"{symbol}: Cannot open position (liquidity/position limit)")
            return None
        
        # Get ML prediction (with LSTM + XGBoost hybrid)
        ml_prediction = self.ml_predictor.predict(symbol, indicators, recent_prices)
        ml_confidence = self.ml_predictor.get_confidence(ml_prediction)
        
        # Mean reversion logic
        price = indicators['price']
        ema_fast = indicators['ema_fast']
        ema_slow = indicators['ema_slow']
        rsi = indicators['rsi']
        near_lower_band = indicators['near_lower_band']
        near_upper_band = indicators['near_upper_band']
        
        signal_type = None
        confidence = 0.0
        
        # LONG SIGNAL (Mean reversion from oversold)
        if (ema_fast > ema_slow and 
            rsi < self.config.RSI_OVERSOLD and 
            near_lower_band):
            
            signal_type = SignalType.BUY
            confidence = 0.70
            
            # Boost confidence if ML agrees
            if ml_prediction == MLPrediction.MEAN_REVERT:
                confidence = min(0.95, confidence + ml_confidence * 0.3)
        
        # SHORT SIGNAL (Mean reversion from overbought)
        elif (ema_fast < ema_slow and 
              rsi > self.config.RSI_OVERBOUGHT and 
              near_upper_band):
            
            signal_type = SignalType.SELL
            confidence = 0.70
            
            # Boost confidence if ML agrees
            if ml_prediction == MLPrediction.MEAN_REVERT:
                confidence = min(0.95, confidence + ml_confidence * 0.3)
        
        # No signal
        if not signal_type:
            return None
        
        # Create trading signal
        return TradingSignal(
            symbol=symbol,
            signal_type=signal_type,
            confidence=confidence,
            price=price,
            timestamp=datetime.now(),
            indicators=indicators,
            ml_prediction=ml_prediction
        )


# ============================================================================
# MAIN TRADING BOT
# ============================================================================

class RigelForexBot:
    """Main Rigel Forex Trading Bot"""
    
    def __init__(self, config: ForexConfig):
        self.config = config
        self.api: Optional[REST] = None
        self.mt5_connector: Optional[MT5Connector] = None
        self.ml_predictor = MLPredictor(config.ML_MODEL_PATH, config.ENABLE_ML)
        self.risk_manager = RiskManager(config)
        self.strategy = MeanReversionStrategy(config, self.ml_predictor)
        self.last_trade_time = {}
        
    def initialize(self):
        """Initialize API connection"""
        if self.config.BROKER_PLATFORM == "mt5":
            try:
                if MT5Connector is None:
                    logger.error("MT5Connector not available")
                    return False

                self.mt5_connector = MT5Connector(self.config.MT5_API_URL)

                if not self.mt5_connector.health_check():
                    logger.error(
                        "MT5 health check failed at %s", self.config.MT5_API_URL
                    )
                    return False

                if self.config.MT5_USER and self.config.MT5_PASSWORD and self.config.MT5_HOST:
                    connected = self.mt5_connector.connect(
                        self.config.MT5_USER,
                        self.config.MT5_PASSWORD,
                        self.config.MT5_HOST,
                        self.config.MT5_PORT,
                    )
                    if not connected:
                        logger.error("Failed to connect to MT5 account")
                        return False
                    account = self.mt5_connector.get_account_info() or {}
                    logger.info("Connected to MT5 API")
                    logger.info("  Balance: %s", account.get("balance", "N/A"))
                    logger.info("  Equity: %s", account.get("equity", "N/A"))
                else:
                    logger.warning(
                        "MT5 credentials not set; running in API-only mode "
                        "(health check passed)"
                    )

                return True
            except Exception as e:
                logger.error(f"Failed to initialize MT5 API: {e}")
                return False

        try:
            self.api = REST(
                self.config.ALPACA_API_KEY,
                self.config.ALPACA_SECRET_KEY,
                self.config.ALPACA_BASE_URL
            )
            
            account = self.api.get_account()
            logger.info("Connected to Alpaca API")
            logger.info(f"  Account ID: {account.id[:8]}...")
            logger.info(f"  Portfolio Value: ${float(account.portfolio_value):,.2f}")
            logger.info(f"  Buying Power: ${float(account.buying_power):,.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca API: {e}")
            return False
    
    def is_trading_session(self) -> bool:
        """Check if current time is within trading session"""
        now = datetime.now()
        current_hour = now.hour
        
        return (self.config.SESSION_START_HOUR <= current_hour <= self.config.SESSION_END_HOUR)
    
    def get_market_data(self, symbol: str, days: int = 100) -> Optional[pd.DataFrame]:
        """Fetch market data for symbol"""
        if self.config.BROKER_PLATFORM == "mt5":
            if not self.mt5_connector:
                logger.error("MT5 connector not initialized")
                return None
            try:
                mt5_symbol = symbol.replace("/", "")
                count = max(100, days * 24)
                payload = self.mt5_connector.get_market_data(mt5_symbol, "H1", count)
                if not payload:
                    return None
                bars = payload.get("bars", [])
                if not bars:
                    return None

                df = pd.DataFrame(bars)
                rename_map = {
                    "time": "timestamp",
                    "open": "open",
                    "high": "high",
                    "low": "low",
                    "close": "close",
                    "tick_volume": "volume",
                    "volume": "volume",
                }
                for source, target in rename_map.items():
                    if source in df.columns and source != target:
                        df = df.rename(columns={source: target})

                required = {"open", "high", "low", "close", "volume"}
                if not required.issubset(set(df.columns)):
                    logger.error("MT5 market data missing required OHLCV columns")
                    return None

                return df
            except Exception as e:
                logger.error(f"Failed to fetch MT5 data for {symbol}: {e}")
                return None

        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            
            # Alpaca forex symbols use format EUR/USD
            bars = self.api.get_bars(
                symbol,
                TimeFrame.Hour,  # Hourly data for forex
                start=start.isoformat(),
                end=end.isoformat()
            ).df
            
            return bars
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            return None
    
    def execute_trade(self, signal: TradingSignal, risk_metrics: RiskMetrics):
        """Execute trade based on signal"""
        
        # Determine stop loss and take profit
        is_long = signal.signal_type == SignalType.BUY
        stop_loss_pips = self.config.STOP_LOSS_PIPS['long' if is_long else 'short']
        take_profit_pips = self.config.TAKE_PROFIT_PIPS['long' if is_long else 'short']
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            risk_metrics,
            signal.price,
            stop_loss_pips
        )
        
        # Calculate stop/target prices
        pip_value = 0.0001  # Standard for most pairs
        if is_long:
            stop_price = signal.price - (stop_loss_pips * pip_value)
            target_price = signal.price + (take_profit_pips * pip_value)
        else:
            stop_price = signal.price + (stop_loss_pips * pip_value)
            target_price = signal.price - (take_profit_pips * pip_value)
        
        logger.info("=" * 70)
        logger.info(f"EXECUTING TRADE: {signal}")
        logger.info(f"  Position Size: {position_size} units")
        logger.info(f"  Entry: ${signal.price:.5f}")
        logger.info(f"  Stop Loss: ${stop_price:.5f} ({stop_loss_pips} pips)")
        logger.info(f"  Take Profit: ${target_price:.5f} ({take_profit_pips} pips)")
        logger.info(f"  Risk/Reward: 1:{take_profit_pips/stop_loss_pips:.2f}")
        
        if signal.ml_prediction:
            logger.info(f"  ML Prediction: {signal.ml_prediction.value}")
        logger.info("=" * 70)
        
        if self.config.DRY_RUN:
            logger.info("DRY RUN - Trade not executed")
            return "simulated"
        
        if not self.config.ENABLE_TRADING:
            logger.warning("Trading disabled in config")
            return "disabled"

        if self.config.BROKER_PLATFORM == "mt5":
            if not self.mt5_connector:
                logger.error("MT5 connector not initialized")
                return

            try:
                side = 'BUY' if is_long else 'SELL'
                mt5_symbol = signal.symbol.replace("/", "")
                lot_size = max(0.01, round(position_size / 100000, 2))

                result = self.mt5_connector.place_trade(
                    symbol=mt5_symbol,
                    order_type=side,
                    volume=lot_size,
                    sl=stop_price,
                    tp=target_price,
                    comment="Rigel mean reversion",
                )

                if result and result.get("success"):
                    logger.info(
                        "MT5 order placed: %s",
                        result.get("ticket", "unknown"),
                    )
                    _notify_discord_trade(side, mt5_symbol, lot_size, "mt5", str(result.get("ticket", "")) or None)
                    return "submitted"
                else:
                    logger.error("Failed to execute MT5 trade: %s", result)
                    return "error"
            except Exception as e:
                logger.error(f"Failed to execute MT5 trade: {e}")
                return "error"
        
        try:
            # Place bracket order with stop loss and take profit
            side = 'buy' if is_long else 'sell'
            
            order = self.api.submit_order(
                symbol=signal.symbol,
                qty=position_size,
                side=side,
                type='limit',
                time_in_force='gtc',
                limit_price=signal.price,
                order_class='bracket',
                stop_loss={'stop_price': stop_price},
                take_profit={'limit_price': target_price}
            )
            
            logger.info(f"Order placed: {order.id}")
            _notify_discord_trade(side, signal.symbol, position_size, "alpaca", str(order.id))
            return "submitted"
            
        except Exception as e:
            logger.error(f"Failed to execute trade: {e}")
            return "error"
    
    def run_cycle(self):
        """Run one trading cycle"""
        cycle_timestamp = datetime.now(timezone.utc).isoformat()
        cycle_result = {
            "bot": "Rigel",
            "fund": "Mansa_FOREX",
            "timestamp": cycle_timestamp,
            "signals_generated": 0.0,
            "executed_signals": 0.0,
            "avg_signal_confidence": 0.0,
        }
        
        # Check trading session
        if not self.is_trading_session():
            logger.debug("Outside trading session")
            cycle_result.update(
                {
                    "status": "skipped_outside_session",
                    "detail": "Rigel cycle skipped outside configured trading hours.",
                }
            )
            log_bot_benchmark_run(
                bot_name="Rigel",
                experiment_name="Rigel_Runtime_Benchmark",
                run_name="Rigel-skipped-session",
                payload=cycle_result,
                strategy_label="FOREX raw strategy",
                discipline_mode="raw_strategy",
                extra_params={
                    "broker_platform": self.config.BROKER_PLATFORM,
                },
                extra_tags={"trade_status": str(cycle_result["status"])},
            )
            return cycle_result
        
        # Get account info
        try:
            if self.config.BROKER_PLATFORM == "mt5":
                if not self.mt5_connector:
                    logger.error("MT5 connector not initialized")
                    return

                raw_account = self.mt5_connector.get_account_info() or {}
                balance = float(raw_account.get("balance", 0.0))
                equity = float(raw_account.get("equity", balance))
                free_margin = float(raw_account.get("margin_free", balance))
                account = {
                    "equity": equity,
                    "cash": free_margin,
                    "portfolio_value": max(equity, 1.0),
                }
                positions = self.mt5_connector.get_positions() or []
            else:
                account = self.api.get_account().__dict__
                positions = self.api.list_positions()
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            cycle_result.update(
                {
                    "status": "account_error",
                    "detail": f"Failed to get account info: {e}",
                }
            )
            log_bot_benchmark_run(
                bot_name="Rigel",
                experiment_name="Rigel_Runtime_Benchmark",
                run_name="Rigel-account-error",
                payload=cycle_result,
                strategy_label="FOREX raw strategy",
                discipline_mode="raw_strategy",
                extra_params={
                    "broker_platform": self.config.BROKER_PLATFORM,
                },
                extra_tags={"trade_status": str(cycle_result["status"])},
            )
            return cycle_result
        
        # Check daily loss limit
        if not self.risk_manager.check_daily_loss_limit(account):
            logger.error("Daily loss limit exceeded - stopping trading")
            cycle_result.update(
                {
                    "status": "blocked_daily_loss_limit",
                    "detail": "Daily loss limit exceeded.",
                }
            )
            log_bot_benchmark_run(
                bot_name="Rigel",
                experiment_name="Rigel_Runtime_Benchmark",
                run_name="Rigel-blocked-daily-loss",
                payload=cycle_result,
                strategy_label="FOREX raw strategy",
                discipline_mode="raw_strategy",
                extra_params={
                    "broker_platform": self.config.BROKER_PLATFORM,
                },
                extra_tags={"trade_status": str(cycle_result["status"])},
            )
            return cycle_result
        
        # Get risk metrics
        risk_metrics = self.risk_manager.get_risk_metrics(account, positions)
        
        logger.info(f"Risk Metrics: {risk_metrics.position_count}/{risk_metrics.max_positions_allowed} positions "
                   f"| Liquidity: {risk_metrics.liquidity_ratio:.1%} "
                   f"| Available: ${risk_metrics.available_cash:,.2f}")
        cycle_result.update(
            {
                "liquidity_ratio": float(risk_metrics.liquidity_ratio),
                "available_cash": float(risk_metrics.available_cash),
                "position_count": float(risk_metrics.position_count),
                "max_positions_allowed": float(risk_metrics.max_positions_allowed),
            }
        )
        
        # Scan pairs for signals
        generated_signals = []
        executed_signals = []
        for pair in self.config.FOREX_PAIRS:
            
            # Rate limiting: min 1 minute between trades per pair
            last_trade = self.last_trade_time.get(pair, datetime.min)
            if (datetime.now() - last_trade).seconds < 60:
                continue
            
            # Get market data
            df = self.get_market_data(pair)
            if df is None or len(df) < 100:
                logger.warning(f"{pair}: Insufficient data")
                continue
            
            # Analyze indicators
            indicators = TechnicalIndicators.analyze_indicators(df, self.config)
            
            # Extract recent prices for ML predictor (last 100 bars)
            recent_prices = df['close'].tail(100).tolist()
            
            # Generate signal (with ML prediction)
            signal = self.strategy.generate_signal(pair, indicators, risk_metrics, recent_prices)
            
            if signal:
                logger.info(f"Signal generated: {signal}")
                generated_signals.append(signal)
                execution_status = self.execute_trade(signal, risk_metrics)
                executed_signals.append(
                    {
                        "symbol": pair,
                        "status": execution_status,
                        "confidence": float(signal.confidence),
                        "ml_prediction": (
                            signal.ml_prediction.value
                            if signal.ml_prediction
                            else "neutral"
                        ),
                    }
                )
                self.last_trade_time[pair] = datetime.now()
            else:
                logger.debug(f"{pair}: No signal (RSI: {indicators['rsi']:.1f}, "
                           f"Trend: {indicators['trend']})")

        if generated_signals:
            avg_confidence = float(
                np.mean([signal.confidence for signal in generated_signals])
            )
            latest_status = str(executed_signals[-1]["status"] or "signal_generated")
            cycle_result.update(
                {
                    "status": latest_status,
                    "detail": (
                        f"Generated {len(generated_signals)} Rigel signals this cycle."
                    ),
                    "signals_generated": float(len(generated_signals)),
                    "executed_signals": float(
                        len(
                            [
                                item for item in executed_signals
                                if item["status"] in {"submitted", "simulated"}
                            ]
                        )
                    ),
                    "avg_signal_confidence": avg_confidence,
                    "latest_symbol": str(generated_signals[-1].symbol),
                    "latest_signal": str(generated_signals[-1].signal_type.value),
                    "latest_rsi": float(generated_signals[-1].indicators.get("rsi", 0.0)),
                    "latest_price": float(generated_signals[-1].price),
                }
            )
            if generated_signals[-1].ml_prediction is not None:
                cycle_result["latest_ml_prediction"] = str(
                    generated_signals[-1].ml_prediction.value
                )
        else:
            cycle_result.update(
                {
                    "status": "no_signal",
                    "detail": "No Rigel signals generated this cycle.",
                }
            )

        log_bot_benchmark_run(
            bot_name="Rigel",
            experiment_name="Rigel_Runtime_Benchmark",
            run_name=f"Rigel-{cycle_result['status']}",
            payload=cycle_result,
            strategy_label="FOREX raw strategy",
            discipline_mode="raw_strategy",
            extra_params={
                "broker_platform": self.config.BROKER_PLATFORM,
                "trading_pairs": ",".join(self.config.FOREX_PAIRS),
                "dry_run": self.config.DRY_RUN,
                "enable_trading": self.config.ENABLE_TRADING,
            },
            extra_tags={"trade_status": str(cycle_result["status"])},
        )
        return cycle_result
    
    def run(self, interval_seconds: int = 300):
        """
        Run bot continuously
        
        Args:
            interval_seconds: Seconds between cycles (default 5 minutes)
        """
        logger.info("=" * 70)
        logger.info("STARTING RIGEL FOREX BOT")
        logger.info("=" * 70)
        
        if not self.initialize():
            logger.error("Initialization failed - exiting")
            return
        
        try:
            while True:
                try:
                    self.run_cycle()
                except Exception as e:
                    logger.error(f"Error in trading cycle: {e}", exc_info=True)
                
                # Sleep until next cycle
                logger.debug(f"Sleeping for {interval_seconds} seconds...")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("\nBot stopped by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    
    # Load configuration
    config = ForexConfig()
    
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("\nSet environment variables:")
        logger.info("  ALPACA_API_KEY=your_key")
        logger.info("  ALPACA_SECRET_KEY=your_secret")
        logger.info("  DRY_RUN=true  # Set to false for live trading")
        logger.info("  ENABLE_TRADING=true  # Enable actual trade execution")
        return
    
    # Create and run bot
    bot = RigelForexBot(config)
    bot.run(interval_seconds=300)  # Run every 5 minutes


if __name__ == "__main__":
    main()
