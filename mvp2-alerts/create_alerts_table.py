"""
Create alerts_log table in MySQL database
Run this to set up the TradingView alerts logging table
"""

import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to bbbot1 database (operational database)
conn = mysql.connector.connect(
    host=os.getenv('BBBOT1_MYSQL_HOST', '127.0.0.1'),
    port=int(os.getenv('BBBOT1_MYSQL_PORT', 3306)),
    user=os.getenv('BBBOT1_MYSQL_USER', 'root'),
    password=os.getenv('BBBOT1_MYSQL_PASSWORD', 'root'),
    database=os.getenv('BBBOT1_MYSQL_DATABASE', 'bbbot1')
)

cursor = conn.cursor()

# Create table
create_table_sql = """
CREATE TABLE IF NOT EXISTS alerts_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  symbol VARCHAR(20) NOT NULL,
  change_percent DECIMAL(6,2) NOT NULL,
  price DECIMAL(12,2),
  currency VARCHAR(10) DEFAULT 'USD',
  alert_type VARCHAR(50) NOT NULL,
  discord_delivered BOOLEAN DEFAULT FALSE,
  discord_error TEXT,
  sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_symbol (symbol),
  INDEX idx_sent_at (sent_at),
  INDEX idx_alert_type (alert_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

try:
    cursor.execute(create_table_sql)
    conn.commit()
    print("✓ Table 'alerts_log' created successfully")
    
    # Show table structure
    cursor.execute("DESCRIBE alerts_log")
    print("\nTable structure:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
        
except mysql.connector.Error as err:
    print(f"✗ Error: {err}")
finally:
    cursor.close()
    conn.close()
