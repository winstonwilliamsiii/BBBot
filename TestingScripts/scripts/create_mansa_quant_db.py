"""Create mansa_quant database and tables for quantitative trading"""
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

print("="*70)
print("CREATING MANSA_QUANT DATABASE & TABLES")
print("="*70)

# Connect to MySQL
conn = mysql.connector.connect(
    host='127.0.0.1',
    port=3307,
    user='root',
    password='root'
)
cursor = conn.cursor()

# Create mansa_quant database
print("\n[1/5] Creating mansa_quant database...")
cursor.execute("CREATE DATABASE IF NOT EXISTS mansa_quant")
cursor.execute("USE mansa_quant")
print("   ✓ Database mansa_quant created")

# Create trading signals table
print("\n[2/5] Creating trading_signals table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS trading_signals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    signal_date DATETIME NOT NULL,
    signal_type ENUM('BUY', 'SELL', 'HOLD') NOT NULL,
    price DECIMAL(10, 2),
    rsi_14 DECIMAL(5, 2),
    macd DECIMAL(10, 4),
    macd_signal DECIMAL(10, 4),
    sentiment_score DECIMAL(5, 4),
    confidence DECIMAL(5, 4),
    strategy VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ticker_date (ticker, signal_date),
    INDEX idx_signal_type (signal_type),
    INDEX idx_signal_date (signal_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""")
print("   ✓ trading_signals table created")

# Create portfolio positions table
print("\n[3/5] Creating portfolio_positions table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS portfolio_positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    quantity DECIMAL(15, 6) NOT NULL,
    avg_cost DECIMAL(10, 2) NOT NULL,
    current_price DECIMAL(10, 2),
    market_value DECIMAL(15, 2),
    unrealized_pnl DECIMAL(15, 2),
    broker VARCHAR(50),
    account_id VARCHAR(100),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ticker (ticker),
    INDEX idx_broker (broker)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""")
print("   ✓ portfolio_positions table created")

# Create trade history table
print("\n[4/5] Creating trade_history table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS trade_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    trade_date DATETIME NOT NULL,
    side ENUM('BUY', 'SELL') NOT NULL,
    quantity DECIMAL(15, 6) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(15, 2) NOT NULL,
    commission DECIMAL(10, 2) DEFAULT 0,
    broker VARCHAR(50),
    order_id VARCHAR(100),
    status ENUM('PENDING', 'FILLED', 'CANCELLED', 'REJECTED') DEFAULT 'PENDING',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ticker_date (ticker, trade_date),
    INDEX idx_broker (broker),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""")
print("   ✓ trade_history table created")

# Create model predictions table
print("\n[5/5] Creating ml_predictions table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS ml_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    prediction_date DATETIME NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    predicted_price DECIMAL(10, 2),
    predicted_direction ENUM('UP', 'DOWN', 'NEUTRAL'),
    confidence DECIMAL(5, 4),
    actual_price DECIMAL(10, 2),
    mae DECIMAL(10, 4),
    rmse DECIMAL(10, 4),
    features JSON,
    mlflow_run_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ticker_date (ticker, prediction_date),
    INDEX idx_model (model_name),
    INDEX idx_run_id (mlflow_run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""")
print("   ✓ ml_predictions table created")

# Commit changes
conn.commit()

# Verify tables
cursor.execute("SHOW TABLES")
tables = cursor.fetchall()
print(f"\n✓ Database mansa_quant created with {len(tables)} tables:")
for table in tables:
    print(f"  - {table[0]}")

cursor.close()
conn.close()

print("\n" + "="*70)
print("SUCCESS - mansa_quant database ready for trading!")
print("="*70)
print("""
Next steps:
1. Update .env with:
   QUANT_MYSQL_DATABASE=mansa_quant
   
2. Test connection:
   python -c "import mysql.connector; conn = mysql.connector.connect(host='127.0.0.1', port=3307, user='root', password='root', database='mansa_quant'); print('Connected to mansa_quant!')"
   
3. Populate with test data from ML pipeline
""")
