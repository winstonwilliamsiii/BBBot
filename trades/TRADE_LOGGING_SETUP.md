# MySQL Trade Logging Setup

**Status**: ⚠️ **DATABASE TABLE EXISTS BUT NOT IN USE**  
**Priority**: HIGH - Recommended for trade record keeping and analysis  
**Last Updated**: February 15, 2026

---

## 📋 Current Status

### What Exists
✅ MySQL `trades` table is defined in:
- **File**: [`scripts/setup/init_all_databases.sql`](../scripts/setup/init_all_databases.sql)
- **Database**: `mansa_bot`
- **Table**: `trades`

### Table Schema
```sql
CREATE TABLE IF NOT EXISTS trades (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    trade_date DATETIME NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    side ENUM('BUY', 'SELL') NOT NULL,
    entry_price DECIMAL(12,4) NOT NULL,
    exit_price DECIMAL(12,4),
    quantity INT NOT NULL,
    pnl DECIMAL(12,2),
    pnl_percent DECIMAL(8,4),
    fees DECIMAL(10,2) DEFAULT 0,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_trade_date (trade_date),
    INDEX idx_ticker (ticker),
    INDEX idx_strategy (strategy),
    INDEX idx_pnl (pnl)
) ENGINE=InnoDB COMMENT='Trading bot transaction history';
```

### What's Missing
❌ **Not integrated** into production trading scripts:
- No code to INSERT trades after order placement
- No code to UPDATE trades when positions close
- No automated P&L calculation

---

## 🔧 Prerequisites

### 1. MySQL Database Running

Check if MySQL container is running:
```bash
docker ps | Select-String mysql
```

If not running, start it:
```bash
# Using Docker Compose
docker-compose up -d mysql

# Or standalone
docker run -d -p 3306:3306 --name bentley-mysql `
  -e MYSQL_ROOT_PASSWORD=your_password `
  -e MYSQL_DATABASE=mansa_bot `
  mysql:8.0
