#!/usr/bin/env python3
"""
Rigel Forex Bot - ML Model Training Script
Trains LSTM and XGBoost models for hybrid prediction ensemble

USAGE:
    python scripts/train_rigel_models.py --symbol EUR/USD --days 365
    python scripts/train_rigel_models.py --all-pairs --days 180
    
OUTPUTS:
    models/rigel/EURUSD_lstm_model.h5
    models/rigel/EURUSD_xgb_model.pkl
    models/rigel/EURUSD_scaler.pkl
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Tuple, List
import logging

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

# ML imports with graceful fallback
try:
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    LSTM_AVAILABLE = True
except ImportError:
    LSTM_AVAILABLE = False
    print("⚠️ TensorFlow not available - LSTM training disabled")

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("⚠️ XGBoost not available - XGBoost training disabled")

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.rigel_forex_bot import ForexConfig, TechnicalIndicators
from alpaca_trade_api import REST, TimeFrame

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class RigelModelTrainer:
    """Train LSTM and XGBoost models for forex prediction"""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str = 'https://paper-api.alpaca.markets'):
        """
        Initialize trainer with Alpaca API credentials
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            base_url: Alpaca API base URL (paper or live)
        """
        self.api = REST(api_key, api_secret, base_url)
        self.config = ForexConfig()
        self.models_dir = project_root / 'models' / 'rigel'
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
    def fetch_training_data(
        self,
        symbol: str,
        days: int = 365,
        timeframe: TimeFrame = TimeFrame.Hour
    ) -> pd.DataFrame:
        """
        Fetch historical forex data from Alpaca
        
        Args:
            symbol: Forex pair (e.g., 'EUR/USD')
            days: Number of days of historical data
            timeframe: Timeframe for bars (Hour, Day, etc.)
            
        Returns:
            DataFrame with OHLCV data and technical indicators
        """
        logger.info(f"Fetching {days} days of {timeframe} data for {symbol}")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            # Fetch bars
            bars = self.api.get_bars(
                symbol,
                timeframe,
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d')
            ).df
            
            if bars.empty:
                raise ValueError(f"No data returned for {symbol}")
            
            # Reset index and rename columns
            bars = bars.reset_index()
            bars.rename(columns={
                'timestamp': 'datetime',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }, inplace=True)
            
            logger.info(f"✓ Fetched {len(bars)} bars for {symbol}")
            return bars
            
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            raise
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for feature engineering
        
        Args:
            df: Raw OHLCV DataFrame
            
        Returns:
            DataFrame with technical indicators added
        """
        logger.info("Computing technical indicators...")
        
        # Calculate EMAs
        df['ema_fast'] = df['close'].ewm(span=self.config.EMA_FAST, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.config.EMA_SLOW, adjust=False).mean()
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.config.RSI_PERIOD).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.config.RSI_PERIOD).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Calculate Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=self.config.BB_PERIOD).mean()
        bb_std = df['close'].rolling(window=self.config.BB_PERIOD).std()
        df['bb_upper'] = df['bb_middle'] + (self.config.BB_STD * bb_std)
        df['bb_lower'] = df['bb_middle'] - (self.config.BB_STD * bb_std)
        
        # Calculate ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        
        # Derived features for XGBoost
        df['price_to_ema_fast'] = df['close'] / df['ema_fast']
        df['price_to_ema_slow'] = df['close'] / df['ema_slow']
        df['ema_ratio'] = df['ema_fast'] / df['ema_slow']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Drop NaN values from indicator calculations
        df = df.dropna()
        
        logger.info(f"✓ Computed indicators, {len(df)} valid rows")
        return df
    
    def create_labels(self, df: pd.DataFrame, lookahead: int = 10) -> pd.Series:
        """
        Create labels for supervised learning
        
        Strategy:
        - Label = 0 (NEUTRAL) if price doesn't move significantly
        - Label = 1 (MEAN_REVERT) if price reverts towards EMA after extremes
        - Label = 2 (TREND) if price continues in current direction
        
        Args:
            df: DataFrame with price and indicator data
            lookahead: Number of bars to look ahead for labeling
            
        Returns:
            Series with labels (0=neutral, 1=mean_revert, 2=trend)
        """
        logger.info(f"Creating labels with {lookahead}-bar lookahead...")
        
        labels = []
        
        for i in range(len(df) - lookahead):
            current_price = df.iloc[i]['close']
            future_price = df.iloc[i + lookahead]['close']
            current_ema = df.iloc[i]['ema_fast']
            current_rsi = df.iloc[i]['rsi']
            
            price_change_pct = (future_price - current_price) / current_price * 100
            
            # Mean reversion scenario
            if (current_rsi < 35 and price_change_pct > 0.2) or \
               (current_rsi > 65 and price_change_pct < -0.2):
                labels.append(1)  # MEAN_REVERT
            # Trend continuation scenario
            elif abs(price_change_pct) > 0.5:
                labels.append(2)  # TREND
            # Neutral scenario
            else:
                labels.append(0)  # NEUTRAL
        
        # Pad with neutral for lookahead period
        labels.extend([0] * lookahead)
        
        logger.info(f"✓ Label distribution: "
                   f"Neutral={labels.count(0)}, "
                   f"Revert={labels.count(1)}, "
                   f"Trend={labels.count(2)}")
        
        return pd.Series(labels)
    
    def train_lstm_model(
        self,
        df: pd.DataFrame,
        sequence_length: int = 60,
        epochs: int = 50,
        batch_size: int = 32
    ) -> Tuple[Sequential, StandardScaler]:
        """
        Train LSTM model for sequential price prediction
        
        Args:
            df: DataFrame with features and labels
            sequence_length: Number of time steps for LSTM sequences
            epochs: Training epochs
            batch_size: Batch size
            
        Returns:
            Tuple of (trained model, scaler)
        """
        if not LSTM_AVAILABLE:
            raise RuntimeError("TensorFlow not installed - cannot train LSTM")
        
        logger.info("Training LSTM model...")
        
        # Prepare sequences
        prices = df['close'].values
        labels = df['label'].values
        
        # Normalize prices
        scaler = StandardScaler()
        prices_scaled = scaler.fit_transform(prices.reshape(-1, 1))
        
        # Create sequences
        X, y = [], []
        for i in range(sequence_length, len(prices_scaled)):
            X.append(prices_scaled[i-sequence_length:i, 0])
            y.append(labels[i])
        
        X = np.array(X)
        y = np.array(y)
        X = X.reshape(X.shape[0], X.shape[1], 1)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        logger.info(f"Training set: {X_train.shape}, Test set: {X_test.shape}")
        
        # Build LSTM model
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(sequence_length, 1)),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25, activation='relu'),
            Dense(3, activation='softmax')  # 3 classes: neutral, revert, trend
        ])
        
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        # Train with early stopping
        early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        
        history = model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop],
            verbose=1
        )
        
        # Evaluate
        test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
        logger.info(f"✓ LSTM Test Accuracy: {test_acc:.2%}")
        
        return model, scaler
    
    def train_xgboost_model(
        self,
        df: pd.DataFrame,
        n_estimators: int = 100,
        max_depth: int = 6
    ) -> xgb.XGBClassifier:
        """
        Train XGBoost model for feature-based classification
        
        Args:
            df: DataFrame with features and labels
            n_estimators: Number of boosting rounds
            max_depth: Maximum tree depth
            
        Returns:
            Trained XGBoost classifier
        """
        if not XGB_AVAILABLE:
            raise RuntimeError("XGBoost not installed - cannot train XGBoost model")
        
        logger.info("Training XGBoost model...")
        
        # Feature columns
        feature_cols = [
            'close', 'ema_fast', 'ema_slow', 'rsi',
            'bb_upper', 'bb_middle', 'bb_lower',
            'price_to_ema_fast', 'price_to_ema_slow',
            'ema_ratio', 'bb_position'
        ]
        
        X = df[feature_cols].values
        y = df['label'].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        logger.info(f"Training set: {X_train.shape}, Test set: {X_test.shape}")
        
        # Train XGBoost
        model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=0.1,
            objective='multi:softmax',
            num_class=3,
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        train_acc = model.score(X_train, y_train)
        test_acc = model.score(X_test, y_test)
        
        logger.info(f"✓ XGBoost Train Accuracy: {train_acc:.2%}")
        logger.info(f"✓ XGBoost Test Accuracy: {test_acc:.2%}")
        
        return model
    
    def save_models(
        self,
        symbol: str,
        lstm_model: Sequential,
        xgb_model: xgb.XGBClassifier,
        scaler: StandardScaler
    ):
        """
        Save trained models to disk
        
        Args:
            symbol: Forex pair (e.g., 'EUR/USD')
            lstm_model: Trained LSTM model
            xgb_model: Trained XGBoost model
            scaler: Fitted StandardScaler
        """
        # Convert symbol to filename format (EUR/USD -> EURUSD)
        symbol_clean = symbol.replace('/', '')
        
        lstm_path = self.models_dir / f"{symbol_clean}_lstm_model.h5"
        xgb_path = self.models_dir / f"{symbol_clean}_xgb_model.pkl"
        scaler_path = self.models_dir / f"{symbol_clean}_scaler.pkl"
        
        logger.info(f"Saving models to {self.models_dir}...")
        
        # Save LSTM
        if LSTM_AVAILABLE and lstm_model:
            lstm_model.save(lstm_path)
            logger.info(f"✓ Saved LSTM model: {lstm_path}")
        
        # Save XGBoost
        if XGB_AVAILABLE and xgb_model:
            joblib.dump(xgb_model, xgb_path)
            logger.info(f"✓ Saved XGBoost model: {xgb_path}")
        
        # Save scaler
        if scaler:
            joblib.dump(scaler, scaler_path)
            logger.info(f"✓ Saved scaler: {scaler_path}")
    
    def train_symbol(
        self,
        symbol: str,
        days: int = 365,
        lstm_epochs: int = 50,
        xgb_estimators: int = 100
    ):
        """
        Complete training pipeline for a single symbol
        
        Args:
            symbol: Forex pair to train
            days: Days of historical data
            lstm_epochs: LSTM training epochs
            xgb_estimators: XGBoost estimator count
        """
        logger.info("=" * 70)
        logger.info(f"TRAINING MODELS FOR {symbol}")
        logger.info("=" * 70)
        
        try:
            # Fetch data
            df = self.fetch_training_data(symbol, days)
            
            # Prepare features
            df = self.prepare_features(df)
            
            # Create labels
            df['label'] = self.create_labels(df, lookahead=10)
            
            # Train LSTM
            lstm_model, scaler = None, None
            if LSTM_AVAILABLE:
                lstm_model, scaler = self.train_lstm_model(df, epochs=lstm_epochs)
            
            # Train XGBoost
            xgb_model = None
            if XGB_AVAILABLE:
                xgb_model = self.train_xgboost_model(df, n_estimators=xgb_estimators)
            
            # Save models
            self.save_models(symbol, lstm_model, xgb_model, scaler)
            
            logger.info(f"✅ Successfully trained models for {symbol}")
            
        except Exception as e:
            logger.error(f"❌ Training failed for {symbol}: {e}")
            raise


