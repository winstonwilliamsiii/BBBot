#!/usr/bin/env python3
"""
Comprehensive API Connection Test
Tests MySQL, Plaid, Alpaca, and Tiingo connections after consolidation
Author: Bentley Budget Bot Development Team
"""
import mysql.connector
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_mysql_connection():
    """Test MySQL connection on Port 3307"""
    print("=" * 100)
    print("1. MYSQL CONNECTION TEST")
    print("=" * 100)
    
    databases = [
        ('Main Database', 'MYSQL', os.getenv('MYSQL_DATABASE', 'mansa_bot')),
        ('Budget Database', 'BUDGET_MYSQL', os.getenv('BUDGET_MYSQL_DATABASE', 'mydb')),
        ('Operational Database', 'BBBOT1_MYSQL', os.getenv('BBBOT1_MYSQL_DATABASE', 'bbbot1')),
        ('MGR Schema', 'MYSQL', 'mgrp_schema'),
        ('MLflow Database', 'MLFLOW_MYSQL', os.getenv('MLFLOW_MYSQL_DATABASE', 'mlflow_db'))
    ]
    
    results = []
    
    for name, prefix, db_name in databases:
        try:
            # Get configuration
            if prefix == 'MYSQL':
                host = os.getenv('MYSQL_HOST', '127.0.0.1')
                port = int(os.getenv('MYSQL_PORT', '3307'))
                user = os.getenv('MYSQL_USER', 'root')
                password = os.getenv('MYSQL_PASSWORD', 'root')
            elif prefix == 'MLFLOW_MYSQL':
                host = os.getenv('MLFLOW_MYSQL_HOST', os.getenv('MYSQL_HOST', '127.0.0.1'))
                port = int(os.getenv('MLFLOW_MYSQL_PORT', os.getenv('MYSQL_PORT', '3307')))
                user = os.getenv('MLFLOW_MYSQL_USER', os.getenv('MYSQL_USER', 'root'))
                password = os.getenv('MLFLOW_MYSQL_PASSWORD', os.getenv('MYSQL_PASSWORD', 'root'))
            else:
                host = os.getenv(f'{prefix}_HOST', '127.0.0.1')
                port = int(os.getenv(f'{prefix}_PORT', '3307'))
                user = os.getenv(f'{prefix}_USER', 'root')
                password = os.getenv(f'{prefix}_PASSWORD', 'root')
            
            # Attempt connection
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=db_name,
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            table_count = len(tables)
            
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"✅ {name} ({db_name})")
            print(f"   Port: {port}")
            print(f"   Tables: {table_count}")
            print(f"   Version: {version}")
            results.append((name, True, f"{table_count} tables"))
            
        except mysql.connector.Error as e:
            print(f"❌ {name} ({db_name})")
            print(f"   Error: {e}")
            results.append((name, False, str(e)))
        except Exception as e:
            print(f"❌ {name} ({db_name})")
            print(f"   Error: {e}")
            results.append((name, False, str(e)))
        
        print()
    
    return results

def test_tiingo_connection():
    """Test Tiingo API connection"""
    print("=" * 100)
    print("2. TIINGO API CONNECTION TEST")
    print("=" * 100)
    
    api_key = os.getenv('TIINGO_API_KEY')
    
    if not api_key or api_key.startswith('your_'):
        print("❌ Tiingo API key not configured in .env")
        return [('Tiingo', False, 'API key missing')]
    
    try:
        # Test endpoint
        url = "https://api.tiingo.com/api/test"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {api_key}'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', 'OK')
            if isinstance(message, str) and 'not correct' in message.lower():
                print(f"❌ Tiingo API Failed")
                print(f"   Message: {message}")
                return [('Tiingo', False, message)]
            print(f"✅ Tiingo API Connected")
            print(f"   Message: {message}")
            return [('Tiingo', True, 'Connected')]
        else:
            print(f"❌ Tiingo API Failed")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return [('Tiingo', False, f'HTTP {response.status_code}')]
            
    except requests.exceptions.Timeout:
        print(f"❌ Tiingo API Timeout")
        return [('Tiingo', False, 'Request timeout')]
    except Exception as e:
        print(f"❌ Tiingo API Error: {e}")
        return [('Tiingo', False, str(e))]
    finally:
        print()

