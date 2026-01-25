"""Comprehensive health check for Bentley Budget Bot Dev Environment"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv(override=True)

print("="*70)
print("BENTLEY BUDGET BOT - DEV ENVIRONMENT HEALTH CHECK")
print("="*70)

results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

# 1. Check Plaid
print("\n[1/5] PLAID Integration...")
try:
    plaid_id = os.getenv('PLAID_CLIENT_ID', '')
    plaid_secret = os.getenv('PLAID_SECRET', '')
    plaid_env = os.getenv('PLAID_ENV', '')
    
    if plaid_id and plaid_secret and plaid_env:
        print(f"      CLIENT_ID: {plaid_id[:15]}... OK")
        print(f"      SECRET: {plaid_secret[:15]}... OK")
        print(f"      ENV: {plaid_env} OK")
        
        # Try to import and create manager
        try:
            from frontend.utils.plaid_link import PlaidLinkManager
            pm = PlaidLinkManager()
            token_data = pm.create_link_token('healthcheck_user')
            if token_data and 'link_token' in token_data:
                print(f"      LINK TOKEN: {token_data['link_token'][:20]}... OK")
                results['passed'].append('PLAID: Fully functional')
            else:
                results['warnings'].append('PLAID: Token creation failed')
        except Exception as e:
            results['warnings'].append(f'PLAID: {str(e)[:50]}')
    else:
        results['failed'].append('PLAID: Credentials missing')
except Exception as e:
    results['failed'].append(f'PLAID: {str(e)[:50]}')

# 2. Check Alpaca
print("\n[2/5] ALPACA Integration...")
try:
    alpaca_key = os.getenv('ALPACA_API_KEY', '')
    alpaca_secret = os.getenv('ALPACA_SECRET_KEY', '')
    alpaca_paper = os.getenv('ALPACA_PAPER', '')
    
    if alpaca_key and alpaca_secret:
        print(f"      API_KEY: {alpaca_key[:15]}... OK")
        print(f"      SECRET: {alpaca_secret[:15]}... OK")
        print(f"      PAPER MODE: {alpaca_paper} OK")
        
        try:
            from alpaca.trading.client import TradingClient
            client = TradingClient(alpaca_key, alpaca_secret, paper=True)
            account = client.get_account()
            print(f"      ACCOUNT: {account.status} - ${account.buying_power:.2f} buying power")
            results['passed'].append('ALPACA: Connected and authenticated')
        except Exception as e:
            results['warnings'].append(f'ALPACA: Connection error - {str(e)[:40]}')
    else:
        results['failed'].append('ALPACA: Credentials missing')
except Exception as e:
    results['failed'].append(f'ALPACA: {str(e)[:50]}')

# 3. Check MySQL (Port 3306)
print("\n[3/5] MySQL Database (Port 3306)...")
try:
    mysql_host = os.getenv('MYSQL_HOST', '127.0.0.1')
    mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', 'root')
    mysql_db = os.getenv('MYSQL_DATABASE', 'mansa_bot')
    
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_db
        )
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"      HOST: {mysql_host}:{mysql_port}")
        print(f"      DATABASE: {mysql_db}")
        print(f"      VERSION: MySQL {version}")
        cursor.close()
        conn.close()
        results['passed'].append('MySQL (3306): Connected')
    except Exception as e:
        results['failed'].append(f'MySQL (3306): {str(e)[:50]}')
except Exception as e:
    results['failed'].append(f'MySQL (3306): {str(e)[:50]}')

# 4. Check MySQL (Port 3307 - Docker BBBot1)
print("\n[4/5] MySQL Database (Port 3307 - Docker)...")
try:
    bbbot_host = os.getenv('BBBOT1_MYSQL_HOST', '127.0.0.1')
    bbbot_port = int(os.getenv('BBBOT1_MYSQL_PORT', '3307'))
    bbbot_user = os.getenv('BBBOT1_MYSQL_USER', 'root')
    bbbot_password = os.getenv('BBBOT1_MYSQL_PASSWORD', 'root')
    bbbot_db = os.getenv('BBBOT1_MYSQL_DATABASE', 'bbbot1')
    
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=bbbot_host,
            port=bbbot_port,
            user=bbbot_user,
            password=bbbot_password,
            database=bbbot_db
        )
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"      HOST: {bbbot_host}:{bbbot_port}")
        print(f"      DATABASE: {bbbot_db}")
        print(f"      VERSION: MySQL {version}")
        cursor.close()
        conn.close()
        results['passed'].append('MySQL (3307): Connected')
    except Exception as e:
        results['failed'].append(f'MySQL (3307): {str(e)[:50]}')
except Exception as e:
    results['failed'].append(f'MySQL (3307): {str(e)[:50]}')

# 5. Check MLFlow
print("\n[5/5] MLflow Tracking...")
try:
    mlflow_uri = os.getenv('MLFLOW_TRACKING_URI', '')
    mlflow_backend = os.getenv('MLFLOW_BACKEND_STORE_URI', '')
    
    if mlflow_uri:
        print(f"      TRACKING_URI: {mlflow_uri}")
        print(f"      BACKEND: {mlflow_backend[:30]}... OK")
        
        try:
            import mlflow
            mlflow.set_tracking_uri(mlflow_uri)
            # Try a simple operation
            experiment = mlflow.get_experiment_by_name('test_health_check')
            print(f"      CONNECTION: Active")
            results['passed'].append('MLflow: Accessible')
        except Exception as e:
            results['warnings'].append(f'MLflow: {str(e)[:40]}')
    else:
        results['failed'].append('MLflow: TRACKING_URI not configured')
except Exception as e:
    results['failed'].append(f'MLflow: {str(e)[:50]}')

# Print Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

if results['passed']:
    print(f"\nPASSED ({len(results['passed'])})")
    for item in results['passed']:
        print(f"  [+] {item}")

if results['warnings']:
    print(f"\nWARNINGS ({len(results['warnings'])})")
    for item in results['warnings']:
        print(f"  [!] {item}")

if results['failed']:
    print(f"\nFAILED ({len(results['failed'])})")
    for item in results['failed']:
        print(f"  [-] {item}")

print("\n" + "="*70)
total = len(results['passed']) + len(results['failed'])
passed = len(results['passed'])
status = "GREEN" if len(results['failed']) == 0 else "RED"
print(f"OVERALL: {passed}/{total} services operational [{status}]")
print("="*70)

if results['failed']:
    sys.exit(1)
