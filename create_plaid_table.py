"""Create missing user_plaid_tokens table"""
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

conn = mysql.connector.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    password=os.getenv('BUDGET_MYSQL_PASSWORD'),
    database='mydb'
)

cursor = conn.cursor()

# Create table directly
create_table_sql = """
CREATE TABLE IF NOT EXISTS user_plaid_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    access_token TEXT NOT NULL COMMENT 'Encrypted Plaid access token',
    item_id VARCHAR(255) NOT NULL,
    institution_id VARCHAR(100),
    institution_name VARCHAR(100),
    last_sync TIMESTAMP NULL,
    sync_cursor VARCHAR(255) COMMENT 'For incremental transaction sync',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_active (user_id, is_active),
    INDEX idx_last_sync (last_sync)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

cursor.execute(create_table_sql)
conn.commit()
print('✅ user_plaid_tokens table created')

# Show tables with 'plaid' in name
cursor.execute("SHOW TABLES LIKE '%plaid%'")
tables = cursor.fetchall()
print(f'\nPlaid-related tables:')
for table in tables:
    print(f'  - {table[0]}')

cursor.close()
conn.close()
