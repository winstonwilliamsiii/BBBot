"""
Trading Strategies for WeBull Equities & ETFs
Compares Mean Reversion vs Random Forest Regression with MACD/RSI signals
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

try:
    from bbbot1_pipeline.mlflow_tracker import get_tracker
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


class TechnicalIndicators:
    """Calculate technical indicators for trading signals"""
    
    @staticmethod
    def calculate_rsi(prices, period=14):
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """Calculate MACD (Moving Average Convergence Divergence)"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        macd_histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': macd_histogram
        })
    
    @staticmethod
    def calculate_bollinger_bands(prices, period=20, std_dev=2):
        """Calculate Bollinger Bands for mean reversion"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return pd.DataFrame({
            'sma': sma,
            'upper': upper_band,
            'lower': lower_band
        })


class MeanReversionStrategy:
    """
    Mean Reversion Strategy using Bollinger Bands
    - Buy when price touches lower band (oversold)
    - Sell when price touches upper band (overbought)
    """
    
    def __init__(self, bb_period=20, bb_std=2, rsi_oversold=30, rsi_overbought=70):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.name = "Mean_Reversion"
    
    def generate_signals(self, df):
        """
        Generate buy/sell signals based on mean reversion
        
        Args:
            df: DataFrame with 'Close' prices
            
        Returns:
            DataFrame with signals: 1 (buy), -1 (sell), 0 (hold)
        """
        # Calculate indicators
        bb = TechnicalIndicators.calculate_bollinger_bands(
            df['Close'], self.bb_period, self.bb_std
        )
        rsi = TechnicalIndicators.calculate_rsi(df['Close'])
        
        # Initialize signals
        signals = pd.DataFrame(index=df.index)
        signals['price'] = df['Close']
        signals['bb_upper'] = bb['upper']
        signals['bb_lower'] = bb['lower']
        signals['bb_sma'] = bb['sma']
        signals['rsi'] = rsi
        signals['signal'] = 0
        
        # Generate buy signals (oversold + below lower band)
        buy_condition = (
            (df['Close'] <= bb['lower']) & 
            (rsi <= self.rsi_oversold)
        )
        signals.loc[buy_condition, 'signal'] = 1
        
        # Generate sell signals (overbought + above upper band)
        sell_condition = (
            (df['Close'] >= bb['upper']) & 
            (rsi >= self.rsi_overbought)
        )
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals
    
    def backtest(self, df, initial_capital=10000):
        """Simple backtest of mean reversion strategy"""
        signals = self.generate_signals(df)
        
        positions = pd.DataFrame(index=signals.index)
        positions['holdings'] = signals['signal'].cumsum()
        positions['cash'] = initial_capital - (positions['holdings'] * signals['price']).cumsum()
        positions['total'] = positions['cash'] + (positions['holdings'] * signals['price'])
        positions['returns'] = positions['total'].pct_change()
        
        # Calculate metrics
        total_return = (positions['total'].iloc[-1] - initial_capital) / initial_capital
        sharpe_ratio = positions['returns'].mean() / positions['returns'].std() * np.sqrt(252)
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'final_value': positions['total'].iloc[-1],
            'signals': signals,
            'positions': positions
        }


class RandomForestStrategy:
    """
    Random Forest Regression Strategy
    - Uses MACD, RSI, and price features to predict next day returns
    - Generates buy/sell signals based on predicted returns
    """
    
    def __init__(self, n_estimators=100, max_depth=10, lookback=5):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.lookback = lookback
        self.model = None
        self.name = "Random_Forest"
    
    def create_features(self, df):
        """Create features for Random Forest model"""
        features = pd.DataFrame(index=df.index)
        
        # Price features
        features['returns'] = df['Close'].pct_change()
        features['log_returns'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # Moving averages
        for window in [5, 10, 20, 50]:
            features[f'sma_{window}'] = df['Close'].rolling(window=window).mean()
            features[f'sma_{window}_ratio'] = df['Close'] / features[f'sma_{window}']
        
        # MACD signals
        macd = TechnicalIndicators.calculate_macd(df['Close'])
        features['macd'] = macd['macd']
        features['macd_signal'] = macd['signal']
        features['macd_histogram'] = macd['histogram']
        
        # RSI
        features['rsi'] = TechnicalIndicators.calculate_rsi(df['Close'])
        
        # Volume features if available
        if 'Volume' in df.columns:
            features['volume'] = df['Volume']
            features['volume_sma'] = df['Volume'].rolling(window=20).mean()
            features['volume_ratio'] = features['volume'] / features['volume_sma']
        
        # Lagged features
        for lag in range(1, self.lookback + 1):
            features[f'return_lag_{lag}'] = features['returns'].shift(lag)
            features[f'rsi_lag_{lag}'] = features['rsi'].shift(lag)
        
        # Target: next day return
        features['target'] = df['Close'].shift(-1) / df['Close'] - 1
        
        return features.dropna()
    
    def train(self, df):
        """Train Random Forest model"""
        features_df = self.create_features(df)
        
        # Split features and target
        X = features_df.drop('target', axis=1)
        y = features_df['target']
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        # Train model
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        return {
            'mse': mse,
            'r2': r2,
            'feature_importance': pd.DataFrame({
                'feature': X.columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
        }
    
    def generate_signals(self, df, threshold=0.001):
        """
        Generate buy/sell signals based on predicted returns
        
        Args:
            df: DataFrame with OHLCV data
            threshold: Minimum predicted return to trigger signal
            
        Returns:
            DataFrame with signals and predictions
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        features_df = self.create_features(df)
        X = features_df.drop('target', axis=1)
        
        # Predict returns
        predictions = self.model.predict(X)
        
        signals = pd.DataFrame(index=features_df.index)
        signals['price'] = df.loc[features_df.index, 'Close']
        signals['predicted_return'] = predictions
        signals['signal'] = 0
        
        # Generate signals based on predicted returns
        signals.loc[predictions > threshold, 'signal'] = 1   # Buy
        signals.loc[predictions < -threshold, 'signal'] = -1  # Sell
        
        return signals
    
    def backtest(self, df, initial_capital=10000, threshold=0.001):
        """Backtest Random Forest strategy"""
        signals = self.generate_signals(df, threshold)
        
        positions = pd.DataFrame(index=signals.index)
        positions['holdings'] = signals['signal'].cumsum()
        positions['cash'] = initial_capital - (positions['holdings'] * signals['price']).cumsum()
        positions['total'] = positions['cash'] + (positions['holdings'] * signals['price'])
        positions['returns'] = positions['total'].pct_change()
        
        # Calculate metrics
        total_return = (positions['total'].iloc[-1] - initial_capital) / initial_capital
        sharpe_ratio = positions['returns'].mean() / positions['returns'].std() * np.sqrt(252)
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'final_value': positions['total'].iloc[-1],
            'signals': signals,
            'positions': positions
        }