def test_alpaca_connection():
    """Test Alpaca API connection"""
    print("=" * 100)
    print("3. ALPACA API CONNECTION TEST")
    print("=" * 100)
    
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_SECRET_KEY')
    paper_mode = os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
    
    if not api_key or not api_secret:
        print("❌ Alpaca credentials not configured in .env")
        return [('Alpaca', False, 'Credentials missing')]
    
    try:
        # Test account endpoint
        base_url = "https://paper-api.alpaca.markets" if paper_mode else "https://api.alpaca.markets"
        url = f"{base_url}/v2/account"
        headers = {
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': api_secret
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Alpaca API Connected ({'PAPER' if paper_mode else 'LIVE'})")
            print(f"   Account Status: {data.get('status', 'UNKNOWN')}")
            print(f"   Currency: {data.get('currency', 'USD')}")
            return [('Alpaca', True, 'Connected')]
        else:
            print(f"❌ Alpaca API Failed")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return [('Alpaca', False, f'HTTP {response.status_code}')]
            
    except requests.exceptions.Timeout:
        print(f"❌ Alpaca API Timeout")
        return [('Alpaca', False, 'Request timeout')]
    except Exception as e:
        print(f"❌ Alpaca API Error: {e}")
        return [('Alpaca', False, str(e))]
    finally:
        print()

def test_plaid_connection():
    """Test Plaid API connection"""
    print("=" * 100)
    print("4. PLAID API CONNECTION TEST")
    print("=" * 100)
    
    client_id = os.getenv('PLAID_CLIENT_ID')
    secret = os.getenv('PLAID_SECRET')
    env = os.getenv('PLAID_ENV', 'sandbox')
    
    if not client_id or not secret:
        print("❌ Plaid credentials not configured in .env")
        return [('Plaid', False, 'Credentials missing')]
    
    try:
        # Test with /item/get endpoint (requires item_access_token)
        # For basic connectivity, we'll test the API base URL
        url = f"https://{env}.plaid.com/link/token/create"
        
        payload = {
            "client_id": client_id,
            "secret": secret,
            "client_name": "Bentley Budget Bot Test",
            "country_codes": ["US"],
            "language": "en",
            "user": {
                "client_user_id": "test_user"
            },
            "products": ["auth", "transactions"]
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Plaid API Connected")
            print(f"   Environment: {env}")
            print(f"   Link Token Created: {data.get('link_token', 'N/A')[:50]}...")
            return [('Plaid', True, 'Connected')]
        else:
            print(f"❌ Plaid API Failed")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return [('Plaid', False, f'HTTP {response.status_code}')]
            
    except requests.exceptions.Timeout:
        print(f"❌ Plaid API Timeout")
        return [('Plaid', False, 'Request timeout')]
    except Exception as e:
        print(f"❌ Plaid API Error: {e}")
        return [('Plaid', False, str(e))]
    finally:
        print()

if __name__ == "__main__":
    print("\n")
    print("=" * 100)
    print("COMPREHENSIVE API CONNECTION TEST")
    print("Testing MySQL, Tiingo, Alpaca, and Plaid connections")
    print("=" * 100)
    print()
    
    all_results = []
    
    # Test all services
    mysql_results = test_mysql_connection()
    all_results.extend(mysql_results)
    
    tiingo_results = test_tiingo_connection()
    all_results.extend(tiingo_results)
    
    alpaca_results = test_alpaca_connection()
    all_results.extend(alpaca_results)
    
    plaid_results = test_plaid_connection()
    all_results.extend(plaid_results)
    
    # Final Summary
    print("=" * 100)
    print("📊 FINAL SUMMARY")
    print("=" * 100)
    print()
    
    successful = sum(1 for _, success, _ in all_results if success)
    total = len(all_results)
    
    print(f"Success Rate: {successful}/{total} connections")
    print()
    
    print("Detailed Results:")
    for service, success, message in all_results:
        status = "✅" if success else "❌"
        print(f"{status} {service:<25} {message}")
    
    print()
    
    if successful == total:
        print("🎉 ALL API CONNECTIONS SUCCESSFUL!")
        print("\n✅ Your consolidation to Port 3307 is complete and working!")
        print("\n📋 Final Steps:")
        print("   1. Consider shutting down MySQL on Port 3306")
        print("   2. Remove Port 3306 from startup services")
        print("   3. Update any external documentation")
    else:
        failed = [service for service, success, _ in all_results if not success]
        print(f"⚠️  {len(failed)} CONNECTION(S) FAILED")
        print(f"\nFailed services: {', '.join(failed)}")
        print("\nTroubleshooting:")
        print("   - Check .env file for correct credentials")
        print("   - Verify MySQL is running on Port 3307")
        print("   - Confirm API keys are valid and not expired")
        print("   - Check network/firewall settings")
    
    print("\n" + "=" * 100)
