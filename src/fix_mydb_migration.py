#!/usr/bin/env python3
"""Quick mydb migration fix"""
import mysql.connector

# Connect to both instances
print("Connecting to databases...")
src = mysql.connector.connect(host='127.0.0.1', port=3306, user='root', password='root', database='mydb')
dst = mysql.connector.connect(host='127.0.0.1', port=3307, user='root', password='root')

dst_cursor = dst.cursor()
dst_cursor.execute('CREATE DATABASE IF NOT EXISTS mydb')
dst_cursor.execute('USE mydb')

src_cursor = src.cursor()
src_cursor.execute('SHOW TABLES')
tables = [t[0] for t in src_cursor.fetchall()]

print(f'Migrating {len(tables)} tables from mydb...')

for table in tables:
    try:
        # Check if it's a view
        src_cursor.execute(f"SELECT TABLE_TYPE FROM information_schema.TABLES WHERE TABLE_SCHEMA='mydb' AND TABLE_NAME='{table}'")
        table_type = src_cursor.fetchone()[0]
        
        if table_type == 'VIEW':
            print(f'  ⏭️  {table}: Skipping view')
            continue
        
        # Get CREATE statement
        src_cursor.execute(f"SHOW CREATE TABLE `{table}`")
        create_sql = src_cursor.fetchone()[1]
        
        # Drop and recreate table
        dst_cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
        dst_cursor.execute(create_sql)
        
        # Copy data
        src_cursor.execute(f"SELECT * FROM `{table}`")
        rows = src_cursor.fetchall()
        
        if rows:
            # Get column count for placeholders
            placeholders = ', '.join(['%s'] * len(rows[0]))
            dst_cursor.executemany(f"INSERT INTO `{table}` VALUES ({placeholders})", rows)
            dst.commit()
        
        print(f'  ✅ {table}: {len(rows)} rows')
    except Exception as e:
        print(f'  ❌ {table}: Error - {e}')
        continue

print('✅ mydb migration complete!')
src.close()
dst.close()