class StrategyComparison:
    """Compare multiple trading strategies with MLFlow tracking"""
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.results = {}
        
        if MLFLOW_AVAILABLE:
            self.tracker = get_tracker()
        else:
            self.tracker = None
    
    def compare_strategies(self, df, ticker):
        """
        Compare Mean Reversion vs Random Forest strategies
        
        Args:
            df: DataFrame with OHLCV data
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with comparison results
        """
        print(f"\n{'='*70}")
        print(f"STRATEGY COMPARISON FOR {ticker}")
        print(f"{'='*70}\n")
        
        # Initialize strategies
        mean_reversion = MeanReversionStrategy()
        random_forest = RandomForestStrategy()
        
        # Train Random Forest
        print("Training Random Forest model...")
        rf_train_results = random_forest.train(df)
        print(f"✅ Random Forest trained - R²: {rf_train_results['r2']:.4f}")
        
        # Backtest both strategies
        print("\nBacktesting Mean Reversion strategy...")
        mr_results = mean_reversion.backtest(df, self.initial_capital)
        
        print("Backtesting Random Forest strategy...")
        rf_results = random_forest.backtest(df, self.initial_capital)
        
        # Compare results
        comparison = {
            'ticker': ticker,
            'mean_reversion': {
                'total_return': mr_results['total_return'],
                'sharpe_ratio': mr_results['sharpe_ratio'],
                'final_value': mr_results['final_value']
            },
            'random_forest': {
                'total_return': rf_results['total_return'],
                'sharpe_ratio': rf_results['sharpe_ratio'],
                'final_value': rf_results['final_value'],
                'r2_score': rf_train_results['r2'],
                'feature_importance': rf_train_results['feature_importance']
            }
        }
        
        # Log to MLFlow
        if self.tracker:
            self._log_to_mlflow(comparison, ticker)
        
        # Print comparison
        self._print_comparison(comparison)
        
        self.results[ticker] = comparison
        return comparison
    
    def _log_to_mlflow(self, comparison, ticker):
        """Log strategy comparison to MLFlow"""
        with self.tracker.start_run(f"Strategy_Comparison_{ticker}"):
            # Mean Reversion metrics
            self.tracker.log_metric("MR_Total_Return", comparison['mean_reversion']['total_return'])
            self.tracker.log_metric("MR_Sharpe_Ratio", comparison['mean_reversion']['sharpe_ratio'])
            self.tracker.log_metric("MR_Final_Value", comparison['mean_reversion']['final_value'])
            
            # Random Forest metrics
            self.tracker.log_metric("RF_Total_Return", comparison['random_forest']['total_return'])
            self.tracker.log_metric("RF_Sharpe_Ratio", comparison['random_forest']['sharpe_ratio'])
            self.tracker.log_metric("RF_Final_Value", comparison['random_forest']['final_value'])
            self.tracker.log_metric("RF_R2_Score", comparison['random_forest']['r2_score'])
            
            # Log parameters
            self.tracker.log_param("ticker", ticker)
            self.tracker.log_param("initial_capital", self.initial_capital)
    
    def _print_comparison(self, comparison):
        """Print formatted comparison results"""
        print(f"\n{'='*70}")
        print("RESULTS COMPARISON")
        print(f"{'='*70}")
        
        print(f"\n{'Strategy':<20} {'Total Return':<15} {'Sharpe Ratio':<15} {'Final Value':<15}")
        print("-" * 70)
        
        mr = comparison['mean_reversion']
        print(f"{'Mean Reversion':<20} {mr['total_return']:>13.2%} {mr['sharpe_ratio']:>14.3f} ${mr['final_value']:>13,.2f}")
        
        rf = comparison['random_forest']
        print(f"{'Random Forest':<20} {rf['total_return']:>13.2%} {rf['sharpe_ratio']:>14.3f} ${rf['final_value']:>13,.2f}")
        
        # Winner
        winner = "Mean Reversion" if mr['total_return'] > rf['total_return'] else "Random Forest"
        print(f"\n🏆 Winner: {winner}")
        
        # Top 5 Random Forest features
        print(f"\n📊 Top 5 Random Forest Features:")
        for i, row in rf['feature_importance'].head(5).iterrows():
            print(f"   {row['feature']:<20} {row['importance']:.4f}")
        
        print(f"\n{'='*70}\n")


if __name__ == "__main__":
    print("Trading Strategies Module")
    print("Use StrategyComparison class to compare Mean Reversion vs Random Forest")
    print("\nExample:")
    print("  from trading_strategies import StrategyComparison")
    print("  import yfinance as yf")
    print("  ")
    print("  df = yf.download('AAPL', start='2023-01-01', end='2024-12-01')")
    print("  comparison = StrategyComparison(initial_capital=10000)")
    print("  results = comparison.compare_strategies(df, 'AAPL')")
