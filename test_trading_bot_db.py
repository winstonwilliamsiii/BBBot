"""Test Trading Bot Database Connection"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv('.env.development')

db_host = os.getenv('MYSQL_HOST')
db_port = int(os.getenv('MYSQL_PORT'))
db_user = os.getenv('MYSQL_USER')
db_password = os.getenv('MYSQL_PASSWORD')
db_name = os.getenv('MYSQL_DATABASE')

print(f"Testing connection to: {db_host}:{db_port}/{db_name}")

connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(connection_string, pool_pre_ping=True)

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM bot_status'))
        count = result.fetchone()[0]
        print(f"✅ Trading Bot Database Connected!")
        print(f"   Host: {db_host}:{db_port}")
        print(f"   Database: {db_name}")
        print(f"   User: {db_user}")
        print(f"   bot_status table records: {count}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
