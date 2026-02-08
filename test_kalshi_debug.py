"""Debug script to test Kalshi API and understand response structure."""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.development')

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from prediction_analytics.services.kalshi_client import KalshiClient

def test_kalshi_connection():
    """Test Kalshi authentication and API calls."""
    print("=" * 60)
    print("🔍 KALSHI API DEBUG TEST")
    print("=" * 60)
    
    # Get credentials (supports both inline key and file path)
    api_key_id = os.getenv('KALSHI_API_KEY_ID')
    private_key = os.getenv('KALSHI_PRIVATE_KEY')
    private_key_path = os.getenv('KALSHI_PRIVATE_KEY_PATH')
    
    print(f"\n🔑 API Key ID: {api_key_id[:20] + '...' if api_key_id else 'NOT SET'}")
    print(f"🔐 Inline Private Key: {'SET' if private_key else 'NOT SET'}")
    print(f"📄 Private Key Path: {private_key_path if private_key_path else 'NOT SET'}")
    
    if not api_key_id or (not private_key and not private_key_path):
        print("\n❌ ERROR: Kalshi API credentials not found")
        print("\n📝 Required credentials:")
        print("   KALSHI_API_KEY_ID=your-key-id-here")
        print("   AND one of:")
        print("   KALSHI_PRIVATE_KEY='-----BEGIN RSA PRIVATE KEY----- ...'")
        print("   KALSHI_PRIVATE_KEY_PATH=./kalshi-private-key.key")
        print("\n🔗 Generate keys at: https://kalshi.com/account/profile")
        return
    
    # Initialize client
    print("\n🔄 Initializing Kalshi client...")
    client = KalshiClient(api_key_id=api_key_id, private_key=private_key, private_key_path=private_key_path)
    
    print(f"✅ Authenticated: {client.authenticated}")
    if not client.authenticated:
        print(f"❌ Auth Error: {client.last_error}")
        return
    
    print("\n" + "=" * 60)
    print("📊 TESTING API ENDPOINTS")
    print("=" * 60)
    
    # Test 1: Get Profile
    print("\n1️⃣ GET USER PROFILE")
    print("-" * 60)
    try:
        profile = client.get_user_profile()
        print(f"✅ Profile Response Type: {type(profile)}")
        print(f"📄 Profile Data:")
        if isinstance(profile, dict):
            for key, value in profile.items():
                print(f"   {key}: {value}")
        else:
            print(f"   {profile}")
    except Exception as e:
        print(f"❌ Profile Error: {e}")
    
    # Test 2: Get Balance
    print("\n2️⃣ GET USER BALANCE")
    print("-" * 60)
    try:
        balance = client.get_user_balance()
        print(f"✅ Balance Response Type: {type(balance)}")
        print(f"💰 Balance Data:")
        if isinstance(balance, dict):
            for key, value in balance.items():
                print(f"   {key}: {value}")
        else:
            print(f"   {balance}")
    except Exception as e:
        print(f"❌ Balance Error: {e}")
    
    # Test 3: Get Portfolio (MAIN ISSUE)
    print("\n3️⃣ GET USER PORTFOLIO (POSITIONS)")
    print("-" * 60)
    try:
        positions = client.get_user_portfolio()
        print(f"✅ Positions Response Type: {type(positions)}")
        print(f"📈 Number of Positions: {len(positions) if positions else 0}")
        print(f"📊 Raw Positions Data:")
        print(positions)
        
        if positions:
            print("\n🔍 Detailed Position Analysis:")
            for i, pos in enumerate(positions, 1):
                print(f"\n   Position {i}:")
                if isinstance(pos, dict):
                    for key, value in pos.items():
                        print(f"      {key}: {value}")
                else:
                    print(f"      {pos}")
        else:
            print("\n⚠️ WARNING: Portfolio is empty!")
            print("   But user confirmed they have $9.82 investment on Kalshi website.")
            print("   This is the BUG we're trying to fix!")
    except Exception as e:
        print(f"❌ Portfolio Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Get Trades/Fills
    print("\n4️⃣ GET USER TRADES (FILLS)")
    print("-" * 60)
    try:
        trades = client.get_user_trades(limit=10)
        print(f"✅ Trades Response Type: {type(trades)}")
        print(f"📊 Number of Trades: {len(trades) if trades else 0}")
        print(f"📄 Raw Trades Data:")
        print(trades)
        
        if trades:
            print("\n🔍 Detailed Trade Analysis:")
            for i, trade in enumerate(trades, 1):
                print(f"\n   Trade {i}:")
                if isinstance(trade, dict):
                    for key, value in trade.items():
                        print(f"      {key}: {value}")
                else:
                    print(f"      {trade}")
    except Exception as e:
        print(f"❌ Trades Error: {e}")
    
    # Test 5: Get Account History
    print("\n5️⃣ GET ACCOUNT HISTORY")
    print("-" * 60)
    try:
        history = client.get_account_history()
        print(f"✅ History Response Type: {type(history)}")
        print(f"📊 Number of History Items: {len(history) if history else 0}")
        print(f"📄 Raw History Data:")
        print(history)
    except Exception as e:
        print(f"❌ History Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ DEBUG TEST COMPLETE")
    print("=" * 60)
    print("\nIf positions are empty but user has investments:")
    print("1. Check if trades/fills show the investment")
    print("2. Check if account history shows deposits/activity")
    print("3. Verify the Kalshi account email matches")
    print("4. Try different API methods or parameters")
    print("5. Check Kalshi SDK documentation for updated methods")

if __name__ == "__main__":
    test_kalshi_connection()
