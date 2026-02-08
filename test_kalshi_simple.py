"""Simple Kalshi authentication test with detailed error reporting."""
import os
from dotenv import load_dotenv

load_dotenv('.env.development')

email = os.getenv('KALSHI_EMAIL')
password = os.getenv('KALSHI_PASSWORD')

print("=" * 60)
print("KALSHI AUTHENTICATION TEST")
print("=" * 60)
print(f"\nEmail: {email}")
print(f"Password length: {len(password) if password else 0} characters")
print(f"Password first char: {password[0] if password else 'N/A'}")
print(f"Password last char: {password[-1] if password else 'N/A'}")
print(f"Has special chars: {'!' in password or '@' in password}")

print("\n" + "=" * 60)
print("Attempting authentication...")
print("=" * 60)

try:
    from kalshi import Session
    
    # Try authentication
    session = Session(
        email=email,
        password=password,
        endpoint="https://api.elections.kalshi.com/v1"
    )
    
    print("\n✅ SUCCESS! Authentication worked!")
    print("\nTrying to get user profile...")
    
    try:
        profile = session.user_get_profile()
        print(f"Profile: {profile}")
    except Exception as e:
        print(f"Profile error: {e}")
    
except Exception as e:
    print(f"\n❌ AUTHENTICATION FAILED")
    print(f"Error: {e}")
    print("\nPossible reasons:")
    print("1. Password was recently changed on Kalshi")
    print("2. Account requires email verification")
    print("3. Account has 2FA enabled")
    print("4. Account is locked/suspended")
    print("5. API access not enabled for this account")
    print("\nPlease:")
    print("- Log into https://kalshi.com manually to verify account works")
    print("- Check if you can see your investment there")
    print("- Verify email is: winstonwilliamsiii@gmail.com")
    print("- Try resetting password if needed")
