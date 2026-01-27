"""Check database schema and tables on port 3307"""
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

print("="*60)
print("DATABASE SCHEMA CHECK - Port 3307")
print("="*60)

# Connect to port 3307
conn = mysql.connector.connect(
    host='127.0.0.1',
    port=3307,
    user='root',
    password='root'
)
cursor = conn.cursor()

# Show all databases
cursor.execute('SHOW DATABASES')
dbs = cursor.fetchall()
print('\nAll Databases on Port 3307:')
for db in dbs:
    print(f'  - {db[0]}')

# Check mansa databases specifically
print('\n' + "="*60)
print('MANSA DATABASE DETAILS')
print("="*60)

mansa_patterns = ['mansa%', 'bbbot%', 'bentley%']
for pattern in mansa_patterns:
    cursor.execute(f"SHOW DATABASES LIKE '{pattern}'")
    matched_dbs = cursor.fetchall()
    
    for db_tuple in matched_dbs:
        db_name = db_tuple[0]
        print(f'\n📊 Database: {db_name}')
        cursor.execute(f'USE `{db_name}`')
        cursor.execute('SHOW TABLES')
        tables = cursor.fetchall()
        
        if tables:
            print(f'   Tables ({len(tables)}):')
            for t in tables:
                table_name = t[0]
                # Get row count
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM `{table_name}`')
                    count = cursor.fetchone()[0]
                    print(f'     - {table_name} ({count} rows)')
                except Exception as e:
                    print(f'     - {table_name} (error: {str(e)[:30]})')
        else:
            print('   ⚠️  No tables found')

cursor.close()
conn.close()

print('\n' + "="*60)
print('RECOMMENDATION')
print("="*60)
print('''
Based on the output above:
1. If mansa_bot and bentley_bot_dev have similar schemas → Merge recommended
2. If mansa_quant shows 0 tables → Need to create/restore tables
3. Check .env for correct database names in MYSQL_DATABASE variables
''')
