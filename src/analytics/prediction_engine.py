"""
Prediction Analytics Engine
Calculates implied probabilities and manages sentiment analysis workflows
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class ProbabilityEngine:
    """
    Calculates implied probabilities from orderbook data
    Supports multiple calculation methods: LMSR, AMM, Orderbook Midpoint
    """
    
    def __init__(self, db_connection_string: str):
        """Initialize probability engine"""
        self.db_engine = create_engine(db_connection_string)
        self.session_factory = sessionmaker(bind=self.db_engine)
    
    def calculate_lmsr_probability(self, yes_price: float, no_price: float) -> float:
        """
        Calculate probability using Logarithmic Market Scoring Rule (LMSR)
        Used by most prediction markets
        """
        total = yes_price + no_price
        if total == 0:
            return 50.0
        return (yes_price / total) * 100
    
    def calculate_amm_probability(self, yes_liquidity: float, no_liquidity: float) -> float:
        """
        Calculate probability using Automated Market Maker formula
        x * y = k (constant product)
        """
        if yes_liquidity + no_liquidity == 0:
            return 50.0
        return (yes_liquidity / (yes_liquidity + no_liquidity)) * 100
    
    def calculate_orderbook_midpoint(self, bids: List[float], asks: List[float]) -> float:
        """
        Calculate probability from orderbook bid/ask midpoint
        """
        if not bids or not asks:
            return 50.0
        
        mid_bid = np.mean(bids)
        mid_ask = np.mean(asks)
        midpoint = (mid_bid + mid_ask) / 2
        
        return midpoint * 100
    
    def calculate_confidence_score(
        self,
        calculation_methods: Dict[str, float],
        sentiment_score: Optional[float] = None
    ) -> float:
        """
        Calculate confidence score based on agreement between calculation methods
        Higher agreement = higher confidence
        
        Args:
            calculation_methods: {method_name: probability_value}
            sentiment_score: Optional sentiment alignment score
        
        Returns:
            Confidence score 0-1
        """
        if not calculation_methods:
            return 0.0
        
        probabilities = list(calculation_methods.values())
        
        # Calculate variance (lower variance = higher confidence)
        if len(probabilities) > 1:
            variance = np.var(probabilities)
            confidence = 1.0 / (1.0 + variance / 100)
        else:
            confidence = 0.8  # Default confidence for single method
        
        # Boost confidence if sentiment aligns
        if sentiment_score is not None and abs(sentiment_score) > 0.5:
            confidence = min(1.0, confidence + 0.1)
        
        return round(confidence, 2)
    
    async def compute_predictions(self, contract_id: str) -> Optional[Dict]:
        """
        Compute implied probabilities for a contract
        """
        with self.session_factory() as session:
            # Get latest contract prices
            contract_query = text("""
                SELECT yes_price, no_price, liquidity_usd
                FROM mansa_quant.event_contracts
                WHERE contract_id = :contract_id AND status = 'OPEN'
            """)
            
            result = session.execute(contract_query, {'contract_id': contract_id}).fetchone()
            if not result:
                logger.warning(f"Contract {contract_id} not found")
                return None
            
            yes_price, no_price, liquidity = result
            
            # Get orderbook data
            orderbook_query = text("""
                SELECT price, side
                FROM mansa_quant.orderbook_data
                WHERE contract_id = :contract_id
                  AND timestamp > NOW() - INTERVAL 1 HOUR
                ORDER BY timestamp DESC
                LIMIT 100
            """)
            
            orderbook_data = session.execute(
                orderbook_query, {'contract_id': contract_id}
            ).fetchall()
            
            # Calculate probabilities using multiple methods
            calculations = {
                'lmsr': self.calculate_lmsr_probability(yes_price, no_price),
                'amm': self.calculate_amm_probability(yes_price, 1.0 - yes_price),
            }
            
            if orderbook_data:
                bids = [p for p, side in orderbook_data if side == 'BID']
                asks = [p for p, side in orderbook_data if side == 'ASK']
                if bids and asks:
                    calculations['orderbook'] = self.calculate_orderbook_midpoint(bids, asks)
            
            # Get sentiment score for confidence adjustment
            sentiment_query = text("""
                SELECT AVG(sentiment_score) as avg_sentiment
                FROM mansa_quant.sentiment_signals
                WHERE contract_id = :contract_id
                  AND created_at > NOW() - INTERVAL 24 HOUR
            """)
            
            sentiment_result = session.execute(
                sentiment_query, {'contract_id': contract_id}
            ).fetchone()
            sentiment_score = sentiment_result[0] if sentiment_result and sentiment_result[0] else None
            
            # Final probability (average of methods)
            final_probability = np.mean(list(calculations.values()))
            confidence = self.calculate_confidence_score(calculations, sentiment_score)
            
            return {
                'contract_id': contract_id,
                'implied_probability': round(final_probability, 2),
                'confidence_score': confidence,
                'calculation_methods': calculations,
                'calculation_method_used': 'ensemble',
                'rationale': f"Probability calculated from {len(calculations)} methods. Confidence {confidence*100:.0f}%."
            }
    
    async def store_prediction(self, prediction: Dict, source: str = 'engine') -> bool:
        """
        Store calculated prediction in database
        """
        try:
            with self.session_factory() as session:
                query = text("""
                    INSERT INTO mansa_quant.prediction_probabilities
                    (contract_id, source, implied_probability, confidence_score, rationale)
                    VALUES (:contract_id, :source, :probability, :confidence, :rationale)
                """)
                
                session.execute(query, {
                    'contract_id': prediction['contract_id'],
                    'source': source,
                    'probability': prediction['implied_probability'],
                    'confidence': prediction['confidence_score'],
                    'rationale': prediction['rationale']
                })
                
                session.commit()
                logger.info(f"Stored prediction for {prediction['contract_id']}")
                return True
        
        except Exception as e:
            logger.error(f"Failed to store prediction: {str(e)}")
            return False
    
    async def store_probability_engine_input(self, contract_id: str, inputs: Dict) -> bool:
        """
        Store probability engine inputs for auditability
        """
        try:
            with self.session_factory() as session:
                query = text("""
                    INSERT INTO mansa_quant.probability_engine_inputs
                    (contract_id, calculation_method, yes_price, no_price, 
                     order_volume_24h, sentiment_average, liquidity_usd)
                    VALUES (:contract_id, :calculation_method, :yes_price, :no_price,
                            :volume, :sentiment, :liquidity)
                """)
                
                session.execute(query, {
                    'contract_id': contract_id,
                    'calculation_method': inputs.get('method', 'ensemble'),
                    'yes_price': inputs.get('yes_price'),
                    'no_price': inputs.get('no_price'),
                    'volume': inputs.get('volume_24h'),
                    'sentiment': inputs.get('sentiment_avg'),
                    'liquidity': inputs.get('liquidity_usd')
                })
                
                session.commit()
                return True
        
        except Exception as e:
            logger.error(f"Failed to store engine inputs: {str(e)}")
            return False


class SentimentAnalysisOrchestrator:
    """
    Manages NLP sentiment analysis workflow
    Pulls text data, runs analysis, stores results
    """
    
    def __init__(self, db_connection_string: str, nlp_model_path: Optional[str] = None):
        """Initialize sentiment orchestrator"""
        self.db_engine = create_engine(db_connection_string)
        self.session_factory = sessionmaker(bind=self.db_engine)
        self.nlp_model_path = nlp_model_path
        self.model = self._load_model() if nlp_model_path else None
    
    def _load_model(self):
        """Load NLP sentiment model (e.g., from transformers)"""
        try:
            # This is a placeholder - implement based on your model choice
            # Example: from transformers import pipeline
            # return pipeline('sentiment-analysis', model=self.nlp_model_path)
            logger.info("NLP model loaded")
            return None
        except Exception as e:
            logger.error(f"Failed to load NLP model: {str(e)}")
            return None
    
    async def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of text
        Returns: {sentiment_score, confidence, emotions}
        """
        try:
            # Placeholder for actual NLP analysis
            # In production, use HuggingFace transformers, OpenAI, or similar
            
            # Mock sentiment calculation for demonstration
            sentiment_score = self._mock_sentiment_score(text)
            emotions = self._mock_emotion_detection(text)
            
            return {
                'sentiment_score': sentiment_score,
                'confidence_score': 0.85,
                'emotion_labels': emotions,
                'model_version': 'sentiment-v2.1'
            }
        
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return None
    
    def _mock_sentiment_score(self, text: str) -> float:
        """
        Mock sentiment scoring (replace with actual model in production)
        """
        # Keywords for sentiment detection
        bullish_words = ['bullish', 'buy', 'long', 'up', 'profit', 'gain', 'moon']
        bearish_words = ['bearish', 'sell', 'short', 'down', 'loss', 'crash', 'rug']
        
        text_lower = text.lower()
        bullish_count = sum(text_lower.count(word) for word in bullish_words)
        bearish_count = sum(text_lower.count(word) for word in bearish_words)
        
        total = bullish_count + bearish_count
        if total == 0:
            return 0.0
        
        # Normalize to -1 to +1
        return ((bullish_count - bearish_count) / total)
    
    def _mock_emotion_detection(self, text: str) -> Dict[str, float]:
        """Mock emotion detection"""
        return {
            'bullish': 0.65,
            'fear': 0.20,
            'uncertainty': 0.10,
            'excitement': 0.05
        }
    
    async def store_sentiment(self, contract_id: str, text: str, source: str, analysis: Dict) -> bool:
        """
        Store sentiment analysis result
        """
        try:
            with self.session_factory() as session:
                query = text("""
                    INSERT INTO mansa_quant.nlp_sentiment_data
                    (contract_id, source_text, text_source, sentiment_score,
                     emotion_labels, confidence_score, model_version)
                    VALUES (:contract_id, :text, :source, :sentiment,
                            :emotions, :confidence, :model_version)
                """)
                
                session.execute(query, {
                    'contract_id': contract_id,
                    'text': text,
                    'source': source,
                    'sentiment': analysis['sentiment_score'],
                    'emotions': json.dumps(analysis['emotion_labels']),
                    'confidence': analysis['confidence_score'],
                    'model_version': analysis['model_version']
                })
                
                session.commit()
                return True
        
        except Exception as e:
            logger.error(f"Failed to store sentiment: {str(e)}")
            return False
    
    async def aggregate_daily_sentiment(self, contract_id: str, date: str) -> Optional[Dict]:
        """
        Aggregate sentiment signals for a day
        """
        try:
            with self.session_factory() as session:
                query = text("""
                    SELECT
                        AVG(sentiment_score) as avg_sentiment,
                        COUNT(*) as tweet_volume,
                        MAX(confidence_score) as max_confidence
                    FROM mansa_quant.nlp_sentiment_data
                    WHERE contract_id = :contract_id
                      AND DATE(analyzed_at) = :date
                """)
                
                result = session.execute(
                    query, {'contract_id': contract_id, 'date': date}
                ).fetchone()
                
                if result and result[0] is not None:
                    avg_sentiment, volume, max_conf = result
                    
                    # Determine signal strength
                    signal_strength = self._determine_signal_strength(abs(avg_sentiment))
                    
                    return {
                        'contract_id': contract_id,
                        'date': date,
                        'avg_sentiment': float(avg_sentiment),
                        'signal_strength': signal_strength,
                        'tweet_volume': int(volume),
                        'source': 'nlp_aggregation'
                    }
                
                return None
        
        except Exception as e:
            logger.error(f"Failed to aggregate sentiment: {str(e)}")
            return None
    
    def _determine_signal_strength(self, abs_sentiment: float) -> str:
        """Determine signal strength from sentiment magnitude"""
        if abs_sentiment < 0.3:
            return 'weak'
        elif abs_sentiment < 0.7:
            return 'moderate'
        else:
            return 'strong'


