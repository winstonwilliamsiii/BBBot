"""
🔍 PLAID DOMAIN WHITELIST CHECKER
==================================
Verify your Plaid dashboard has the correct domains whitelisted

This is THE #1 cause of "Waiting for SDK to load..." errors.
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("="*70)
print("🔍 PLAID DOMAIN WHITELIST CHECK")
print("="*70)

# Get current Plaid config
client_id = os.getenv('PLAID_CLIENT_ID', 'NOT_SET')
env = os.getenv('PLAID_ENV', 'sandbox')

print(f"\n📋 Your Current Plaid Configuration:")
print(f"   Client ID: {client_id[:20]}..." if client_id != 'NOT_SET' else "   Client ID: NOT_SET")
print(f"   Environment: {env}")

print(f"\n🌐 Domains That MUST Be Whitelisted in Plaid Dashboard:")
print("="*70)

domains_to_whitelist = [
    # Local development
    "http://localhost:8501",  # Streamlit default
    "http://localhost:8502",  # Streamlit custom
    "http://127.0.0.1:8501",
    "http://127.0.0.1:8502",
    
    # Production Streamlit Cloud
    "https://bbbot305.streamlit.app",
    "https://*.streamlit.app",  # Wildcard for all Streamlit Cloud apps
    
    # Vercel deployment
    "https://bentley-budget-bot.vercel.app",
    "https://*.vercel.app",  # Wildcard for Vercel
    
    # Next.js local dev (if applicable)
    "http://localhost:3000",
    
    # Lovable.app (if using)
    "https://*.lovable.app",
]

for i, domain in enumerate(domains_to_whitelist, 1):
    print(f"{i:2d}. {domain}")

print("\n" + "="*70)
print("⚠️  ACTION REQUIRED - Add These Domains to Plaid Dashboard")
print("="*70)

print("""
📍 WHERE TO ADD THESE DOMAINS:

1. Go to: https://dashboard.plaid.com/team/api
   
2. Click on "Keys" or "API" section
   
3. Find "Allowed redirect URIs" or "Allowed origins"
   
4. Add EACH domain listed above (one per line)
   
5. Click "Save" or "Update"

6. Wait 2-3 minutes for changes to propagate

⚠️  CRITICAL: Without these domains, Plaid Link SDK will NOT load.

The SDK checks the parent window's origin against your whitelist.
If not found → SDK refuses to initialize → "Waiting for SDK to load..."
""")

print("\n🧪 HOW TO TEST:")
print("="*70)
print("""
After adding domains to Plaid dashboard:

1. Clear your browser cache (Ctrl+Shift+Delete)
2. Close all browser tabs with your app
3. Restart your browser
4. Open: http://localhost:8502 (or your Streamlit URL)
5. Navigate to 🏦 Plaid Test page
6. Click "Create Link Token" 
7. Click "Open Plaid Link in New Window"
8. Open browser console (F12)
9. Check for these messages:
   ✅ "Plaid Link fully loaded"  → SUCCESS
   ❌ CORS error or no messages  → Domain still not whitelisted
""")

print("\n🔍 DEBUGGING TIPS:")
print("="*70)
print("""
If you STILL see "Waiting for SDK to load..." after whitelisting:

1. Check browser console (F12) → Console tab
   - Look for CORS errors mentioning 'plaid.com'
   - Look for 'Access-Control-Allow-Origin' errors

2. Check browser console → Network tab
   - Filter by 'plaid'
   - See if cdn.plaid.com/link/v2/stable/link-initialize.js loads
   - If blocked with red → domain not whitelisted
   - If 200 OK → domain is fine, check other issues

3. Verify the link_token:
   - In the popup URL, check if ?link_token= has a value
   - Should start with: link-sandbox-xxxxxx (sandbox)
   - Or: link-development-xxxxx (development)
   - Or: link-production-xxxxx (production)

4. Check Plaid environment:
   - Your PLAID_ENV must match the token type
   - Sandbox tokens won't work with development env
   - Development tokens won't work with production env
""")

print("\n📞 STILL NOT WORKING?")
print("="*70)
print("""
If domains are whitelisted but Plaid Link still won't load:

1. Contact Plaid Support: https://dashboard.plaid.com/support
   
2. Include this info:
   - Client ID: {client_id}
   - Environment: {env}
   - Domain trying to access: [your actual URL]
   - Error message: "Waiting for SDK to load..."
   - Browser: Chrome/Firefox/Safari
   - Console errors: [paste from F12]

3. Or check Plaid's status page:
   https://status.plaid.com/
""".format(client_id=client_id[:20] + "...", env=env))

print("\n" + "="*70)
print("✅ NEXT STEPS:")
print("="*70)
print("""
1. ✓ Add ALL domains listed above to Plaid dashboard
2. ✓ Save changes and wait 2-3 minutes
3. ✓ Clear browser cache
4. ✓ Test with browser console open (F12)
5. ✓ Report back what you see in console

Once domains are whitelisted, Plaid Link should load immediately.
No code changes needed - this is a Plaid dashboard configuration issue.
""")

print("="*70)
