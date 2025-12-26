
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the frontend/utils directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'frontend' / 'utils'))

def test_plaid_api():
    """Test Plaid API configuration"""
    print("============= PLAID API TEST ==============")
    
    try:
        from plaid_link import PlaidLinkManager
        
        print("Attempting to initialize PlaidLinkManager...")
        manager = PlaidLinkManager()
        print("✅ SUCCESS! PlaidLinkManager initialized")
        
        print("
Attempting to create a link token...")
        link_token_response = manager.create_link_token(user_id='test_user')
        
        if link_token_response and 'link_token' in link_token_response:
            print("✅ SUCCESS! Link token created successfully.")
            print(f"   Link Token: {link_token_response['link_token']}")
        else:
            print("❌ FAILED to create link token.")
            
    except ImportError as e:
        print(f"❌ FAILED to import PlaidLinkManager: {e}")
        print("   Please ensure that the 'frontend/utils/plaid_link.py' file exists.")
        
    except Exception as e:
        print(f"❌ FAILED to initialize or use PlaidLinkManager: {e}")

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    test_plaid_api()
