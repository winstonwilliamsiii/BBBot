#!/usr/bin/env python3
"""
Demo_Bots Dry Run Script - Testing Bot Logic Without APIs
===============================================

Purpose:
  - Dry-run bot trading logic with test data
  - Validate signals generation before staging
  - Log decisions to audit trail
  - No actual trades or API calls

Usage:
  python demo_main.py --portfolio fixtures/demo_portfolio.json
  python demo_main.py --mode backtest --start 2025-01-01 --end 2025-12-31

Author: Bentley Bot System
Date: January 27, 2026
"""

import json
import csv
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import argparse
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# Try to import from project (fallback to stubs if not available)
try:
    from frontend.utils.rbac import RBACManager, UserRole
except ImportError:
    RBACManager = None

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('demo_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """Trading decision types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class DemoPortfolioPosition:
    """Position in demo portfolio"""
    ticker: str
    quantity: int
    entry_price: float
    current_price: float
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def gain_loss(self) -> float:
        return (self.current_price - self.entry_price) * self.quantity
    
    @property
    def gain_loss_pct(self) -> float:
        if self.entry_price == 0:
            return 0
        return ((self.current_price - self.entry_price) / self.entry_price) * 100


@dataclass
class TradingDecision:
    """Represents a trading decision in demo mode"""
    bot_id: str
    ticker: str
    decision_type: DecisionType
    confidence: float
    reason: str
    rsi: Optional[float] = None
    macd: Optional[float] = None
    sentiment_score: Optional[float] = None
    target_price: Optional[float] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class IngestAuditEvent:
    """Data ingestion audit event"""
    connector_type: str
    source_system: str
    record_count: int
    success_flag: bool
    sync_duration_ms: int
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DemoBotAuditLogger:
    """Logs bot decisions and ingestion events to files for demo mode"""
    
    def __init__(self, log_dir: str = "demo_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.decisions_log = self.log_dir / f"bot_decisions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.ingestion_log = self.log_dir / f"ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        logger.info(f"Audit logs will be saved to {self.log_dir}/")
    
    def log_trading_decision(self, decision: TradingDecision) -> None:
        """Log a trading decision"""
        with open(self.decisions_log, 'a') as f:
            decision_dict = {
                'bot_id': decision.bot_id,
                'ticker': decision.ticker,
                'decision_type': decision.decision_type.value,
                'confidence': decision.confidence,
                'reason': decision.reason,
                'rsi': decision.rsi,
                'macd': decision.macd,
                'sentiment_score': decision.sentiment_score,
                'target_price': decision.target_price,
                'timestamp': decision.timestamp.isoformat()
            }
            f.write(json.dumps(decision_dict) + '\n')
        
        logger.info(f"Decision logged: {decision.ticker} {decision.decision_type.value} "
                   f"(confidence: {decision.confidence:.2f})")
    
    def log_ingestion_event(self, event: IngestAuditEvent) -> None:
        """Log a data ingestion event"""
        with open(self.ingestion_log, 'a') as f:
            event_dict = {
                'connector_type': event.connector_type,
                'source_system': event.source_system,
                'record_count': event.record_count,
                'success_flag': event.success_flag,
                'sync_duration_ms': event.sync_duration_ms,
                'error_message': event.error_message,
                'timestamp': event.timestamp.isoformat()
            }
            f.write(json.dumps(event_dict) + '\n')
        
        status = "SUCCESS" if event.success_flag else "FAILED"
        logger.info(f"Ingestion logged: {event.connector_type} - {status} "
                   f"({event.record_count} records in {event.sync_duration_ms}ms)")


class DemoTradingBot:
    """Demo trading bot for dry-run testing"""
    
    def __init__(self, bot_id: str = "demo_bot", audit_logger: Optional[DemoBotAuditLogger] = None):
        self.bot_id = bot_id
        self.audit_logger = audit_logger or DemoBotAuditLogger()
        self.portfolio: Dict[str, DemoPortfolioPosition] = {}
        self.decisions: List[TradingDecision] = []
        
        logger.info(f"Initialized {bot_id}")
    
    def load_demo_portfolio(self, portfolio_data: Dict[str, Any]) -> None:
        """Load demo portfolio from dict"""
        start_time = datetime.now()
        
        try:
            for ticker, data in portfolio_data.items():
                self.portfolio[ticker] = DemoPortfolioPosition(
                    ticker=ticker,
                    quantity=int(data.get('quantity', 0)),
                    entry_price=float(data.get('entry_price', 0)),
                    current_price=float(data.get('current_price', 0))
                )
            
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Log ingestion event
            self.audit_logger.log_ingestion_event(IngestAuditEvent(
                connector_type="demo_portfolio",
                source_system="fixture",
                record_count=len(self.portfolio),
                success_flag=True,
                sync_duration_ms=elapsed_ms
            ))
            
            logger.info(f"Loaded {len(self.portfolio)} positions for demo portfolio")
            
        except Exception as e:
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.audit_logger.log_ingestion_event(IngestAuditEvent(
                connector_type="demo_portfolio",
                source_system="fixture",
                record_count=0,
                success_flag=False,
                sync_duration_ms=elapsed_ms,
                error_message=str(e)
            ))
            logger.error(f"Failed to load portfolio: {e}")
            raise
    
    def calculate_technical_indicators(self, ticker: str, prices: List[float]) -> Dict[str, float]:
        """Calculate RSI and MACD indicators (simplified demo version)"""
        if len(prices) < 14:
            return {"rsi": 50.0, "macd": 0.0}
        
        # Simplified RSI (0-100)
        gains = sum(max(0, prices[i] - prices[i-1]) for i in range(1, len(prices)))
        losses = sum(max(0, prices[i-1] - prices[i]) for i in range(1, len(prices)))
        
        if losses == 0:
            rsi = 100.0
        else:
            rs = gains / losses
            rsi = 100 - (100 / (1 + rs))
        
        # Simplified MACD
        ema_12 = sum(prices[-12:]) / 12 if len(prices) >= 12 else prices[-1]
        ema_26 = sum(prices[-26:]) / 26 if len(prices) >= 26 else prices[-1]
        macd = ema_12 - ema_26
        
        return {"rsi": rsi, "macd": macd}
    
    def generate_trading_signal(self, ticker: str, sentiment_score: float = 0.5) -> Optional[TradingDecision]:
        """Generate trading signal based on indicators (demo logic)"""
        if ticker not in self.portfolio:
            return None
        
        position = self.portfolio[ticker]
        prices = [position.entry_price * (1 + i * 0.01) for i in range(-10, 1)]
        indicators = self.calculate_technical_indicators(ticker, prices)
        
        rsi = indicators['rsi']
        macd = indicators['macd']
        
        # Demo trading logic
        confidence = 0.0
        decision_type = DecisionType.HOLD
        reason = "Monitoring"
        target_price = None
        
        # RSI-based signals
        if rsi < 30:  # Oversold
            decision_type = DecisionType.BUY
            confidence = 0.7
            reason = f"RSI oversold ({rsi:.1f})"
            target_price = position.current_price * 1.05
        elif rsi > 70:  # Overbought
            decision_type = DecisionType.SELL
            confidence = 0.6
            reason = f"RSI overbought ({rsi:.1f})"
            target_price = position.current_price * 0.95
        
        # MACD confirmation
        if macd > 0 and decision_type == DecisionType.BUY:
            confidence = min(0.9, confidence + 0.1)
            reason += " + MACD positive"
        elif macd < 0 and decision_type == DecisionType.SELL:
            confidence = min(0.9, confidence + 0.1)
            reason += " + MACD negative"
        
        # Sentiment adjustment
        if sentiment_score > 0.6 and decision_type != DecisionType.SELL:
            confidence += 0.05
            reason += f" + Positive sentiment ({sentiment_score:.2f})"
        elif sentiment_score < 0.4 and decision_type != DecisionType.BUY:
            confidence += 0.05
            reason += f" + Negative sentiment ({sentiment_score:.2f})"
        
        # Cap confidence at 0.95 (never 100% in demo)
        confidence = min(0.95, max(0.0, confidence))
        
        decision = TradingDecision(
            bot_id=self.bot_id,
            ticker=ticker,
            decision_type=decision_type,
            confidence=confidence,
            reason=reason,
            rsi=rsi,
            macd=macd,
            sentiment_score=sentiment_score,
            target_price=target_price
        )
        
        return decision
    
    def run_analysis(self, sentiment_data: Optional[Dict[str, float]] = None) -> List[TradingDecision]:
        """Run bot analysis on all positions"""
        self.decisions = []
        sentiment_data = sentiment_data or {}
        
        logger.info(f"Running demo bot analysis on {len(self.portfolio)} positions")
        
        for ticker in self.portfolio:
            sentiment = sentiment_data.get(ticker, 0.5)
            decision = self.generate_trading_signal(ticker, sentiment)
            
            if decision:
                self.decisions.append(decision)
                self.audit_logger.log_trading_decision(decision)
        
        logger.info(f"Analysis complete. Generated {len(self.decisions)} decisions")
        return self.decisions
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        total_value = sum(p.market_value for p in self.portfolio.values())
        total_gain_loss = sum(p.gain_loss for p in self.portfolio.values())
        total_positions = len(self.portfolio)
        
        return {
            "total_positions": total_positions,
            "total_market_value": total_value,
            "total_gain_loss": total_gain_loss,
            "total_gain_loss_pct": (total_gain_loss / (total_value - total_gain_loss) * 100) if (total_value - total_gain_loss) != 0 else 0,
            "positions": [
                {
                    "ticker": p.ticker,
                    "quantity": p.quantity,
                    "market_value": p.market_value,
                    "gain_loss": p.gain_loss,
                    "gain_loss_pct": p.gain_loss_pct
                }
                for p in self.portfolio.values()
            ]
        }
    
    def get_decisions_summary(self) -> Dict[str, Any]:
        """Get decisions summary"""
        buy_signals = sum(1 for d in self.decisions if d.decision_type == DecisionType.BUY)
        sell_signals = sum(1 for d in self.decisions if d.decision_type == DecisionType.SELL)
        hold_signals = sum(1 for d in self.decisions if d.decision_type == DecisionType.HOLD)
        avg_confidence = sum(d.confidence for d in self.decisions) / len(self.decisions) if self.decisions else 0
        
        return {
            "total_decisions": len(self.decisions),
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "hold_signals": hold_signals,
            "avg_confidence": avg_confidence,
            "decisions": [
                {
                    "ticker": d.ticker,
                    "decision": d.decision_type.value,
                    "confidence": d.confidence,
                    "reason": d.reason,
                    "timestamp": d.timestamp.isoformat()
                }
                for d in self.decisions
            ]
        }


def load_demo_portfolio_from_file(filepath: str) -> Dict[str, Any]:
    """Load demo portfolio from JSON or CSV file"""
    filepath = Path(filepath)
    
    if filepath.suffix.lower() == '.json':
        with open(filepath) as f:
            return json.load(f)
    elif filepath.suffix.lower() in ['.csv', '.txt']:
        data = {}
        with open(filepath) as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row.get('ticker') or row.get('Ticker')
                data[ticker] = {
                    'quantity': int(row.get('quantity', 0) or row.get('Quantity', 0)),
                    'entry_price': float(row.get('entry_price', 0) or row.get('Entry Price', 0)),
                    'current_price': float(row.get('current_price', 0) or row.get('Current Price', 0))
                }
        return data
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")


def create_demo_portfolio() -> Dict[str, Any]:
    """Create default demo portfolio for testing"""
    return {
        "AAPL": {
            "quantity": 100,
            "entry_price": 150.00,
            "current_price": 155.25
        },
        "GOOGL": {
            "quantity": 50,
            "entry_price": 140.00,
            "current_price": 142.50
        },
        "TSLA": {
            "quantity": 25,
            "entry_price": 250.00,
            "current_price": 245.75
        },
        "MSFT": {
            "quantity": 75,
            "entry_price": 380.00,
            "current_price": 385.50
        }
    }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Demo Bot Dry-Run Script - Test trading logic without APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default demo portfolio
  python demo_main.py
  
  # Run with custom portfolio file
  python demo_main.py --portfolio my_portfolio.json
  
  # Run with sentiment analysis
  python demo_main.py --sentiment fixtures/sentiment.json
  
  # Run backtest mode (future)
  python demo_main.py --mode backtest --start 2025-01-01 --end 2025-12-31
        """
    )
    
    parser.add_argument('--portfolio', type=str, default=None,
                       help='Path to portfolio file (JSON or CSV)')
    parser.add_argument('--sentiment', type=str, default=None,
                       help='Path to sentiment data file (JSON)')
    parser.add_argument('--output', type=str, default='demo_results.json',
                       help='Output file for results')
    parser.add_argument('--mode', type=str, choices=['demo', 'backtest'], default='demo',
                       help='Run mode (demo=live, backtest=historical)')
    parser.add_argument('--start', type=str, default=None,
                       help='Start date for backtest (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default=None,
                       help='End date for backtest (YYYY-MM-DD)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("=" * 60)
    logger.info("BENTLEY BOT - DEMO MODE DRY-RUN")
    logger.info("=" * 60)
    
    try:
        # Initialize bot
        audit_logger = DemoBotAuditLogger()
        bot = DemoTradingBot(bot_id="demo_bot", audit_logger=audit_logger)
        
        # Load portfolio
        if args.portfolio:
            logger.info(f"Loading portfolio from {args.portfolio}")
            portfolio_data = load_demo_portfolio_from_file(args.portfolio)
        else:
            logger.info("Using default demo portfolio")
            portfolio_data = create_demo_portfolio()
        
        bot.load_demo_portfolio(portfolio_data)
        
        # Load sentiment data if provided
        sentiment_data = {}
        if args.sentiment:
            logger.info(f"Loading sentiment data from {args.sentiment}")
            with open(args.sentiment) as f:
                sentiment_data = json.load(f)
        
        # Run analysis
        logger.info("Running bot analysis...")
        decisions = bot.run_analysis(sentiment_data)
        
        # Get summaries
        portfolio_summary = bot.get_portfolio_summary()
        decisions_summary = bot.get_decisions_summary()
        
        # Prepare results
        results = {
            "mode": args.mode,
            "timestamp": datetime.now().isoformat(),
            "bot_id": bot.bot_id,
            "portfolio_summary": portfolio_summary,
            "decisions_summary": decisions_summary,
            "audit_logs": {
                "decisions_log": str(audit_logger.decisions_log),
                "ingestion_log": str(audit_logger.ingestion_log)
            }
        }
        
        # Save results
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {args.output}")
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("PORTFOLIO SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Positions: {portfolio_summary['total_positions']}")
        logger.info(f"Total Market Value: ${portfolio_summary['total_market_value']:,.2f}")
        logger.info(f"Total Gain/Loss: ${portfolio_summary['total_gain_loss']:,.2f} "
                   f"({portfolio_summary['total_gain_loss_pct']:.2f}%)")
        
        logger.info("\n" + "=" * 60)
        logger.info("DECISIONS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Decisions: {decisions_summary['total_decisions']}")
        logger.info(f"BUY Signals: {decisions_summary['buy_signals']}")
        logger.info(f"SELL Signals: {decisions_summary['sell_signals']}")
        logger.info(f"HOLD Signals: {decisions_summary['hold_signals']}")
        logger.info(f"Average Confidence: {decisions_summary['avg_confidence']:.2f}")
        
        logger.info("\n" + "=" * 60)
        logger.info("DEMO RUN COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Audit logs saved to: demo_logs/")
        logger.info(f"Results saved to: {args.output}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Demo run failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
