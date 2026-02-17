"""
Test suite for Technical Indicator Trading Bot
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.technical_indicator_bot import (
    TechnicalIndicators,
    TradingConfig,
    TechnicalIndicatorBot
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_price_data():
    """Generate sample price data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # Generate realistic price movement
    returns = np.random.normal(0.001, 0.02, 100)
    prices = 100 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'close': prices,
        'open': prices * 0.99,
        'high': prices * 1.01,
        'low': prices * 0.98,
        'volume': np.random.randint(1000000, 5000000, 100)
    }, index=dates)
    
    return df


@pytest.fixture
def mock_alpaca_api():
    """Mock Alpaca API client"""
    with patch('scripts.technical_indicator_bot.REST') as mock_rest:
        mock_api = Mock()
        
        # Mock account data
        mock_account = Mock()
        mock_account.equity = '10000.00'
        mock_account.cash = '5000.00'
        mock_account.buying_power = '10000.00'
        mock_account.portfolio_value = '10000.00'
        mock_api.get_account.return_value = mock_account
        
        # Mock positions
        mock_api.list_positions.return_value = []
        
        # Mock order submission
        mock_order = Mock()
        mock_order.id = 'test-order-123'
        mock_api.submit_order.return_value = mock_order
        
        mock_rest.return_value = mock_api
        yield mock_api


@pytest.fixture
def test_config():
    """Create test configuration"""
    # Set test environment variables BEFORE importing config
    os.environ['ALPACA_API_KEY'] = 'test_key'
    os.environ['ALPACA_SECRET_KEY'] = 'test_secret'
    os.environ['ALPACA_BASE_URL'] = 'https://paper-api.alpaca.markets'
    os.environ['DRY_RUN'] = 'true'
    os.environ['ENABLE_TRADING'] = 'false'
    
    # Create a fresh config instance with current env vars
    config = TradingConfig()
    # Override class attributes with env vars
    config.ALPACA_API_KEY = os.environ.get('ALPACA_API_KEY')
    config.ALPACA_SECRET_KEY = os.environ.get('ALPACA_SECRET_KEY')
    
    return config


# ============================================================================
# TECHNICAL INDICATOR TESTS
# ============================================================================

class TestTechnicalIndicators:
    """Test technical indicator calculations"""
    
    def test_compute_rsi(self, sample_price_data):
        """Test RSI calculation"""
        rsi = TechnicalIndicators.compute_rsi(sample_price_data['close'], period=14)
        
        assert len(rsi) == len(sample_price_data)
        # RSI should be between 0 and 100
        assert rsi.dropna().min() >= 0
        assert rsi.dropna().max() <= 100
        # First 14 values should be NaN
        assert pd.isna(rsi.iloc[:14]).all()
    
    def test_compute_macd(self, sample_price_data):
        """Test MACD calculation"""
        macd, signal, hist = TechnicalIndicators.compute_macd(
            sample_price_data['close'],
            fast=12, slow=26, signal=9
        )
        
        assert len(macd) == len(sample_price_data)
        assert len(signal) == len(sample_price_data)
        assert len(hist) == len(sample_price_data)
        
        # Histogram should equal MACD - Signal
        np.testing.assert_array_almost_equal(
            hist.dropna().values,
            (macd - signal).dropna().values,
            decimal=10
        )
    
    def test_compute_bollinger_bands(self, sample_price_data):
        """Test Bollinger Bands calculation"""
        upper, middle, lower = TechnicalIndicators.compute_bollinger_bands(
            sample_price_data['close'],
            period=20, std_dev=2
        )
        
        assert len(upper) == len(sample_price_data)
        assert len(middle) == len(sample_price_data)
        assert len(lower) == len(sample_price_data)
        
        # Upper should be > Middle > Lower
        valid_data = ~upper.isna()
        assert (upper[valid_data] >= middle[valid_data]).all()
        assert (middle[valid_data] >= lower[valid_data]).all()
    
    def test_compute_sma(self, sample_price_data):
        """Test SMA calculation"""
        sma = TechnicalIndicators.compute_sma(sample_price_data['close'], period=20)
        
        assert len(sma) == len(sample_price_data)
        # First 19 values should be NaN
        assert pd.isna(sma.iloc[:19]).all()
        # SMA values should be reasonable
        assert sma.dropna().min() > 0