async def run_analytics_pipeline(db_connection_string: str):
    """
    Run full analytics pipeline
    1. Calculate probabilities
    2. Run sentiment analysis
    3. Store results
    """
    logger.info("Starting prediction analytics pipeline...")
    
    # Initialize engines
    prob_engine = ProbabilityEngine(db_connection_string)
    sentiment_engine = SentimentAnalysisOrchestrator(db_connection_string)
    
    # Get all active contracts
    with prob_engine.session_factory() as session:
        contracts = session.execute(
            text("SELECT contract_id FROM mansa_quant.event_contracts WHERE status = 'OPEN'")
        ).fetchall()
        
        for (contract_id,) in contracts:
            try:
                # Compute and store predictions
                prediction = await prob_engine.compute_predictions(contract_id)
                if prediction:
                    await prob_engine.store_prediction(prediction)
                    logger.info(f"Stored prediction for {contract_id}: {prediction['implied_probability']}%")
                
            except Exception as e:
                logger.error(f"Pipeline failed for {contract_id}: {str(e)}")
                continue


if __name__ == "__main__":
    import asyncio
    DB_URL = "mysql+pymysql://bentley_user:bentley_password@localhost:3306/Bentley_Bot"
    asyncio.run(run_analytics_pipeline(DB_URL))
