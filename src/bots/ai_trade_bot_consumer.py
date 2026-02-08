"""
AI Trade Bot Consumer
Queries prediction_probabilities + sentiment_signals
Routes trades accordingly and logs outcomes
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class AITradeBot:
    """
    Passive income bot that consumes prediction + sentiment data
    Makes trading decisions based on confidence thresholds
    """
    
    def __init__(
        self,
        bot_id: str,
        db_connection_string: str,
        confidence_threshold: float = 0.75,
        min_sentiment_score: float = 0.3,
        max_position_size: float = 100.00,
        paper_trading: bool = True
    ):
        """Initialize AI Trade Bot"""
        self.bot_id = bot_id
        self.db_engine = create_engine(db_connection_string)
        self.session_factory = sessionmaker(bind=self.db_engine)
        
        # Trading parameters
        self.confidence_threshold = confidence_threshold
        self.min_sentiment_score = min_sentiment_score
        self.max_position_size = max_position_size
        self.paper_trading = paper_trading
        
        logger.info(f"Initialized {bot_id} - Paper Trading: {paper_trading}")
    
    async def fetch_trading_signals(self) -> List[Dict]:
        """
        Fetch actionable trading signals from predictions + sentiment
        """
        with self.session_factory() as session:
            query = text("""
                SELECT 
                    pp.id as prediction_id,
                    pp.contract_id,
                    pp.implied_probability,
                    pp.confidence_score,
                    pp.rationale,
                    ss.id as sentiment_id,
                    ss.sentiment_score,
                    ss.signal_strength,
                    ec.contract_name,
                    ec.source,
                    ec.yes_price,
                    ec.no_price,
                    ec.volume_24h,
                    ec.liquidity_usd,
                    -- Calculate combined signal score
                    (pp.confidence_score * 0.6 + ABS(ss.sentiment_score) * 0.4) as combined_score
                FROM mansa_quant.prediction_probabilities pp
                JOIN mansa_quant.event_contracts ec ON pp.contract_id = ec.contract_id
                LEFT JOIN mansa_quant.sentiment_signals ss ON pp.contract_id = ss.contract_id
                    AND ss.created_at > NOW() - INTERVAL 2 HOUR
                WHERE ec.status = 'OPEN'
                    AND pp.confidence_score >= :confidence_threshold
                    AND pp.created_at > NOW() - INTERVAL 2 HOUR
                    AND (ss.sentiment_score IS NULL OR ABS(ss.sentiment_score) >= :min_sentiment)
                    -- Avoid re-trading same contracts
                    AND NOT EXISTS (
                        SELECT 1 FROM mansa_quant.passive_income_logs pil
                        WHERE pil.contract_id = pp.contract_id
                            AND pil.bot_id = :bot_id
                            AND pil.execution_timestamp > NOW() - INTERVAL 24 HOUR
                            AND pil.trade_status IN ('EXECUTED', 'PENDING')
                    )
                ORDER BY combined_score DESC
                LIMIT 10
            """)
            
            result = session.execute(query, {
                'confidence_threshold': self.confidence_threshold,
                'min_sentiment': self.min_sentiment_score,
                'bot_id': self.bot_id
            })
            
            return [dict(row._mapping) for row in result]
    
    def evaluate_trade_action(self, signal: Dict) -> str:
        """
        Determine trade action based on probability + sentiment
        
        Returns: 'BUY', 'SELL', 'HOLD', 'SKIP'
        """
        probability = signal['implied_probability']
        sentiment = signal.get('sentiment_score', 0)
        combined_score = signal['combined_score']
        
        # Strong bullish signal
        if probability > 70 and sentiment > 0.5 and combined_score > 0.8:
            return 'BUY'
        
        # Moderate bullish signal
        elif probability > 60 and sentiment > 0.3 and combined_score > 0.7:
            return 'BUY'
        
        # Strong bearish signal
        elif probability < 30 and sentiment < -0.5 and combined_score > 0.8:
            return 'SELL'
        
        # Moderate bearish signal
        elif probability < 40 and sentiment < -0.3 and combined_score > 0.7:
            return 'SELL'
        
        # Neutral or unclear signal
        else:
            return 'SKIP'
    
    def calculate_position_size(self, signal: Dict) -> float:
        """
        Calculate position size based on confidence and liquidity
        Kelly Criterion-inspired sizing
        """
        confidence = signal['confidence_score']
        liquidity = signal.get('liquidity_usd', 0)
        
        # Base position size as % of max
        base_size = self.max_position_size * confidence
        
        # Reduce size if liquidity is low
        if liquidity < 1000:
            base_size *= 0.5
        elif liquidity < 5000:
            base_size *= 0.75
        
        return round(min(base_size, self.max_position_size), 2)
    
    async def execute_trade(self, signal: Dict, action: str, position_size: float) -> Dict:
        """
        Execute trade on broker (Polymarket, Kalshi, etc.)
        In paper trading mode, simulates execution
        """
        if self.paper_trading:
            # Simulate execution for paper trading
            return {
                'status': 'EXECUTED',
                'execution_timestamp': datetime.utcnow(),
                'entry_price': signal['yes_price'],
                'broker': signal['source'],
                'order_id': f"PAPER_{signal['contract_id']}_{datetime.utcnow().timestamp()}"
            }
        else:
            # Real execution logic here
            # Integrate with Polymarket/Kalshi/Alpaca APIs
            logger.warning("Live trading not implemented - using paper trading")
            return {
                'status': 'FAILED',
                'error': 'Live trading not enabled'
            }
    
    async def log_trade_decision(
        self,
        signal: Dict,
        action: str,
        position_size: float,
        execution_result: Optional[Dict] = None
    ) -> bool:
        """
        Log trade decision to passive_income_logs table
        """
        try:
            with self.session_factory() as session:
                query = text("""
                    INSERT INTO mansa_quant.passive_income_logs
                    (bot_id, contract_id, prediction_id, sentiment_id, trade_action,
                     position_size, entry_price, trade_rationale, implied_probability_at_entry,
                     sentiment_score_at_entry, combined_signal_score, confidence_threshold_met,
                     broker, trade_status, execution_timestamp)
                    VALUES (:bot_id, :contract_id, :prediction_id, :sentiment_id, :action,
                            :position_size, :entry_price, :rationale, :probability,
                            :sentiment, :combined_score, :confidence_met,
                            :broker, :status, :execution_time)
                """)
                
                session.execute(query, {
                    'bot_id': self.bot_id,
                    'contract_id': signal['contract_id'],
                    'prediction_id': signal['prediction_id'],
                    'sentiment_id': signal.get('sentiment_id'),
                    'action': action,
                    'position_size': position_size,
                    'entry_price': execution_result.get('entry_price') if execution_result else signal['yes_price'],
                    'rationale': f"Bot Decision: {action} based on {signal['rationale']}",
                    'probability': signal['implied_probability'],
                    'sentiment': signal.get('sentiment_score'),
                    'combined_score': signal['combined_score'],
                    'confidence_met': True,
                    'broker': signal['source'],
                    'status': execution_result.get('status', 'PENDING') if execution_result else 'PENDING',
                    'execution_time': execution_result.get('execution_timestamp') if execution_result else datetime.utcnow()
                })
                
                session.commit()
                logger.info(f"Logged trade: {action} {signal['contract_id']} - Size: {position_size}")
                return True
        
        except Exception as e:
            logger.error(f"Failed to log trade: {str(e)}")
            return False
    
    async def log_decision_audit(
        self,
        signal: Dict,
        decision_type: str,
        decision_result: str,
        execution_time_ms: int
    ):
        """
        Log detailed decision audit trail
        """
        try:
            with self.session_factory() as session:
                query = text("""
                    INSERT INTO mansa_quant.bot_decision_audit
                    (bot_id, contract_id, decision_type, decision_result,
                     input_data, output_data, execution_time_ms)
                    VALUES (:bot_id, :contract_id, :decision_type, :result,
                            :input_data, :output_data, :exec_time)
                """)
                
                import json
                session.execute(query, {
                    'bot_id': self.bot_id,
                    'contract_id': signal['contract_id'],
                    'decision_type': decision_type,
                    'result': decision_result,
                    'input_data': json.dumps({
                        'probability': float(signal['implied_probability']),
                        'sentiment': float(signal.get('sentiment_score', 0)),
                        'combined_score': float(signal['combined_score'])
                    }),
                    'output_data': json.dumps({
                        'action': decision_result,
                        'threshold_met': True
                    }),
                    'exec_time': execution_time_ms
                })
                
                session.commit()
        
        except Exception as e:
            logger.error(f"Failed to log audit: {str(e)}")
    
    async def run_trading_loop(self):
        """
        Main trading loop - fetch signals, evaluate, execute
        """
        logger.info(f"Starting trading loop for {self.bot_id}")
        
        while True:
            try:
                # Fetch signals
                signals = await self.fetch_trading_signals()
                logger.info(f"Fetched {len(signals)} trading signals")
                
                for signal in signals:
                    start_time = datetime.utcnow()
                    
                    # Evaluate trade action
                    action = self.evaluate_trade_action(signal)
                    
                    if action == 'SKIP':
                        logger.info(f"Skipping {signal['contract_id']} - No clear signal")
                        await self.log_decision_audit(
                            signal, 'TRADE_SIGNAL', 'SKIP', 
                            int((datetime.utcnow() - start_time).total_seconds() * 1000)
                        )
                        continue
                    
                    # Calculate position size
                    position_size = self.calculate_position_size(signal)
                    
                    # Execute trade
                    execution_result = await self.execute_trade(signal, action, position_size)
                    
                    # Log trade
                    await self.log_trade_decision(signal, action, position_size, execution_result)
                    
                    # Audit trail
                    await self.log_decision_audit(
                        signal, 'TRADE_SIGNAL', action,
                        int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    )
                
                # Wait before next iteration (5 minutes)
                await asyncio.sleep(300)
            
            except Exception as e:
                logger.error(f"Trading loop error: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute on error


async def main():
    """Entry point for bot consumer service"""
    import os
    
    # Configuration from environment
    BOT_ID = os.environ.get('BOT_ID', 'passive-income-bot-v1')
    DB_URL = f"mysql+pymysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT', 3306)}/Bentley_Bot"
    
    CONFIDENCE_THRESHOLD = float(os.environ.get('CONFIDENCE_THRESHOLD', 0.75))
    MIN_SENTIMENT_SCORE = float(os.environ.get('MIN_SENTIMENT_SCORE', 0.3))
    MAX_POSITION_SIZE = float(os.environ.get('MAX_POSITION_SIZE', 100.00))
    PAPER_TRADING = os.environ.get('PAPER_TRADING', 'true').lower() == 'true'
    
    # Initialize bot
    bot = AITradeBot(
        bot_id=BOT_ID,
        db_connection_string=DB_URL,
        confidence_threshold=CONFIDENCE_THRESHOLD,
        min_sentiment_score=MIN_SENTIMENT_SCORE,
        max_position_size=MAX_POSITION_SIZE,
        paper_trading=PAPER_TRADING
    )
    
    # Run trading loop
    await bot.run_trading_loop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