```

### 2. Database Initialized

```bash
# Run initialization script
docker exec -i bentley-mysql mysql -uroot -pyour_password mansa_bot < scripts/setup/init_all_databases.sql
```

### 3. Python MySQL Library

```bash
# Install MySQL connector
pip install mysql-connector-python
```

Or add to `requirements.txt`:
```
mysql-connector-python==8.2.0
```

---

## 🚀 Implementation Guide

### Step 1: Create Database Helper Module

Create `frontend/utils/trade_logger.py`:

```python
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class TradeLogger:
    """Log trades to MySQL database"""
    
    def __init__(self):
        self.host = os.getenv('MYSQL_HOST', 'localhost')
        self.port = os.getenv('MYSQL_PORT', '3306')
        self.database = os.getenv('MYSQL_DATABASE', 'mansa_bot')
        self.user = os.getenv('MYSQL_USER', 'root')
        self.password = os.getenv('MYSQL_PASSWORD', '')
        self.connection = None
    
    def connect(self):
        """Connect to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            return True
        except Error as e:
            print(f"❌ MySQL connection error: {e}")
            return False
    
    def log_trade_entry(self, ticker, strategy, side, entry_price, quantity, notes=None):
        """
        Log a new trade entry
        
        Args:
            ticker: Stock symbol (e.g., "TURB", "SUPX")
            strategy: Trading strategy name (e.g., "bracket_order", "momentum")
            side: "BUY" or "SELL"
            entry_price: Entry price
            quantity: Number of shares
            notes: Optional notes about the trade
            
        Returns:
            trade_id: ID of inserted trade, or None on failure
        """
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return None
        
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO trades 
                (trade_date, ticker, strategy, side, entry_price, quantity, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                datetime.now(),
                ticker,
                strategy,
                side.upper(),
                entry_price,
                quantity,
                notes
            )
            
            cursor.execute(query, values)
            self.connection.commit()
            trade_id = cursor.lastrowid
            
            print(f"✅ Trade logged to MySQL (ID: {trade_id})")
            return trade_id
            
        except Error as e:
            print(f"❌ Error logging trade: {e}")
            return None
        finally:
            cursor.close()
    
    def update_trade_exit(self, trade_id, exit_price, fees=0):
        """
        Update trade with exit information and calculate P&L
        
        Args:
            trade_id: ID of the trade to update
            exit_price: Exit price
            fees: Trading fees (optional)
        """
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return False
        
        try:
            cursor = self.connection.cursor()
            
            # Get trade details to calculate P&L
            cursor.execute("""
                SELECT entry_price, quantity, side 
                FROM trades 
                WHERE id = %s
            """, (trade_id,))
            
            result = cursor.fetchone()
            if not result:
                print(f"❌ Trade ID {trade_id} not found")
                return False
            
            entry_price, quantity, side = result
            
            # Calculate P&L
            if side == 'BUY':
                pnl = (exit_price - entry_price) * quantity - fees
            else:  # SELL
                pnl = (entry_price - exit_price) * quantity - fees
            
            pnl_percent = (pnl / (entry_price * quantity)) * 100
            
            # Update trade
            query = """
                UPDATE trades 
                SET exit_price = %s, 
                    pnl = %s, 
                    pnl_percent = %s, 
                    fees = %s,
                    updated_at = %s
                WHERE id = %s
            """
            values = (exit_price, pnl, pnl_percent, fees, datetime.now(), trade_id)
            
            cursor.execute(query, values)
            self.connection.commit()
            
            print(f"✅ Trade {trade_id} updated with exit price ${exit_price:.2f}")
            print(f"   P&L: ${pnl:.2f} ({pnl_percent:+.2f}%)")
            return True
            
        except Error as e:
            print(f"❌ Error updating trade: {e}")
            return False
        finally:
            cursor.close()
    
    def get_trade_summary(self, ticker=None, days=30):
        """Get trade summary statistics"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            where_clause = "WHERE trade_date >= DATE_SUB(NOW(), INTERVAL %s DAY)"
            params = [days]
            
            if ticker:
                where_clause += " AND ticker = %s"
                params.append(ticker)
            
            query = f"""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN side = 'BUY' THEN 1 ELSE 0 END) as buy_trades,
                    SUM(CASE WHEN side = 'SELL' THEN 1 ELSE 0 END) as sell_trades,
                    SUM(pnl) as total_pnl,
                    AVG(pnl_percent) as avg_pnl_percent,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades
                FROM trades
                {where_clause}
            """
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            return result
            
        except Error as e:
            print(f"❌ Error getting trade summary: {e}")
            return None
        finally:
            cursor.close()
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ MySQL connection closed")
```

### Step 2: Add Environment Variables

Add to your `.env` file:
```bash
# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=mansa_bot
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
```

### Step 3: Integrate into Trading Scripts

Update `place_turb_supx_orders.py`:

```python
# At the top of the file
from frontend.utils.trade_logger import TradeLogger

# After successful TURB order placement
if turb_order:
    print(f"\n✅ TURB order placed successfully!")
    # ... existing code ...
    
    # ADD THIS: Log trade to MySQL
    try:
        logger = TradeLogger()
        trade_id = logger.log_trade_entry(
            ticker=turb_symbol,
            strategy="bracket_order",
            side="BUY",
            entry_price=turb_entry,
            quantity=turb_qty,
            notes=f"Bracket order: SL=${turb_stop_loss}, TP=${turb_take_profit}"
        )
        if trade_id:
            print(f"   📊 Trade logged to database (ID: {trade_id})")
            # Store trade_id in order metadata for later exit updates
        logger.close()
    except Exception as e:
        print(f"   ⚠️  Database logging failed: {e}")

