"""
Fetch and Display Webull Funds
Standalone script to fetch WeFolio funds and save to database

This script is integrated into the Investment Analysis page under the
Broker Connections tab (requires RBAC authentication).

For interactive use, see: pages/01_📈_Investment_Analysis.py
"""

import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from frontend.utils.broker_connections import BrokerConnectionManager, WebullFund
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "user"),
    "password": os.getenv("MYSQL_PASSWORD", "pass"),
    "database": os.getenv("MYSQL_DATABASE", "bentley_budget")
}


def fetch_and_save_webull_funds(api_token: str, use_demo: bool = False):
    """
    Fetch WeFolio funds and save to database
    
    Args:
        api_token: Webull API authentication token
        use_demo: If True, use demo data instead of API
    """
    print("=" * 60)
    print("Webull WeFolio Fund Fetcher")
    print("=" * 60)
    
    if use_demo:
        print("\n📊 Using demo data...")
        funds = BrokerConnectionManager.get_demo_webull_funds()
    else:
        print(f"\n🔄 Fetching funds from Webull API...")
        funds = BrokerConnectionManager.fetch_webull_funds(api_token)
    
    if not funds:
        print("❌ No funds fetched. Exiting.")
        return
    
    print(f"✅ Fetched {len(funds)} funds\n")
    
    # Display fund summary
    print("-" * 60)
    print(f"{'Fund Name':<30} {'NAV':>10} {'Value':>15}")
    print("-" * 60)
    
    total_value = 0
    for fund in funds:
        print(f"{fund.name:<30} ${fund.nav:>9.2f} ${fund.value:>14,.2f}")
        total_value += fund.value
    
    print("-" * 60)
    print(f"{'TOTAL':<30} {'':<10} ${total_value:>14,.2f}")
    print("-" * 60)
    
    # Save to database
    print("\n💾 Saving funds to database...")
    
    try:
        BrokerConnectionManager.save_funds_to_db(funds, MYSQL_CONFIG)
        print("✅ Successfully saved all funds to database")
    except Exception as e:
        print(f"❌ Failed to save to database: {e}")
        print("\n⚠️  Make sure MySQL is running and credentials are correct")
        print(f"   Config: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['database']}")
    
    print("\n" + "=" * 60)
    print("Complete!")
    print("=" * 60)


def setup_database():
    """Create database table if it doesn't exist"""
    import mysql.connector
    
    print("\n🔧 Setting up database table...")
    
    try:
        conn = mysql.connector.connect(
            host=MYSQL_CONFIG["host"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
            database=MYSQL_CONFIG["database"]
        )
        
        cursor = conn.cursor()
        
        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wefolio_funds (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                nav DECIMAL(10, 2),
                shares DECIMAL(15, 4),
                value DECIMAL(15, 2),
                daily_change DECIMAL(15, 2),
                daily_change_pct DECIMAL(5, 2),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_last_updated (last_updated),
                INDEX idx_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Database table ready")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fetch Webull WeFolio funds and save to database"
    )
    parser.add_argument(
        "--token",
        type=str,
        help="Webull API token (or set WEBULL_API_TOKEN env var)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use demo data instead of real API"
    )
    parser.add_argument(
        "--setup-db",
        action="store_true",
        help="Create database table if it doesn't exist"
    )
    
    args = parser.parse_args()
    
    # Setup database if requested
    if args.setup_db:
        if not setup_database():
            sys.exit(1)
    
    # Get API token
    token = args.token or os.getenv("WEBULL_API_TOKEN")
    
    if not token and not args.demo:
        print("❌ Error: Webull API token required")
        print("\nUsage:")
        print("  1. Provide token: python script.py --token YOUR_TOKEN")
        print("  2. Set env var: export WEBULL_API_TOKEN=YOUR_TOKEN")
        print("  3. Use demo data: python script.py --demo")
        sys.exit(1)
    
    # Fetch and save funds
    fetch_and_save_webull_funds(token, use_demo=args.demo)
    
    print("\n💡 Tip: Use the Investment Analysis page for interactive management")
    print("   Navigate to: pages/01_📈_Investment_Analysis.py")
    print("   Login as 'client' or 'investor' to access Broker Connections")