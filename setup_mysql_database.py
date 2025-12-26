"""
Create MySQL Database and Schema
Sets up mansa_bot database with required tables
"""
import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

def create_database_and_schema():
    """Create mansa_bot database and tables"""
    
    print("="*60)
    print("Creating mansa_bot Database")
    print("="*60)
    
    # Connect without database
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', '127.0.0.1'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', 'root')
    )
    
    cursor = conn.cursor()
    
    # Create database
    print("\n📦 Creating database...")
    cursor.execute("CREATE DATABASE IF NOT EXISTS mansa_bot")
    print("✅ Database 'mansa_bot' created")
    
    cursor.execute("USE mansa_bot")
    
    # Create portfolios table
    print("\n📊 Creating 'portfolios' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            portfolio_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            ticker VARCHAR(10) NOT NULL,
            quantity DECIMAL(15,4) NOT NULL DEFAULT 0,
            purchase_price DECIMAL(15,4),
            total_value DECIMAL(15,4),
            current_price DECIMAL(15,4),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_ticker (user_id, ticker),
            INDEX idx_ticker (ticker)
        )
    """)
    print("✅ 'portfolios' table created")
    
    # Create transactions table
    print("\n💰 Creating 'transactions' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            ticker VARCHAR(10) NOT NULL,
            transaction_type ENUM('BUY', 'SELL') NOT NULL,
            quantity DECIMAL(15,4) NOT NULL,
            price DECIMAL(15,4) NOT NULL,
            total_value DECIMAL(15,4) NOT NULL,
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            INDEX idx_user_date (user_id, transaction_date),
            INDEX idx_ticker (ticker)
        )
    """)
    print("✅ 'transactions' table created")
    
    # Insert sample data
    print("\n🧪 Inserting sample portfolio data...")
    
    sample_data = [
        ('demo_user', 'IONQ', 100, 25.50, 2550.00, 28.75),
        ('demo_user', 'QBTS', 150, 12.30, 1845.00, 15.20),
        ('demo_user', 'SOUN', 200, 8.75, 1750.00, 10.50),
        ('demo_user', 'RGTI', 75, 42.00, 3150.00, 45.30),
    ]
    
    cursor.executemany("""
        INSERT INTO portfolios (user_id, ticker, quantity, purchase_price, total_value, current_price)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            quantity = VALUES(quantity),
            purchase_price = VALUES(purchase_price),
            total_value = VALUES(total_value),
            current_price = VALUES(current_price)
    """, sample_data)
    
    print(f"✅ Inserted {len(sample_data)} sample holdings")
    
    # Insert sample transactions
    print("\n📝 Inserting sample transactions...")
    
    sample_transactions = [
        ('demo_user', 'IONQ', 'BUY', 100, 25.50, 2550.00),
        ('demo_user', 'QBTS', 'BUY', 150, 12.30, 1845.00),
        ('demo_user', 'SOUN', 'BUY', 200, 8.75, 1750.00),
        ('demo_user', 'RGTI', 'BUY', 75, 42.00, 3150.00),
    ]
    
    cursor.executemany("""
        INSERT INTO transactions (user_id, ticker, transaction_type, quantity, price, total_value)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, sample_transactions)
    
    print(f"✅ Inserted {len(sample_transactions)} sample transactions")
    
    conn.commit()
    
    # Verify
    print("\n🔍 Verifying data...")
    cursor.execute("SELECT COUNT(*) FROM portfolios")
    portfolio_count = cursor.fetchone()[0]
    print(f"   Portfolios: {portfolio_count} records")
    
    cursor.execute("SELECT COUNT(*) FROM transactions")
    transaction_count = cursor.fetchone()[0]
    print(f"   Transactions: {transaction_count} records")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ Setup Complete!")
    print("="*60)
    print("\nYou can now:")
    print("1. Run: python test_mysql_connection.py")
    print("2. Test portfolio service in Streamlit")
    print("3. Deploy get_portfolio_mysql function to Appwrite")
    print("="*60 + "\n")


if __name__ == "__main__":
    create_database_and_schema()
