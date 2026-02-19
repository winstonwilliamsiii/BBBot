"""
Unit Tests for Rigel Forex Bot
================================

Tests for:
- Risk management
- Position sizing
- Liquidity controls
- Technical indicators
- Signal generation
- ML prediction hooks
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.rigel_forex_bot import (
    ForexConfig,
    TechnicalIndicators,
    MLPredictor,
    MLPrediction,
    RiskManager,
    RiskMetrics,
    MeanReversionStrategy,
    SignalType,
    TradingSignal,
    RigelForexBot
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def config():
    """Create test configuration"""
    config = ForexConfig()
    config.ALPACA_API_KEY = "test_key"
    config.ALPACA_SECRET_KEY = "test_secret"
    config.DRY_RUN = True
    config.ENABLE_TRADING = False
    return config


@pytest.fixture
def sample_price_data():
    """Generate sample price data for testing"""
    dates = pd.date_range(start='2025-01-01', periods=100, freq='H')
    
    # Generate realistic price movements
    np.random.seed(42)
    price = 1.08000  # EUR/USD starting price
    prices = [price]
    
    for _ in range(99):
        change = np.random.normal(0, 0.0001)  # Small random changes
        price += change
        prices.append(price)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p + np.random.uniform(0, 0.0001) for p in prices],
        'low': [p - np.random.uniform(0, 0.0001) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    df.set_index('timestamp', inplace=True)
    return df


@pytest.fixture
def risk_metrics():
    """Sample risk metrics"""
    return RiskMetrics(
        account_equity=10000.0,
        available_cash=2500.0,
        open_positions_value=7500.0,
        liquidity_ratio=0.25,
        max_position_size=100.0,
        position_count=2,
        max_positions_allowed=3
    )


@pytest.fixture
def ml_predictor():
    """ML predictor instance"""
    return MLPredictor(enabled=False)


# ============================================================================
# TEST RISK MANAGER
# ============================================================================

class TestRiskManager:
    """Test risk management functionality"""
    
    def test_risk_metrics_calculation(self, config):
        """Test risk metrics are calculated correctly"""
        manager = RiskManager(config)
        
        account = {
            'equity': '10000.00',
            'cash': '2500.00',
            'portfolio_value': '10000.00'
        }
        positions = [Mock(), Mock()]  # 2 positions
        
        metrics = manager.get_risk_metrics(account, positions)
        
        assert metrics.account_equity == 10000.0
        assert metrics.available_cash == 0.0  # 2500 - (10000 * 0.25) = 0
        assert metrics.liquidity_ratio == 0.25
        assert metrics.position_count == 2
        assert metrics.max_position_size == 100.0  # 10000 * 0.01
    
    def test_position_sizing_basic(self, config):
        """Test basic position sizing calculation"""
        manager = RiskManager(config)
        
        risk_metrics = RiskMetrics(
            account_equity=10000.0,
            available_cash=2500.0,
            open_positions_value=7500.0,
            liquidity_ratio=0.25,
            max_position_size=100.0,  # 1% of 10000
            position_count=1,
            max_positions_allowed=3
        )
        
        # Test for EUR/USD with 50 pip stop loss
        entry_price = 1.08000
        stop_loss_pips = 50
        pip_value = 0.0001
        
        position_size = manager.calculate_position_size(
            risk_metrics,
            entry_price,
            stop_loss_pips,
            pip_value
        )
        
        # Expected: 100 / (50 * 0.0001) = 20,000 units
        # Rounded to nearest 1000
        assert position_size == 20000
    
    def test_position_sizing_with_min_max_limits(self, config):
        """Test position sizing respects min/max limits"""
        manager = RiskManager(config)
        
        # Scenario 1: Very small risk (should hit minimum)
        risk_metrics_small = RiskMetrics(
            account_equity=1000.0,
            available_cash=250.0,
            open_positions_value=750.0,
            liquidity_ratio=0.25,
            max_position_size=10.0,  # Very small
            position_count=0,
            max_positions_allowed=3
        )
        
        position_size = manager.calculate_position_size(
            risk_metrics_small,
            1.08000,
            50,
            0.0001
        )
        
        assert position_size >= config.MIN_POSITION_SIZE
        
        # Scenario 2: Very large risk (should hit maximum)
        risk_metrics_large = RiskMetrics(
            account_equity=1000000.0,
            available_cash=250000.0,
            open_positions_value=750000.0,
            liquidity_ratio=0.25,
            max_position_size=10000.0,  # Very large
            position_count=0,
            max_positions_allowed=3
        )
        
        position_size = manager.calculate_position_size(
            risk_metrics_large,
            1.08000,
            10,  # Small stop
            0.0001
        )
        
        assert position_size <= config.MAX_POSITION_SIZE
    
    def test_daily_loss_limit_check(self, config):
        """Test daily loss limit is enforced"""
        manager = RiskManager(config)
        
        # Account above minimum
        account_good = {'equity': '5000.00'}
        assert manager.check_daily_loss_limit(account_good) is True
        
        # Account below minimum
        account_bad = {'equity': '500.00'}
        assert manager.check_daily_loss_limit(account_bad) is False


# ============================================================================
# TEST RISK METRICS
# ============================================================================

class TestRiskMetrics:
    """Test RiskMetrics dataclass"""
    
    def test_can_open_position_with_capacity(self):
        """Test can open position when capacity exists"""
        metrics = RiskMetrics(
            account_equity=10000.0,
            available_cash=2500.0,
            open_positions_value=7500.0,
            liquidity_ratio=0.25,
            max_position_size=100.0,
            position_count=1,
            max_positions_allowed=3
        )
        
        assert metrics.can_open_position() is True
    
    def test_cannot_open_position_max_positions(self):
        """Test cannot open position at max positions"""
        metrics = RiskMetrics(
            account_equity=10000.0,
            available_cash=2500.0,
            open_positions_value=7500.0,
            liquidity_ratio=0.25,
            max_position_size=100.0,
            position_count=3,  # At max
            max_positions_allowed=3
        )
        
        assert metrics.can_open_position() is False
    
    def test_cannot_open_position_low_liquidity(self):
        """Test cannot open position with low liquidity"""
        metrics = RiskMetrics(
            account_equity=10000.0,
            available_cash=100.0,  # Very low
            open_positions_value=9900.0,
            liquidity_ratio=0.10,  # Below 20% threshold
            max_position_size=100.0,
            position_count=1,
            max_positions_allowed=3
        )
        
        assert metrics.can_open_position() is False
    
    def test_cannot_open_position_insufficient_cash(self):
        """Test cannot open position with insufficient cash"""
        metrics = RiskMetrics(
            account_equity=10000.0,
            available_cash=50.0,  # Less than max_position_size
            open_positions_value=9950.0,
            liquidity_ratio=0.25,
            max_position_size=100.0,
            position_count=1,
            max_positions_allowed=3
        )
        
        assert metrics.can_open_position() is False


# ============================================================================
# TEST TECHNICAL INDICATORS
# ============================================================================

class TestTechnicalIndicators:
    """Test technical indicator calculations"""
    
    def test_ema_calculation(self, sample_price_data):
        """Test EMA calculation"""
        close_prices = sample_price_data['close']
        ema_20 = TechnicalIndicators.calculate_ema(close_prices, 20)
        
        assert len(ema_20) == len(close_prices)
        assert not ema_20.isnull().all()
        # EMA should be smooth (not too volatile)
        assert ema_20.std() < close_prices.std()
    
    def test_rsi_calculation(self, sample_price_data):
        """Test RSI calculation"""
        close_prices = sample_price_data['close']
        rsi = TechnicalIndicators.calculate_rsi(close_prices, 14)
        
        assert len(rsi) == len(close_prices)
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        assert valid_rsi.min() >= 0
        assert valid_rsi.max() <= 100
    
    def test_bollinger_bands_calculation(self, sample_price_data):
        """Test Bollinger Bands calculation"""
        close_prices = sample_price_data['close']
        upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(
            close_prices, 20, 2
        )
        
        # Bands should exist
        assert len(upper) == len(close_prices)
        assert len(middle) == len(close_prices)
        assert len(lower) == len(close_prices)
        
        # Upper > Middle > Lower
        valid_data = ~(upper.isnull() | middle.isnull() | lower.isnull())
        assert (upper[valid_data] >= middle[valid_data]).all()
        assert (middle[valid_data] >= lower[valid_data]).all()
    
    def test_analyze_indicators(self, sample_price_data, config):
        """Test full indicator analysis"""
        indicators = TechnicalIndicators.analyze_indicators(sample_price_data, config)
        
        # Check all expected keys exist
        expected_keys = [
            'price', 'ema_fast', 'ema_slow', 'rsi',
            'bb_upper', 'bb_middle', 'bb_lower',
            'trend', 'near_lower_band', 'near_upper_band'
        ]
        
        for key in expected_keys:
            assert key in indicators
        
        # Check trend is calculated correctly
        if indicators['ema_fast'] > indicators['ema_slow']:
            assert indicators['trend'] == 'bullish'
        else:
            assert indicators['trend'] == 'bearish'


# ============================================================================
# TEST ML PREDICTOR
# ============================================================================

class TestMLPredictor:
    """Test ML prediction functionality"""
    
    def test_predictor_disabled_by_default(self):
        """Test predictor returns neutral when disabled"""
        predictor = MLPredictor(enabled=False)
        
        indicators = {'rsi': 50, 'ema_fast': 1.08, 'ema_slow': 1.07}
        prediction = predictor.predict("EUR/USD", indicators)
        
        assert prediction == MLPrediction.NEUTRAL
        assert predictor.get_confidence(prediction) == 0.50
    
    def test_predictor_placeholder_logic(self):
        """Test ML predictor with proper price history"""
        predictor = MLPredictor(enabled=True)
        
        # Create downtrend price history (for mean revert up signal)
        recent_prices = [1.0850 - (i * 0.0001) for i in range(100)]
        
        # Oversold condition
        indicators_oversold = {
            'rsi': 25,
            'ema_fast': 1.08,
            'ema_slow': 1.07,
            'price': 1.0760,
            'bb_upper': 1.0850,
            'bb_middle': 1.0800,
            'bb_lower': 1.0750
        }
        prediction = predictor.predict("EUR/USD", indicators_oversold, recent_prices)
        # Without trained models, predictor should return NEUTRAL
        assert prediction == MLPrediction.NEUTRAL
        
        # Overbought condition with uptrend prices
        recent_prices_up = [1.0750 + (i * 0.0001) for i in range(100)]
        indicators_overbought = {
            'rsi': 75,
            'ema_fast': 1.08,
            'ema_slow': 1.07,
            'price': 1.0840,
            'bb_upper': 1.0850,
            'bb_middle': 1.0800,
            'bb_lower': 1.0750
        }
        prediction = predictor.predict("EUR/USD", indicators_overbought, recent_prices_up)
        # Without trained models, predictor should return NEUTRAL
        assert prediction == MLPrediction.NEUTRAL
        
        # Neutral condition
        indicators_neutral = {'rsi': 50, 'ema_fast': 1.08, 'ema_slow': 1.07}
        prediction = predictor.predict("EUR/USD", indicators_neutral)
        assert prediction == MLPrediction.NEUTRAL


# ============================================================================
# TEST MEAN REVERSION STRATEGY
# ============================================================================

class TestMeanReversionStrategy:
    """Test mean reversion strategy logic"""
    
    def test_long_signal_generation(self, config, ml_predictor, risk_metrics):
        """Test long signal is generated correctly"""
        strategy = MeanReversionStrategy(config, ml_predictor)
        
        # Create bullish mean reversion setup
        indicators = {
            'price': 1.08000,
            'ema_fast': 1.08100,  # Fast > Slow (bullish)
            'ema_slow': 1.08000,
            'rsi': 40,  # Oversold
            'bb_upper': 1.08500,
            'bb_middle': 1.08000,
            'bb_lower': 1.07998,  # Price near lower band
            'trend': 'bullish',
            'near_lower_band': True,
            'near_upper_band': False
        }
        
        # Create recent price history for ML predictor
        recent_prices = [1.0800 + (i * 0.0001) for i in range(100)]
        
        signal = strategy.generate_signal("EUR/USD", indicators, risk_metrics, recent_prices)
        
        assert signal is not None
        assert signal.signal_type == SignalType.BUY
        assert signal.confidence >= 0.70
        assert signal.symbol == "EUR/USD"
        assert signal.price == 1.08000
    
    def test_short_signal_generation(self, config, ml_predictor, risk_metrics):
        """Test short signal is generated correctly"""
        strategy = MeanReversionStrategy(config, ml_predictor)
        
        # Create bearish mean reversion setup
        indicators = {
            'price': 1.08000,
            'ema_fast': 1.07900,  # Fast < Slow (bearish)
            'ema_slow': 1.08000,
            'rsi': 60,  # Overbought
            'bb_upper': 1.08002,  # Price near upper band
            'bb_middle': 1.08000,
            'bb_lower': 1.07500,
            'trend': 'bearish',
            'near_lower_band': False,
            'near_upper_band': True
        }
        
        # Create recent price history for ML predictor
        recent_prices = [1.0800 - (i * 0.0001) for i in range(100)]
        
        signal = strategy.generate_signal("EUR/USD", indicators, risk_metrics, recent_prices)
        
        assert signal is not None
        assert signal.signal_type == SignalType.SELL
        assert signal.confidence >= 0.70
    
    def test_no_signal_when_conditions_not_met(self, config, ml_predictor, risk_metrics):
        """Test no signal when conditions not met"""
        strategy = MeanReversionStrategy(config, ml_predictor)
        
        # Neutral market conditions
        indicators = {
            'price': 1.08000,
            'ema_fast': 1.08000,
            'ema_slow': 1.08000,
            'rsi': 50,  # Neutral
            'bb_upper': 1.08500,
            'bb_middle': 1.08000,
            'bb_lower': 1.07500,
            'trend': 'neutral',
            'near_lower_band': False,
            'near_upper_band': False
        }
        
        # Create recent price history for ML predictor
        recent_prices = [1.0800 for _ in range(100)]
        
        signal = strategy.generate_signal("EUR/USD", indicators, risk_metrics, recent_prices)
        
        assert signal is None
    
    def test_no_signal_when_liquidity_insufficient(self, config, ml_predictor):
        """Test no signal when liquidity is insufficient"""
        strategy = MeanReversionStrategy(config, ml_predictor)
        
        # Low liquidity risk metrics
        risk_metrics_low = RiskMetrics(
            account_equity=10000.0,
            available_cash=50.0,  # Very low
            open_positions_value=9950.0,
            liquidity_ratio=0.10,  # Below threshold
            max_position_size=100.0,
            position_count=3,  # At max
            max_positions_allowed=3
        )
        
        # Perfect technical setup
        indicators = {
            'price': 1.08000,
            'ema_fast': 1.08100,
            'ema_slow': 1.08000,
            'rsi': 40,
            'bb_upper': 1.08500,
            'bb_middle': 1.08000,
            'bb_lower': 1.07998,
            'trend': 'bullish',
            'near_lower_band': True,
            'near_upper_band': False
        }
        
        # Create recent price history for ML predictor
        recent_prices = [1.0800 + (i * 0.0001) for i in range(100)]
        
        signal = strategy.generate_signal("EUR/USD", indicators, risk_metrics_low, recent_prices)
        
        # Should be None due to liquidity constraints
        assert signal is None


# ============================================================================
# TEST MAIN BOT
# ============================================================================

class TestRigelForexBot:
    """Test main bot functionality"""
    
    def test_initialization(self, config):
        """Test bot initializes correctly"""
        bot = RigelForexBot(config)
        
        assert bot.config == config
        assert bot.ml_predictor is not None
        assert bot.risk_manager is not None
        assert bot.strategy is not None
        assert bot.last_trade_time == {}
    
    def test_trading_session_check(self, config):
        """Test trading session detection"""
        bot = RigelForexBot(config)
        
        # Mock datetime to test different hours
        with patch('scripts.rigel_forex_bot.datetime') as mock_datetime:
            # During session (10 AM)
            mock_datetime.now.return_value = datetime(2026, 2, 18, 10, 0)
            assert bot.is_trading_session() is True
            
            # Outside session (8 AM)
            mock_datetime.now.return_value = datetime(2026, 2, 18, 8, 0)
            assert bot.is_trading_session() is False
            
            # Outside session (5 PM)
            mock_datetime.now.return_value = datetime(2026, 2, 18, 17, 0)
            assert bot.is_trading_session() is False
    
    @patch('scripts.rigel_forex_bot.REST')
    def test_initialization_success(self, mock_rest, config):
        """Test successful API initialization"""
        bot = RigelForexBot(config)
        
        # Mock API
        mock_api = Mock()
        mock_account = Mock()
        mock_account.id = "test123456"
        mock_account.portfolio_value = "10000.00"
        mock_account.buying_power = "5000.00"
        mock_api.get_account.return_value = mock_account
        mock_rest.return_value = mock_api
        
        result = bot.initialize()
        
        assert result is True
        assert bot.api is not None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for full workflow"""
    
    @patch('scripts.rigel_forex_bot.REST')
    def test_full_signal_to_execution_flow(self, mock_rest, config, sample_price_data):
        """Test complete flow from data to signal to execution"""
        # Setup
        bot = RigelForexBot(config)
        
        # Mock API with proper account object
        mock_api = Mock()
        
        # Create account using a simple class
        class MockAccount:
            def __init__(self):
                self.id = "test123"
                self.portfolio_value = "10000.00"
                self.buying_power = "5000.00"
                self.equity = "10000.00"
                self.cash = "2500.00"
        
        mock_account = MockAccount()
        
        # Configure mock API
        mock_api.get_account.return_value = mock_account
        mock_api.list_positions.return_value = []
        mock_rest.return_value = mock_api
        bot.api = mock_api
        
        # Mock market data
        bot.get_market_data = Mock(return_value=sample_price_data)
        
        # Run cycle (should not crash)
        with patch.object(bot, 'is_trading_session', return_value=True):
            bot.run_cycle()
        
        # Verify data was fetched
        assert bot.get_market_data.called


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
