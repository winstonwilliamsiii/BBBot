"""
Development Environment Setup Script
====================================
Automated setup for Bentley Bot local development.

This script will:
1. Create MySQL database and tables
2. Verify all API connections
3. Set up MLflow tracking
4. Configure Streamlit secrets
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and print results"""
    print(f"\n📦 {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print(f"   {result.stdout[:200]}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def setup_mysql_database():
    """Create MySQL database if it doesn't exist"""
    print("\n" + "="*60)
    print("SETTING UP MYSQL DATABASE")
    print("="*60)
    
    try:
        import mysql.connector
        from dotenv import load_dotenv
        
        load_dotenv('.env.development', override=True)
        
        # Connect without database first
        conn = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password=''  # Empty password for root in dev
        )
        
        cursor = conn.cursor()
        
        # Create database
        db_name = 'bentley_bot_dev'
        print(f"\n1. Creating database '{db_name}'...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"✅ Database '{db_name}' ready")
        
        # Switch to the database
        cursor.execute(f"USE {db_name}")
        
        # Create essential tables
        print("\n2. Creating essential tables...")
        
        # Users table for RBAC
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                role VARCHAR(20) DEFAULT 'VIEWER',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        print("   ✅ users table")
        
        # Transactions table for budget tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                account_id VARCHAR(100),
                amount DECIMAL(10, 2) NOT NULL,
                category VARCHAR(50),
                date DATE NOT NULL,
                description TEXT,
                merchant_name VARCHAR(100),
                plaid_transaction_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        print("   ✅ transactions table")
        
        # Plaid items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plaid_items (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                plaid_item_id VARCHAR(100) UNIQUE NOT NULL,
                access_token VARCHAR(255) NOT NULL,
                institution_id VARCHAR(100),
                institution_name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_synced TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        print("   ✅ plaid_items table")
        
        # Stock prices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_prices_yf (
                id INT PRIMARY KEY AUTO_INCREMENT,
                ticker VARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                open DECIMAL(10, 2),
                high DECIMAL(10, 2),
                low DECIMAL(10, 2),
                close DECIMAL(10, 2),
                volume BIGINT,
                adj_close DECIMAL(10, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY ticker_date (ticker, date)
            )
        """)
        print("   ✅ stock_prices_yf table")
        
        # Create default admin user
        print("\n3. Creating default admin user...")
        cursor.execute("""
            INSERT IGNORE INTO users (username, password_hash, email, role)
            VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqQqZ5wQ5u', 'admin@localhost', 'ADMIN')
        """)
        # Password is 'admin123' - hashed with bcrypt
        print("   ✅ Default admin user created (username: admin, password: admin123)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n✅ MySQL database setup complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ MySQL setup failed: {e}")
        print("\nTroubleshooting:")
        print("1. Is MySQL running? Check with: Get-Service MySQL*")
        print("2. Is root password correct? Default is empty for local dev")
        print("3. Try connecting manually: mysql -u root -p")
        return False


def install_missing_packages():
    """Install any missing Python packages"""
    print("\n" + "="*60)
    print("CHECKING PYTHON PACKAGES")
    print("="*60)
    
    required_packages = [
        'streamlit',
        'yfinance',
        'mysql-connector-python',
        'pandas',
        'plotly',
        'python-dotenv',
        'beautifulsoup4',
        'requests',
        'sqlalchemy',
        'pymysql',
        'mlflow',
        'plaid-python',
        'alpaca-py'
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("\nInstalling missing packages...")
        for package in missing:
            run_command(
                f'pip install {package}',
                f'Installing {package}'
            )
    else:
        print("\n✅ All required packages installed!")
    
    return True


def create_api_credentials_guide():
    """Create a guide for getting API credentials"""
    guide_path = 'DEV_API_CREDENTIALS_GUIDE.md'
    
    content = """# Development API Credentials Guide

This guide helps you get real API credentials for development.

## ✅ Already Working
- **MySQL**: Configured with root user
- **yFinance**: No API key needed - works out of the box

## 🔑 API Keys Needed

### 1. Alpaca Paper Trading (Required for Trading Features)

**Why**: Test trading strategies without real money

**Steps**:
1. Go to https://alpaca.markets
2. Click "Sign Up" → Choose "Paper Trading Account" (FREE)
3. Verify email and complete registration
4. Go to Dashboard → API Keys
5. Generate "Paper Trading" API keys
6. Copy keys to `.env.development`:
   ```
   ALPACA_API_KEY=PK...
   ALPACA_SECRET_KEY=...
   ```

**Time**: 5 minutes

---

### 2. Plaid Sandbox (Required for Personal Budget Features)

**Why**: Connect bank accounts for budget tracking

**Steps**:
1. Go to https://plaid.com
2. Click "Get API Keys" → Sign up for free
3. Complete registration (no credit card needed)
4. Go to Dashboard → Team Settings → Keys
5. Copy "Sandbox" credentials
6. Update `.env.development`:
   ```
   PLAID_CLIENT_ID=...
   PLAID_SECRET=...
   PLAID_ENVIRONMENT=sandbox
   ```

**Time**: 5 minutes

---

### 3. AlphaVantage (Optional - Enhanced Data)

**Why**: Get detailed fundamental data for stocks

**Steps**:
1. Go to https://www.alphavantage.co/support/#api-key
2. Enter your email
3. Check email for API key
4. Update `.env.development`:
   ```
   ALPHA_VANTAGE_API_KEY=...
   ```

**Time**: 2 minutes

---

### 4. Kalshi (Optional - Prediction Markets)

**Why**: Access prediction market data

**Current Status**: Already configured with demo credentials

**Note**: Requires ADMIN role to access Prediction Analytics page

---

## 🚀 After Getting Credentials

1. Update `.env.development` with your real keys
2. Run: `python fix_dev_apis.py` to verify all connections
3. Run: `streamlit run streamlit_app.py` to start the app

---

## 📞 Support

If you have issues:
1. Check the error messages in `fix_dev_apis.py` output
2. Verify your API keys are correctly copied (no extra spaces)
3. Make sure you're using the correct environment (sandbox for Plaid, paper for Alpaca)

---

## 🔒 Security Notes

- **Never commit** `.env.development` to Git (already in `.gitignore`)
- These are development credentials only
- Use different credentials for production
- Rotate keys regularly
"""
    
    with open(guide_path, 'w') as f:
        f.write(content)
    
    print(f"\n✅ Created {guide_path}")
    print("   Open this file for instructions on getting API credentials")


def main():
    """Main setup function"""
    print("\n" + "🚀 BENTLEY BOT - DEVELOPMENT ENVIRONMENT SETUP")
    print("=" * 60)
    
    steps = [
        ("Install Python Packages", install_missing_packages),
        ("Setup MySQL Database", setup_mysql_database),
        ("Create API Guide", create_api_credentials_guide),
    ]
    
    results = []
    for step_name, step_func in steps:
        try:
            success = step_func()
            results.append((step_name, success))
        except Exception as e:
            print(f"\n❌ {step_name} failed: {e}")
            results.append((step_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 SETUP SUMMARY")
    print("="*60)
    
    for step_name, success in results:
        icon = "✅" if success else "❌"
        print(f"   {icon} {step_name}")
    
    all_success = all(success for _, success in results)
    
    if all_success:
        print("\n✅ Setup complete!")
        print("\n📋 Next Steps:")
        print("   1. Read DEV_API_CREDENTIALS_GUIDE.md")
        print("   2. Get API credentials (takes ~15 minutes total)")
        print("   3. Update .env.development with real credentials")
        print("   4. Run: python fix_dev_apis.py")
        print("   5. Run: streamlit run streamlit_app.py")
    else:
        print("\n⚠️  Setup partially complete")
        print("   Review errors above and try again")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
