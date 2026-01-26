"""
Appwrite Function: Prediction Analytics Investor Dashboard
Endpoint: /api/prediction-dashboard
Method: GET, POST
Purpose: Fetch real-time prediction + sentiment data for visualization
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Appwrite SDK
from appwrite.client import Client
from appwrite.services.databases import Databases

# Database connection (MySQL via Railway)
import pymysql
from pymysql.cursors import DictCursor


def setup_mysql_connection():
    """Initialize MySQL connection to Bentley_Bot"""
    return pymysql.connect(
        host=os.environ.get('BENTLEY_DB_HOST', 'localhost'),
        port=int(os.environ.get('BENTLEY_DB_PORT', 3306)),
        user=os.environ.get('BENTLEY_DB_USER', 'bentley_user'),
        password=os.environ.get('BENTLEY_DB_PASSWORD'),
        database='Bentley_Bot',
        charset='utf8mb4',
        cursorclass=DictCursor
    )


def get_top_predictions(limit: int = 10, min_confidence: float = 0.7) -> List[Dict]:
    """
    Fetch top predictions with high confidence scores
    """
    connection = setup_mysql_connection()
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    pp.contract_id,
                    ec.contract_name,
                    ec.source,
                    ec.category,
                    pp.implied_probability,
                    pp.confidence_score,
                    pp.rationale,
                    pp.created_at,
                    ss.sentiment_score,
                    ss.signal_strength
                FROM mansa_quant.prediction_probabilities pp
                JOIN mansa_quant.event_contracts ec ON pp.contract_id = ec.contract_id
                LEFT JOIN mansa_quant.sentiment_signals ss ON pp.contract_id = ss.contract_id
                    AND ss.created_at > NOW() - INTERVAL 24 HOUR
                WHERE pp.confidence_score >= %s
                    AND ec.status = 'OPEN'
                ORDER BY pp.confidence_score DESC, pp.implied_probability DESC
                LIMIT %s
            """
            cursor.execute(query, (min_confidence, limit))
            return cursor.fetchall()
    finally:
        connection.close()


def get_bot_performance(bot_id: str = 'passive-income-bot-v1', days: int = 30) -> Dict:
    """
    Fetch bot performance metrics for investor dashboard
    """
    connection = setup_mysql_connection()
    try:
        with connection.cursor() as cursor:
            # Overall performance
            overall_query = """
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(profit_loss) as total_profit_loss,
                    AVG(profit_loss) as avg_profit_per_trade,
                    AVG(confidence_threshold_met) as avg_confidence_met,
                    MIN(profit_loss) as max_loss,
                    MAX(profit_loss) as max_profit
                FROM mansa_quant.passive_income_logs
                WHERE bot_id = %s
                    AND execution_timestamp > NOW() - INTERVAL %s DAY
                    AND trade_status = 'EXECUTED'
            """
            cursor.execute(overall_query, (bot_id, days))
            overall_stats = cursor.fetchone()
            
            # Daily performance trend
            daily_query = """
                SELECT 
                    DATE(execution_timestamp) as trade_date,
                    COUNT(*) as trades_count,
                    SUM(profit_loss) as daily_profit_loss,
                    AVG(confidence_threshold_met) as avg_confidence
                FROM mansa_quant.passive_income_logs
                WHERE bot_id = %s
                    AND execution_timestamp > NOW() - INTERVAL %s DAY
                    AND trade_status = 'EXECUTED'
                GROUP BY DATE(execution_timestamp)
                ORDER BY trade_date DESC
            """
            cursor.execute(daily_query, (bot_id, days))
            daily_performance = cursor.fetchall()
            
            # Win rate calculation
            total_trades = overall_stats['total_trades'] or 0
            winning_trades = overall_stats['winning_trades'] or 0
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            return {
                'bot_id': bot_id,
                'period_days': days,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': overall_stats['losing_trades'] or 0,
                'win_rate': round(win_rate, 2),
                'total_profit_loss': float(overall_stats['total_profit_loss'] or 0),
                'avg_profit_per_trade': float(overall_stats['avg_profit_per_trade'] or 0),
                'max_profit': float(overall_stats['max_profit'] or 0),
                'max_loss': float(overall_stats['max_loss'] or 0),
                'daily_performance': [
                    {
                        'date': str(day['trade_date']),
                        'trades': day['trades_count'],
                        'profit_loss': float(day['daily_profit_loss']),
                        'avg_confidence': float(day['avg_confidence'] or 0)
                    }
                    for day in daily_performance
                ]
            }
    finally:
        connection.close()


