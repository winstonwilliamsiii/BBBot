#!/usr/bin/env python3
"""
Deploy Unified Broker Schema to MySQL
Deploys to local (Port 3307) and optionally to Railway
"""
import mysql.connector
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

SCHEMA_FILE = Path(__file__).parent / "bentleybot" / "sql" / "#MySQL for UNIFIED BROKER Schema.sql"

def execute_sql_file(connection, sql_file_path):
    """Execute SQL file with multiple statements"""
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Split by semicolon but keep CREATE TABLE blocks together
    statements = []
    current_statement = []
    in_create = False
    
    for line in sql_content.split('\n'):
        # Skip comments
        if line.strip().startswith('--') or line.strip().startswith('#'):
            continue
        
        current_statement.append(line)
        
        # Track if we're in CREATE TABLE
        if 'CREATE TABLE' in line.upper():
            in_create = True
        
        # End of statement
        if ';' in line and not in_create:
            statement = '\n'.join(current_statement).strip()
            if statement:
                statements.append(statement)
            current_statement = []
        elif ';' in line and in_create and 'ENGINE=' in line:
            # End of CREATE TABLE
            statement = '\n'.join(current_statement).strip()
            if statement:
                statements.append(statement)
            current_statement = []
            in_create = False
    
    # Execute statements
    cursor = connection.cursor()
    executed = 0
    failed = 0
    
    for statement in statements:
        if not statement or statement.isspace():
            continue
        
        try:
            cursor.execute(statement)
            connection.commit()
            executed += 1
        except mysql.connector.Error as e:
            # Ignore "already exists" errors
            if 'already exists' in str(e).lower():
                executed += 1
            else:
                print(f"⚠️  Error: {e}")
                print(f"   Statement: {statement[:100]}...")
                failed += 1
    
    return executed, failed

def deploy_to_local():
    """Deploy to local MySQL (Port 3307)"""
    print("=" * 80)
    print("DEPLOYING TO LOCAL MySQL (Port 3307)")
    print("=" * 80)
    
    try:
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', '127.0.0.1'),
            port=int(os.getenv('MYSQL_PORT', 3307)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', 'root'),
            database=os.getenv('MYSQL_DATABASE', 'mansa_bot')
        )
        
        print(f"✅ Connected to {os.getenv('MYSQL_HOST')}:3307/mansa_bot")
        print(f"📄 Executing schema from: {SCHEMA_FILE}")
        print()
        
        executed, failed = execute_sql_file(conn, SCHEMA_FILE)
        
        print()
        print(f"✅ Executed: {executed} statements")
        if failed > 0:
            print(f"❌ Failed: {failed} statements")
        
        # Verify tables created
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'mansa_bot' 
            AND table_name IN ('brokers', 'accounts', 'positions', 'orders', 'order_executions')
        """)
        tables = [t[0] for t in cursor.fetchall()]
        
        print()
        print("📊 Broker Schema Tables:")
        for table in ['brokers', 'accounts', 'positions', 'orders', 'order_executions']:
            status = "✅" if table in tables else "❌"
            print(f"   {status} {table}")
        
        conn.close()
        return len(tables) == 5
        
    except mysql.connector.Error as e:
        print(f"❌ Connection error: {e}")
        return False

def deploy_to_railway():
    """Deploy to Railway MySQL"""
    print()
    print("=" * 80)
    print("DEPLOYING TO RAILWAY MySQL")
    print("=" * 80)
    
    railway_host = os.getenv('RAILWAY_MYSQL_HOST')
    railway_port = os.getenv('RAILWAY_MYSQL_PORT')
    railway_password = os.getenv('RAILWAY_MYSQL_PASSWORD')
    
    if not railway_host or not railway_password or railway_password == '<from_streamlit_secrets>':
        print("⚠️  Railway MySQL credentials not configured")
        print("   Set RAILWAY_MYSQL_* variables in .env")
        return False
    
    try:
        conn = mysql.connector.connect(
            host=railway_host,
            port=int(railway_port),
            user=os.getenv('RAILWAY_MYSQL_USER', 'root'),
            password=railway_password,
            database='mansa_bot',
            connect_timeout=10
        )
        
        print(f"✅ Connected to {railway_host}:{railway_port}/mansa_bot")
        print(f"📄 Executing schema from: {SCHEMA_FILE}")
        print()
        
        executed, failed = execute_sql_file(conn, SCHEMA_FILE)
        
        print()
        print(f"✅ Executed: {executed} statements")
        if failed > 0:
            print(f"❌ Failed: {failed} statements")
        
        # Verify tables
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'mansa_bot' 
            AND table_name IN ('brokers', 'accounts', 'positions', 'orders', 'order_executions')
        """)
        tables = [t[0] for t in cursor.fetchall()]
        
        print()
        print("📊 Broker Schema Tables on Railway:")
        for table in ['brokers', 'accounts', 'positions', 'orders', 'order_executions']:
            status = "✅" if table in tables else "❌"
            print(f"   {status} {table}")
        
        conn.close()
        return len(tables) == 5
        
    except mysql.connector.Error as e:
        print(f"❌ Connection error: {e}")
        return False

