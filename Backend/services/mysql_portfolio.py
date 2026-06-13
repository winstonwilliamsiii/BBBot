"""
MySQL Portfolio Service - Query wrapper for portfolio data
Connects to MySQL database for portfolio holdings and transactions
"""
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# MySQL Configuration from .env (Docker container on port 3307)
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
    'port': int(os.getenv('MYSQL_PORT', 3307)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'root'),
    'database': os.getenv('MYSQL_DATABASE', 'mansa_bot')
}

def get_mysql_connection():
    """Create MySQL database connection"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"MySQL Connection Error: {e}")
        return None


def get_user_portfolio(user_id: str):
    """
    Get user's portfolio holdings from MySQL
    
    Args:
        user_id: User identifier
        
    Returns:
        list: Portfolio holdings with ticker, quantity, cost_basis
    """
    conn = get_mysql_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Query portfolio table
        query = """
        SELECT 
            ticker,
            SUM(quantity) as total_quantity,
            AVG(purchase_price) as avg_cost_basis,
            SUM(total_value) as total_invested
        FROM portfolios
        WHERE user_id = %s
        GROUP BY ticker
        HAVING total_quantity > 0
        """
        
        cursor.execute(query, (user_id,))
        holdings = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {"holdings": holdings, "user_id": user_id}
        
    except mysql.connector.Error as e:
        if conn:
            conn.close()
        return {"error": f"Query failed: {str(e)}"}


def get_user_transactions(user_id: str, limit: int = 100):
    """
    Get user's transaction history from MySQL
    
    Args:
        user_id: User identifier
        limit: Maximum number of transactions
        
    Returns:
        list: Transaction records
    """
    conn = get_mysql_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT 
            transaction_id,
            ticker,
            transaction_type,
            quantity,
            price,
            total_value,
            transaction_date
        FROM transactions
        WHERE user_id = %s
        ORDER BY transaction_date DESC
        LIMIT %s
        """
        
        cursor.execute(query, (user_id, limit))
        transactions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {"transactions": transactions, "user_id": user_id}
        
    except mysql.connector.Error as e:
        if conn:
            conn.close()
        return {"error": f"Query failed: {str(e)}"}


def get_portfolio_summary(user_id: str):
    """
    Get portfolio summary statistics
    
    Args:
        user_id: User identifier
        
    Returns:
        dict: Portfolio metrics (total value, cost basis, P&L)
    """
    conn = get_mysql_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT 
            COUNT(DISTINCT ticker) as total_positions,
            SUM(total_value) as total_invested,
            SUM(quantity * current_price) as current_value,
            SUM(quantity * current_price) - SUM(total_value) as unrealized_pnl
        FROM portfolios
        WHERE user_id = %s
        """
        
        cursor.execute(query, (user_id,))
        summary = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "summary": summary,
            "user_id": user_id
        }
        
    except mysql.connector.Error as e:
        if conn:
            conn.close()
        return {"error": f"Query failed: {str(e)}"}