def get_active_signals(limit: int = 20) -> List[Dict]:
    """
    Fetch active trading signals (predictions + sentiment)
    """
    connection = setup_mysql_connection()
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    ec.contract_id,
                    ec.contract_name,
                    ec.source,
                    ec.category,
                    ec.yes_price,
                    ec.volume_24h,
                    pp.implied_probability,
                    pp.confidence_score,
                    ss.sentiment_score,
                    ss.signal_strength,
                    CASE 
                        WHEN pp.implied_probability > 70 AND ss.sentiment_score > 0.5 THEN 'STRONG_BUY'
                        WHEN pp.implied_probability > 60 AND ss.sentiment_score > 0.3 THEN 'BUY'
                        WHEN pp.implied_probability < 40 AND ss.sentiment_score < -0.3 THEN 'SELL'
                        ELSE 'HOLD'
                    END as signal_action,
                    pp.created_at as signal_timestamp
                FROM mansa_quant.event_contracts ec
                JOIN mansa_quant.prediction_probabilities pp ON ec.contract_id = pp.contract_id
                JOIN mansa_quant.sentiment_signals ss ON ec.contract_id = ss.contract_id
                WHERE ec.status = 'OPEN'
                    AND pp.created_at > NOW() - INTERVAL 2 HOUR
                    AND ss.created_at > NOW() - INTERVAL 2 HOUR
                    AND pp.confidence_score >= 0.65
                ORDER BY pp.confidence_score DESC, pp.created_at DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            return cursor.fetchall()
    finally:
        connection.close()


def get_contract_details(contract_id: str) -> Optional[Dict]:
    """
    Get detailed information about a specific contract
    """
    connection = setup_mysql_connection()
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    ec.*,
                    pp.implied_probability,
                    pp.confidence_score,
                    pp.rationale,
                    ss.sentiment_score,
                    ss.signal_strength,
                    (SELECT COUNT(*) FROM mansa_quant.passive_income_logs 
                     WHERE contract_id = ec.contract_id) as bot_trades_count,
                    (SELECT SUM(profit_loss) FROM mansa_quant.passive_income_logs 
                     WHERE contract_id = ec.contract_id AND trade_status = 'EXECUTED') as total_bot_pnl
                FROM mansa_quant.event_contracts ec
                LEFT JOIN mansa_quant.prediction_probabilities pp ON ec.contract_id = pp.contract_id
                LEFT JOIN mansa_quant.sentiment_signals ss ON ec.contract_id = ss.contract_id
                WHERE ec.contract_id = %s
                ORDER BY pp.created_at DESC, ss.created_at DESC
                LIMIT 1
            """
            cursor.execute(query, (contract_id,))
            return cursor.fetchone()
    finally:
        connection.close()


def main(context):
    """
    Appwrite function entry point
    """
    # Parse request
    method = context.req.method
    path = context.req.path
    query_params = context.req.query or {}
    
    # CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # Handle OPTIONS preflight
    if method == 'OPTIONS':
        return context.res.json({}, headers=headers)
    
    try:
        # Route requests
        if path == '/api/prediction-dashboard' and method == 'GET':
            # Main dashboard data
            response_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'top_predictions': get_top_predictions(
                    limit=int(query_params.get('limit', 10)),
                    min_confidence=float(query_params.get('min_confidence', 0.7))
                ),
                'bot_performance': get_bot_performance(
                    bot_id=query_params.get('bot_id', 'passive-income-bot-v1'),
                    days=int(query_params.get('days', 30))
                ),
                'active_signals': get_active_signals(
                    limit=int(query_params.get('signals_limit', 20))
                )
            }
            return context.res.json(response_data, headers=headers)
        
        elif path.startswith('/api/contract/') and method == 'GET':
            # Contract detail endpoint
            contract_id = path.split('/')[-1]
            contract_data = get_contract_details(contract_id)
            
            if contract_data:
                return context.res.json(contract_data, headers=headers)
            else:
                return context.res.json(
                    {'error': 'Contract not found'}, 
                    headers=headers,
                    statusCode=404
                )
        
        else:
            return context.res.json(
                {'error': 'Endpoint not found'}, 
                headers=headers,
                statusCode=404
            )
    
    except Exception as e:
        context.log(f"Error: {str(e)}")
        return context.res.json(
            {'error': 'Internal server error', 'message': str(e)}, 
            headers=headers,
            statusCode=500
        )
