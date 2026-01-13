import mysql.connector
conn = mysql.connector.connect(host='127.0.0.1', port=3307, user='root', password='root', database='mansa_bot')
cursor = conn.cursor()
cursor.execute('SHOW TABLES')
all_tables = [t[0] for t in cursor.fetchall()]
print('All tables in mansa_bot:')
for t in all_tables:
    print(f'  - {t}')
conn.close()
