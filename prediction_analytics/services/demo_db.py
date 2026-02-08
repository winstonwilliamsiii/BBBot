"""Simplified mysql.connector-based DB layer for Demo_Bots testing."""
import mysql.connector
from prediction_analytics.config_dual import DemoConfig

def get_connection():
    """Create a mysql.connector connection to Demo_Bots."""
    return mysql.connector.connect(
        host=DemoConfig.MYSQL_HOST,
        port=DemoConfig.MYSQL_PORT,
        user=DemoConfig.MYSQL_USER,
        password=DemoConfig.MYSQL_PASSWORD,
        database=DemoConfig.MYSQL_DB
    )

def insert_probability(contract_id, source, prob, confidence, rationale):
    """Insert prediction probability into Demo_Bots database."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO prediction_probabilities
        (contract_id, source, implied_probability, confidence_score, rationale)
        VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(query, (contract_id, source, prob, confidence, rationale))
    conn.commit()
    cursor.close()
    conn.close()

def insert_sentiment(contract_id, score, strength, source):
    """Insert sentiment signal into Demo_Bots database."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO sentiment_signals
        (contract_id, sentiment_score, signal_strength, source)
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(query, (contract_id, score, strength, source))
    conn.commit()
    cursor.close()
    conn.close()