def main():
    """Main training script entry point"""
    parser = argparse.ArgumentParser(description='Train Rigel Forex Bot ML models')
    parser.add_argument('--symbol', type=str, help='Forex pair to train (e.g., EUR/USD)')
    parser.add_argument('--all-pairs', action='store_true', help='Train all configured pairs')
    parser.add_argument('--days', type=int, default=365, help='Days of historical data (default: 365)')
    parser.add_argument('--lstm-epochs', type=int, default=50, help='LSTM training epochs (default: 50)')
    parser.add_argument('--xgb-estimators', type=int, default=100, help='XGBoost estimators (default: 100)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.symbol and not args.all_pairs:
        parser.error("Must specify either --symbol or --all-pairs")
    
    # Load credentials from environment
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_SECRET_KEY') or os.getenv('ALPACA_API_SECRET')
    
    if not api_key or not api_secret:
        logger.error("❌ Missing Alpaca API credentials")
        logger.error(
            "Set ALPACA_API_KEY and ALPACA_SECRET_KEY "
            "(or ALPACA_API_SECRET) environment variables"
        )
        sys.exit(1)
    
    # Initialize trainer
    trainer = RigelModelTrainer(api_key, api_secret)
    
    # Train symbols
    if args.all_pairs:
        symbols = trainer.config.FOREX_PAIRS
        logger.info(f"Training models for {len(symbols)} pairs: {', '.join(symbols)}")
        
        for symbol in symbols:
            try:
                trainer.train_symbol(
                    symbol,
                    days=args.days,
                    lstm_epochs=args.lstm_epochs,
                    xgb_estimators=args.xgb_estimators
                )
            except Exception as e:
                logger.error(f"Skipping {symbol} due to error: {e}")
                continue
    else:
        trainer.train_symbol(
            args.symbol,
            days=args.days,
            lstm_epochs=args.lstm_epochs,
            xgb_estimators=args.xgb_estimators
        )
    
    logger.info("=" * 70)
    logger.info("✅ TRAINING COMPLETE")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
