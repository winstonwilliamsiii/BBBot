"""
Complete BBBot Diagnostic Report
Generates a full system report to identify all issues
"""
import os
import sys
from dotenv import load_dotenv
import subprocess

print("="*60)
print("BBBot Complete Diagnostic Report")
print("="*60)
print()

# Load environment
load_dotenv()

# 1. Python Environment
print("1. PYTHON ENVIRONMENT")
print("-" * 60)
print(f"Python Version: {sys.version}")
print(f"Python Executable: {sys.executable}")
print()

# 2. Environment Variables
print("2. ENVIRONMENT VARIABLES (.env)")
print("-" * 60)

env_vars = {
    'BUDGET_MYSQL_HOST': os.getenv('BUDGET_MYSQL_HOST', 'NOT SET'),
    'BUDGET_MYSQL_PORT': os.getenv('BUDGET_MYSQL_PORT', 'NOT SET'),
    'BUDGET_MYSQL_USER': os.getenv('BUDGET_MYSQL_USER', 'NOT SET'),
    'BUDGET_MYSQL_PASSWORD': '***' if os.getenv('BUDGET_MYSQL_PASSWORD') else 'NOT SET',
    'BUDGET_MYSQL_DATABASE': os.getenv('BUDGET_MYSQL_DATABASE', 'NOT SET'),
    'PLAID_CLIENT_ID': os.getenv('PLAID_CLIENT_ID', 'NOT SET')[:15] + '...' if os.getenv('PLAID_CLIENT_ID') else 'NOT SET',
    'PLAID_SECRET': '***' if os.getenv('PLAID_SECRET') else 'NOT SET',
    'PLAID_ENV': os.getenv('PLAID_ENV', 'NOT SET'),
}

for key, value in env_vars.items():
    status = "✅" if value not in ['NOT SET', ''] else "❌"
    print(f"{status} {key}: {value}")
print()

# 3. MySQL Connection
print("3. MYSQL DATABASE CONNECTION")
print("-" * 60)
try:
    import mysql.connector
    config = {
        'host': os.getenv('BUDGET_MYSQL_HOST', '127.0.0.1'),
        'port': int(os.getenv('BUDGET_MYSQL_PORT', '3306')),
        'user': os.getenv('BUDGET_MYSQL_USER', 'root'),
        'password': os.getenv('BUDGET_MYSQL_PASSWORD', 'root'),
        'database': os.getenv('BUDGET_MYSQL_DATABASE', 'mydb'),
    }
    
    conn = mysql.connector.connect(**config)
    print(f"✅ Connected to MySQL")
    print(f"   Host: {config['host']}:{config['port']}")
    print(f"   Database: {config['database']}")
    
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"   Tables: {len(tables)} found")
    for table in tables:
        print(f"     - {table}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ MySQL Connection Failed: {e}")
print()

# 4. Plaid Configuration
print("4. PLAID INTEGRATION")
print("-" * 60)
try:
    from frontend.utils.plaid_link import PlaidLinkManager
    
    manager = PlaidLinkManager()
    print(f"✅ PlaidLinkManager initialized")
    print(f"   Client ID: {manager.client_id[:15]}...")
    print(f"   Environment: {manager.env}")
    print(f"   Host: {manager._get_plaid_host()}")
    
except ValueError as e:
    print(f"⚠️  Plaid Configuration Issue: {e}")
except Exception as e:
    print(f"❌ Plaid Error: {e}")
print()

# 5. Streamlit Status
print("5. STREAMLIT STATUS")
print("-" * 60)
try:
    import streamlit as st
    print(f"✅ Streamlit installed: {st.__version__}")
except Exception as e:
    print(f"❌ Streamlit issue: {e}")

# Check if Streamlit is running
try:
    result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, shell=True)
    if ':8501' in result.stdout:
        print("✅ Streamlit appears to be running on port 8501")
    else:
        print("⚠️  Streamlit not detected on port 8501")
except:
    print("⚠️  Could not check Streamlit status")
print()

# 6. Critical Files
print("6. CRITICAL FILES CHECK")
print("-" * 60)
critical_files = [
    'streamlit_app.py',
    'frontend/utils/budget_analysis.py',
    'frontend/utils/plaid_link.py',
    'frontend/components/budget_dashboard.py',
    'frontend/utils/rbac.py',
    'pages/01_💰_Personal_Budget.py',
    '.env',
]

for file in critical_files:
    if os.path.exists(file):
        print(f"✅ {file}")
    else:
        print(f"❌ {file} - MISSING!")
print()

# 7. Package Versions
print("7. KEY PACKAGE VERSIONS")
print("-" * 60)
packages = ['streamlit', 'mysql-connector-python', 'plaid-python', 'pandas', 'plotly', 'python-dotenv']
for package in packages:
    try:
        result = subprocess.run(['pip', 'show', package], capture_output=True, text=True)
        if 'Version:' in result.stdout:
            version = [line for line in result.stdout.split('\n') if 'Version:' in line][0]
            print(f"✅ {package}: {version.split(':')[1].strip()}")
        else:
            print(f"❌ {package}: NOT INSTALLED")
    except:
        print(f"⚠️  {package}: Could not check")
print()

# 8. Summary
print("="*60)
print("DIAGNOSTIC SUMMARY")
print("="*60)

issues = []

# Check each component
if not os.getenv('PLAID_CLIENT_ID'):
    issues.append("Plaid Client ID not configured")
if not os.getenv('BUDGET_MYSQL_HOST'):
    issues.append("Budget database config missing")

if issues:
    print("❌ ISSUES FOUND:")
    for issue in issues:
        print(f"   - {issue}")
else:
    print("✅ ALL SYSTEMS OPERATIONAL")

print()
print("="*60)
print("Save this output and share when resuming troubleshooting")
print("="*60)