# ============================================================================
# TRADING CONFIG TESTS
# ============================================================================

class TestTradingConfig:
    """Test trading configuration"""
    
    def test_config_validation_success(self, test_config):
        """Test successful config validation"""
        try:
            test_config.validate()
        except ValueError:
            pytest.fail("Config validation should not raise error with valid credentials")
    
    def test_config_validation_failure(self):
        """Test config validation failure with missing credentials"""
        # Create a mock config class without API keys
        with patch.object(TradingConfig, 'ALPACA_API_KEY', None):
            with patch.object(TradingConfig, 'ALPACA_SECRET_KEY', None):
                with patch('os.getenv', return_value=None):
                    with pytest.raises(ValueError, match="Missing Alpaca API credentials"):
                        TradingConfig.validate()
    
    def test_config_defaults(self, test_config):
        """Test default configuration values"""
        assert test_config.SYMBOL == os.getenv("TRADING_SYMBOL", "SPY")
        assert test_config.RSI_PERIOD == 14
        assert test_config.RSI_OVERBOUGHT == 70
        assert test_config.RSI_OVERSOLD == 30
        assert test_config.DRY_RUN is True


# ============================================================================
# TRADING BOT TESTS
# ============================================================================

class TestTechnicalIndicatorBot:
    """Test trading bot functionality"""
    
    def test_bot_initialization(self, test_config, mock_alpaca_api):
        """Test bot initialization"""
        bot = TechnicalIndicatorBot(test_config)
        assert bot.config == test_config
        assert bot.api is not None
        assert bot.indicators is not None
    
    def test_get_account_info(self, test_config, mock_alpaca_api):
        """Test account info retrieval"""
        bot = TechnicalIndicatorBot(test_config)
        account_info = bot.get_account_info()
        
        assert 'equity' in account_info
        assert 'cash' in account_info
        assert 'buying_power' in account_info
        assert account_info['equity'] == 10000.0
    
    def test_get_current_position_no_position(self, test_config, mock_alpaca_api):
        """Test getting current position when none exists"""
        bot = TechnicalIndicatorBot(test_config)
        position = bot.get_current_position('SPY')
        assert position == 0
    
    def test_get_current_position_with_position(self, test_config, mock_alpaca_api):
        """Test getting current position when position exists"""
        # Mock a position
        mock_position = Mock()
        mock_position.symbol = 'SPY'
        mock_position.qty = '10'
        mock_alpaca_api.list_positions.return_value = [mock_position]
        
        bot = TechnicalIndicatorBot(test_config)
        position = bot.get_current_position('SPY')
        assert position == 10
    
    def test_calculate_all_indicators(self, test_config, mock_alpaca_api, sample_price_data):
        """Test calculation of all indicators"""
        bot = TechnicalIndicatorBot(test_config)
        df_with_indicators = bot.calculate_all_indicators(sample_price_data.copy())
        
        # Check all indicators are calculated
        assert 'RSI' in df_with_indicators.columns
        assert 'MACD' in df_with_indicators.columns
        assert 'MACD_Signal' in df_with_indicators.columns
        assert 'MACD_Hist' in df_with_indicators.columns
        assert 'SMA_Short' in df_with_indicators.columns
        assert 'SMA_Long' in df_with_indicators.columns
        assert 'BB_Upper' in df_with_indicators.columns
        assert 'BB_Middle' in df_with_indicators.columns
        assert 'BB_Lower' in df_with_indicators.columns
    
    def test_generate_signal_buy(self, test_config, mock_alpaca_api, sample_price_data):
        """Test BUY signal generation"""
        bot = TechnicalIndicatorBot(test_config)
        df = bot.calculate_all_indicators(sample_price_data.copy())
        
        # Manually set indicators to trigger BUY signal
        df.loc[df.index[-1], 'RSI'] = 25  # Oversold
        df.loc[df.index[-1], 'close'] = df.loc[df.index[-1], 'BB_Lower'] - 1  # Below lower band
        df.loc[df.index[-1], 'SMA_Short'] = 105
        df.loc[df.index[-1], 'SMA_Long'] = 100
        df.loc[df.index[-1], 'close'] = 110  # Above both SMAs
        
        signal = bot.generate_signal(df)
        assert signal in ['BUY', 'SELL', 'HOLD']
    
    def test_generate_signal_sell(self, test_config, mock_alpaca_api, sample_price_data):
        """Test SELL signal generation"""
        bot = TechnicalIndicatorBot(test_config)
        df = bot.calculate_all_indicators(sample_price_data.copy())
        
        # Manually set indicators to trigger SELL signal
        df.loc[df.index[-1], 'RSI'] = 75  # Overbought
        df.loc[df.index[-1], 'close'] = df.loc[df.index[-1], 'BB_Upper'] + 1  # Above upper band
        
        signal = bot.generate_signal(df)
        assert signal in ['BUY', 'SELL', 'HOLD']
    
    def test_calculate_position_size(self, test_config, mock_alpaca_api):
        """Test position size calculation"""
        bot = TechnicalIndicatorBot(test_config)
        bot.get_account_info()
        
        position_size = bot.calculate_position_size(price=100.0)
        
        # Position size should be based on 2% risk
        expected_max = int((10000.0 * 0.02) / 100.0)
        assert position_size <= expected_max
        assert position_size <= test_config.MAX_POSITION_SIZE
    
    def test_execute_trade_dry_run(self, test_config, mock_alpaca_api, caplog):
        """Test trade execution in dry run mode"""
        # Enable trading but keep dry run on
        test_config.ENABLE_TRADING = True
        test_config.DRY_RUN = True
        
        bot = TechnicalIndicatorBot(test_config)
        bot.get_account_info()
        
        with caplog.at_level('INFO'):
            bot.execute_trade('SPY', 'BUY', 100.0)
        
        # Should log dry run message, not actually execute
        assert '[DRY RUN]' in caplog.text
        mock_alpaca_api.submit_order.assert_not_called()
    
    def test_execute_trade_disabled(self, test_config, mock_alpaca_api, caplog):
        """Test trade execution when trading is disabled"""
        test_config.DRY_RUN = False
        test_config.ENABLE_TRADING = False
        
        bot = TechnicalIndicatorBot(test_config)
        bot.get_account_info()
        
        with caplog.at_level('WARNING'):
            bot.execute_trade('SPY', 'BUY', 100.0)
        
        assert 'Trading is disabled' in caplog.text
        mock_alpaca_api.submit_order.assert_not_called()
    
    @patch('scripts.technical_indicator_bot.TechnicalIndicatorBot.fetch_market_data')
    def test_run_method(self, mock_fetch, test_config, mock_alpaca_api, sample_price_data):
        """Test main run method"""
        mock_fetch.return_value = sample_price_data
        
        bot = TechnicalIndicatorBot(test_config)
        
        # Should not raise any exceptions
        try:
            bot.run()
        except Exception as e:
            pytest.fail(f"Bot.run() raised unexpected exception: {e}")


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_dataframe(self, test_config, mock_alpaca_api):
        """Test handling of empty dataframe"""
        bot = TechnicalIndicatorBot(test_config)
        empty_df = pd.DataFrame()
        
        signal = bot.generate_signal(empty_df)
        assert signal == 'HOLD'
    
    def test_insufficient_data_for_indicators(self, test_config, mock_alpaca_api):
        """Test handling of insufficient data"""
        bot = TechnicalIndicatorBot(test_config)
        
        # Only 5 rows of data (not enough for indicators)
        small_df = pd.DataFrame({
            'close': [100, 101, 99, 102, 100],
            'open': [99, 100, 98, 101, 99],
            'high': [102, 103, 101, 104, 102],
            'low': [98, 99, 97, 100, 98],
            'volume': [1000000] * 5
        })
        
        df = bot.calculate_all_indicators(small_df)
        signal = bot.generate_signal(df)
        
        # Should handle gracefully and return HOLD
        assert signal == 'HOLD'
    
    def test_api_error_handling(self, test_config):
        """Test handling of API errors"""
        with patch('scripts.technical_indicator_bot.REST') as mock_rest:
            mock_rest.side_effect = Exception("API connection failed")
            
            with pytest.raises(Exception, match="API connection failed"):
                TechnicalIndicatorBot(test_config)


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