# For SUPX stop loss and take profit
if stop_order and profit_order:
    try:
        logger = TradeLogger()
        trade_id = logger.log_trade_entry(
            ticker="SUPX",
            strategy="protection_orders",
            side="SELL",
            entry_price=supx_current_price,
            quantity=supx_qty,
            notes=f"Protection: SL=${supx_stop_loss}, TP=${supx_take_profit}"
        )
        if trade_id:
            print(f"   📊 Protection orders logged (ID: {trade_id})")
        logger.close()
    except Exception as e:
        print(f"   ⚠️  Database logging failed: {e}")
```

---

## 📊 Query Trade History

### View Recent Trades
```sql
-- Last 10 trades
SELECT 
    id,
    trade_date,
    ticker,
    side,
    entry_price,
    exit_price,
    quantity,
    pnl,
    pnl_percent,
    strategy
FROM trades
ORDER BY trade_date DESC
LIMIT 10;
```

### Get TURB Trade History
```sql
SELECT * FROM trades WHERE ticker = 'TURB' ORDER BY trade_date DESC;
```

### Calculate Win Rate
```sql
SELECT 
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losses,
    ROUND(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_pct
FROM trades
WHERE exit_price IS NOT NULL;
```

### Monthly P&L Summary
```sql
SELECT 
    DATE_FORMAT(trade_date, '%Y-%m') as month,
    ticker,
    COUNT(*) as trades,
    SUM(pnl) as total_pnl,
    AVG(pnl_percent) as avg_return_pct
FROM trades
WHERE exit_price IS NOT NULL
GROUP BY DATE_FORMAT(trade_date, '%Y-%m'), ticker
ORDER BY month DESC, ticker;
```

---

## 🎯 Benefits of MySQL Logging

1. **Historical Record** - Permanent record of all trades
2. **Performance Analysis** - Calculate win rates, P&L, strategy effectiveness
3. **Compliance** - Meet record-keeping requirements
4. **Audit Trail** - Track all trading activity
5. **Data Analytics** - Export to visualization tools (Tableau, Power BI)
6. **Tax Reporting** - Generate reports for tax filing

---

## 🔍 Troubleshooting

### Can't Connect to MySQL

**Check 1: MySQL is running**
```bash
docker ps | Select-String mysql
```

**Check 2: Test connection**
```python
import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        port=3306,
        database='mansa_bot',
        user='root',
        password='your_password'
    )
    print("✅ Connected to MySQL")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

**Check 3: Verify credentials in `.env`**
```bash
# In PowerShell
$env:MYSQL_HOST
$env:MYSQL_DATABASE
$env:MYSQL_USER
```

### Table Doesn't Exist

```bash
# Re-run initialization script
docker exec -i bentley-mysql mysql -uroot -pYOUR_PASSWORD mansa_bot < scripts/setup/init_all_databases.sql
```

---

## 📝 Next Steps

To fully implement MySQL trade logging:

1. ✅ Ensure MySQL is running and initialized
2. ⚠️ Create `frontend/utils/trade_logger.py` (see code above)
3. ⚠️ Add MySQL credentials to `.env` file
4. ⚠️ Update `place_turb_supx_orders.py` with logging calls
5. ⚠️ Test with paper trading first
6. ✅ Verify trades appear in database

---

## 💡 Future Enhancements

- Automated exit tracking (monitor Alpaca webhooks)
- Real-time P&L dashboard
- Strategy comparison reports
- Risk metrics calculation (Sharpe ratio, max drawdown)
- Export to CSV for tax reporting

---

## 📚 Related Files

- [`scripts/setup/init_all_databases.sql`](../scripts/setup/init_all_databases.sql) - Database schema
- [`place_turb_supx_orders.py`](place_turb_supx_orders.py) - Needs integration
- [`frontend/components/alpaca_connector.py`](../frontend/components/alpaca_connector.py) - Alpaca API client
- [`.env.example`](../.env.example) - Environment variable template
