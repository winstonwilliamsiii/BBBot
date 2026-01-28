"""
Probability Engine
==================
Calculates and analyzes prediction probabilities
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime


class ProbabilityEngine:
    """Engine for probability calculations and analysis"""
    
    def __init__(self):
        """Initialize probability engine"""
        pass
    
    def calculate_implied_probability(self, price: float) -> float:
        """Calculate implied probability from market price
        
        Args:
            price: The current market price (0-1)
            
        Returns:
            Implied probability as percentage
        """
        if not 0 <= price <= 1:
            raise ValueError("Price must be between 0 and 1")
        return price * 100
    
    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio for a series of returns
        
        Args:
            returns: List of returns
            risk_free_rate: Risk-free rate for calculation
            
        Returns:
            Sharpe ratio
        """
        if not returns:
            return 0.0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - risk_free_rate
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        return np.mean(excess_returns) / np.std(excess_returns)
    
    def calculate_confidence_score(self, probability: float, market_volume: float) -> float:
        """Calculate confidence score based on probability and market volume
        
        Args:
            probability: The probability (0-1)
            market_volume: Trading volume
            
        Returns:
            Confidence score (0-1)
        """
        # Normalize volume (assuming volume > 100k is high)
        normalized_volume = min(market_volume / 100000, 1.0)
        
        # Probability confidence (higher at extremes)
        prob_confidence = abs(probability - 0.5) * 2
        
        # Combine factors
        confidence = (prob_confidence + normalized_volume) / 2
        return min(confidence, 1.0)
    
    def analyze_market_sentiment(self, markets: List[Dict]) -> Dict:
        """Analyze overall sentiment from market data
        
        Args:
            markets: List of market dictionaries with price and volume
            
        Returns:
            Sentiment analysis results
        """
        if not markets:
            return {"bullish_count": 0, "bearish_count": 0, "neutral_count": 0}
        
        bullish = 0
        bearish = 0
        neutral = 0
        
        for market in markets:
            price = market.get("price", 0.5)
            
            if price > 0.65:
                bullish += 1
            elif price < 0.35:
                bearish += 1
            else:
                neutral += 1
        
        return {
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": neutral,
            "bullish_percentage": (bullish / len(markets)) * 100 if markets else 0,
            "bearish_percentage": (bearish / len(markets)) * 100 if markets else 0,
            "neutral_percentage": (neutral / len(markets)) * 100 if markets else 0
        }