def seed_broker_data(connection):
    """Insert initial broker configurations"""
    print()
    print("🌱 Seeding initial broker data...")
    
    cursor = connection.cursor()
    
    brokers = [
        ('alpaca', 'Alpaca Markets', 'equities', 'https://paper-api.alpaca.markets'),
        ('ibkr', 'Interactive Brokers', 'equities', 'https://api.ibkr.com'),
        ('schwab', 'Charles Schwab', 'equities', 'https://api.schwab.com'),
        ('binance', 'Binance', 'crypto', 'https://api.binance.com'),
        ('tradestation', 'TradeStation', 'equities', 'https://api.tradestation.com'),
        ('mt5', 'MetaTrader 5', 'forex', 'http://localhost:8000')
    ]
    
    for name, display_name, broker_type, api_url in brokers:
        try:
            cursor.execute("""
                INSERT INTO brokers (name, display_name, type, api_base_url)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    display_name = VALUES(display_name),
                    api_base_url = VALUES(api_base_url),
                    updated_at = CURRENT_TIMESTAMP
            """, (name, display_name, broker_type, api_url))
            connection.commit()
            print(f"   ✅ {display_name}")
        except mysql.connector.Error as e:
            print(f"   ⚠️  {display_name}: {e}")

if __name__ == "__main__":
    print()
    print("=" * 80)
    print("UNIFIED BROKER SCHEMA DEPLOYMENT")
    print("=" * 80)
    print()
    
    if not SCHEMA_FILE.exists():
        print(f"❌ Schema file not found: {SCHEMA_FILE}")
        exit(1)
    
    # Deploy to local
    local_success = deploy_to_local()
    
    # Optionally seed data
    if local_success:
        seed_local = input("\n🌱 Seed initial broker data to local MySQL? (y/n): ")
        if seed_local.lower() == 'y':
            conn = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST', '127.0.0.1'),
                port=int(os.getenv('MYSQL_PORT', 3307)),
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', 'root'),
                database=os.getenv('MYSQL_DATABASE', 'mansa_bot')
            )
            seed_broker_data(conn)
            conn.close()
    
    # Deploy to Railway
    deploy_railway = input("\n🚂 Deploy to Railway MySQL? (y/n): ")
    if deploy_railway.lower() == 'y':
        railway_success = deploy_to_railway()
        
        if railway_success:
            seed_railway = input("\n🌱 Seed initial broker data to Railway? (y/n): ")
            if seed_railway.lower() == 'y':
                conn = mysql.connector.connect(
                    host=os.getenv('RAILWAY_MYSQL_HOST'),
                    port=int(os.getenv('RAILWAY_MYSQL_PORT')),
                    user=os.getenv('RAILWAY_MYSQL_USER', 'root'),
                    password=os.getenv('RAILWAY_MYSQL_PASSWORD'),
                    database='mansa_bot',
                    connect_timeout=10
                )
                seed_broker_data(conn)
                conn.close()
    
    print()
    print("=" * 80)
    print("DEPLOYMENT COMPLETE")
    print("=" * 80)
    print()
    print("📚 Documentation:")
    print("   - Schema Guide: UNIFIED_BROKER_SCHEMA_GUIDE.md")
    print("   - Schema File: bentleybot/sql/#MySQL for UNIFIED BROKER Schema.sql")
    print()
