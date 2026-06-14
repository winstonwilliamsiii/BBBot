"""
DATABASE MERGE ANALYSIS & RECOMMENDATION
Port 3307 Schema Consolidation
=========================================

Current State:
--------------
Port 3307 has 4 databases:
1. mansa_bot    - 44 Airflow tables (metadata/orchestration)
2. bbbot1       - 6 empty stock data tables  
3. mlflow_db    - MLflow experiment tracking
4. mansa_quant  - 4 trading/quant tables (newly created)

Question: Should mansa_bot be merged with bentley_bot_dev?
-----------------------------------------------------------

RECOMMENDATION: NO - Keep Separate
===================================

Reasons:
--------

1. **Different Purposes**
   - mansa_bot = Airflow orchestration (DAGs, task instances, logs)
   - bbbot1 = Raw stock/market data storage
   - mansa_quant = Trading signals & portfolio tracking
   - bentley_bot_dev = Would be another isolated dev environment

2. **Airflow Best Practice**
   Airflow requires its own dedicated metadata database. Mixing it with
   application data can cause:
   - Version upgrade conflicts
   - Backup/restore complications
   - Performance degradation

3. **Clean Separation of Concerns**
   Current structure is optimal:
   
   Port 3306 (Native MySQL):
   └── mansa_bot (Airflow metadata)
   
   Port 3307 (Docker MySQL):
   ├── bbbot1 (Stock prices, fundamentals, sentiment)
   ├── mlflow_db (ML experiment tracking)
   └── mansa_quant (Trading signals, positions, history)

4. **No Duplication**
   Each database has unique tables serving different purposes.
   No merge is needed.


RECOMMENDED ACTIONS
===================

✅ 1. Keep Current Structure
   - mansa_bot on port 3306 for Airflow
   - bbbot1, mlflow_db, mansa_quant on port 3307 for app data

✅ 2. Populate Empty Tables
   Run these to add data to bbbot1:
   
   # Stock prices from yfinance
   python bbbot1_pipeline/ingest_yfinance.py
   
   # Fundamentals
   python bbbot1_pipeline/ingest_fundamentals.py
   
   # Sentiment data
   python bbbot1_pipeline/ingest_sentiment.py

✅ 3. Update Application Code
   Ensure apps use correct database:
   - Airflow DAGs → MYSQL_DATABASE=mansa_bot (port 3306)
   - Stock data → BBBOT1_MYSQL_DATABASE=bbbot1 (port 3307)
   - Trading signals → QUANT_MYSQL_DATABASE=mansa_quant (port 3307)
   - MLflow → MLFLOW_MYSQL_DATABASE=mlflow_db (port 3307)

✅ 4. MySQL Workbench Configuration
   To see mansa_quant in Workbench:
   
   1. Open MySQL Workbench
   2. Click "+" to add new connection
   3. Connection name: "Docker MySQL (3307)"
   4. Hostname: 127.0.0.1
   5. Port: 3307
   6. Username: root
   7. Password: root
   8. Test Connection
   9. Refresh schemas panel (F5)
   
   You should now see:
   - bbbot1
   - mlflow_db
   - mansa_quant ✓ (now visible!)


DATABASE SCHEMA SUMMARY
========================

mansa_bot (Port 3306) - Airflow Metadata
-----------------------------------------
44 tables for:
- DAG definitions & runs
- Task instances & logs  
- Users & permissions
- Job scheduling

bbbot1 (Port 3307) - Market Data
---------------------------------
- fundamentals_raw
- news_articles
- sentiment_msgs
- stock_fundamentals
- stock_prices_yf
- technicals_raw

mlflow_db (Port 3307) - ML Tracking
------------------------------------
- experiments
- runs
- metrics
- params
- artifacts

mansa_quant (Port 3307) - Trading ✓ NEW
----------------------------------------
- trading_signals (BUY/SELL/HOLD with RSI, MACD)
- portfolio_positions (holdings by broker)
- trade_history (executed orders)
- ml_predictions (model forecasts)


CONCLUSION
==========
Do NOT merge databases. Current architecture is correct and follows
best practices for multi-purpose data storage.

Focus on:
1. ✓ mansa_quant is now created and visible
2. Populate bbbot1 with stock data
3. Configure MySQL Workbench connection to port 3307
4. Run Airflow DAGs to orchestrate data pipelines
"""

if __name__ == "__main__":
    print(__doc__)
    
    # Quick verification
    import mysql.connector
    
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            port=3307,
            user='root',
            password='root',
            database='mansa_quant'
        )
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [t[0] for t in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("✓ VERIFICATION: mansa_quant is accessible")
        print("="*60)
        print(f"Tables: {', '.join(tables)}")
        print("\nYou can now see this in MySQL Workbench!")
        
    except Exception as e:
        print(f"\n⚠️  Connection test failed: {e}")
