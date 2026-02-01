#MySQL CONNECTOR PREDICTION ANALYSIS
import mysql.connector
from config import Config

def get_connection():
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

def insert_probability(contract_id, source, prob, confidence, rationale):
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