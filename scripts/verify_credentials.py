"""
Final Verification - Tests both Plaid and Alpaca with Streamlit secrets
"""

import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

st.title("🔧 Credential Verification Dashboard")
st.markdown("---")

def get_secret_with_nested_support(key: str, default: str = None) -> str:
    """Get secret from Streamlit secrets (nested format) or environment"""
    try:
        # Try flat format
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
        
        # Try nested format
        if hasattr(st, 'secrets'):
            section_map = {
                'PLAID_CLIENT_ID': 'plaid',
                'PLAID_SECRET': 'plaid',
                'PLAID_ENV': 'plaid',
                'ALPACA_API_KEY': 'alpaca',
                'ALPACA_SECRET_KEY': 'alpaca',
                'ALPACA_PAPER': 'alpaca',
            }
            
            section = section_map.get(key)
            if section and section in st.secrets:
                if key in st.secrets[section]:
                    return str(st.secrets[section][key])
    except Exception:
        pass
    
    return os.getenv(key, default)

# Plaid Status
st.subheader("📊 Plaid Banking Integration")

plaid_client_id = get_secret_with_nested_support('PLAID_CLIENT_ID', '')
plaid_secret = get_secret_with_nested_support('PLAID_SECRET', '')
plaid_env = get_secret_with_nested_support('PLAID_ENV', 'sandbox')

col1, col2 = st.columns(2)

with col1:
    if plaid_client_id and len(plaid_client_id) == 24:
        st.success("✅ PLAID_CLIENT_ID")
        st.code(f"{plaid_client_id[:8]}... (24 chars)")
    else:
        st.error("❌ PLAID_CLIENT_ID")
        st.code(f"Length: {len(plaid_client_id)}")

with col2:
    if plaid_secret and len(plaid_secret) >= 20:
        st.success("✅ PLAID_SECRET")
        st.code(f"{plaid_secret[:8]}... ({len(plaid_secret)} chars)")
    else:
        st.error("❌ PLAID_SECRET")

st.info(f"🌍 Environment: **{plaid_env}**")

# Test Plaid connection
if st.button("🧪 Test Plaid Connection", key="test_plaid"):
    with st.spinner("Testing Plaid API..."):
        try:
            from plaid.api import plaid_api
            from plaid.configuration import Configuration
            from plaid.api_client import ApiClient
            from plaid.model.link_token_create_request import LinkTokenCreateRequest
            from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
            from plaid.model.products import Products
            from plaid.model.country_code import CountryCode
            
            env_hosts = {
                'sandbox': 'https://sandbox.plaid.com',
                'development': 'https://development.plaid.com',
                'production': 'https://production.plaid.com'
            }
            
            configuration = Configuration(
                host=env_hosts.get(plaid_env, 'https://sandbox.plaid.com'),
                api_key={
                    'clientId': plaid_client_id,
                    'secret': plaid_secret,
                }
            )
            
            api_client = ApiClient(configuration)
            client = plaid_api.PlaidApi(api_client)
            
            request = LinkTokenCreateRequest(
                user=LinkTokenCreateRequestUser(client_user_id="test_user_123"),
                client_name="Bentley Budget Bot",
                products=[Products("transactions")],
                country_codes=[CountryCode("US")],
                language='en',
            )
            
            response = client.link_token_create(request)
            
            st.success("✅ Plaid API Connection Successful!")
            st.json({
                "link_token": response['link_token'][:20] + "...",
                "expiration": str(response['expiration'])
            })
            
        except Exception as e:
            st.error(f"❌ Plaid API Test Failed")
            st.exception(e)

st.markdown("---")

# Alpaca Status
st.subheader("📈 Alpaca Trading Integration")

alpaca_api_key = get_secret_with_nested_support('ALPACA_API_KEY', '')
alpaca_secret = get_secret_with_nested_support('ALPACA_SECRET_KEY', '')
alpaca_paper = get_secret_with_nested_support('ALPACA_PAPER', 'true')

col1, col2 = st.columns(2)

with col1:
    if alpaca_api_key:
        key_type = "Paper (PK)" if alpaca_api_key.startswith('PK') else "Live (AK)"
        st.success(f"✅ ALPACA_API_KEY")
        st.code(f"{alpaca_api_key[:8]}... ({key_type})")
    else:
        st.error("❌ ALPACA_API_KEY")

with col2:
    if alpaca_secret:
        st.success("✅ ALPACA_SECRET_KEY")
        st.code(f"{alpaca_secret[:8]}... ({len(alpaca_secret)} chars)")
    else:
        st.error("❌ ALPACA_SECRET_KEY")

paper_mode = alpaca_paper.lower() == 'true'
mode_text = "🧪 PAPER TRADING (Virtual Money)" if paper_mode else "💰 LIVE TRADING (Real Money)"
st.info(f"Trading Mode: **{mode_text}**")

# Configuration check
if alpaca_api_key:
    if alpaca_api_key.startswith('PK') and not paper_mode:
        st.warning("⚠️ Mismatch: Paper key (PK) but ALPACA_PAPER=false")
    elif alpaca_api_key.startswith('AK') and paper_mode:
        st.warning("⚠️ Mismatch: Live key (AK) but ALPACA_PAPER=true")

# Test Alpaca connection
if st.button("🧪 Test Alpaca Connection", key="test_alpaca"):
    with st.spinner("Testing Alpaca API..."):
        try:
            from frontend.components.alpaca_connector import AlpacaConnector
            
            alpaca = AlpacaConnector(
                api_key=alpaca_api_key,
                secret_key=alpaca_secret,
                paper=paper_mode
            )
            
            account = alpaca.get_account()
            
            if account:
                st.success("✅ Alpaca API Connection Successful!")
                st.json({
                    "account_id": account.get('id', 'N/A')[:16] + "...",
                    "status": account.get('status', 'N/A'),
                    "buying_power": f"${float(account.get('buying_power', 0)):,.2f}",
                    "cash": f"${float(account.get('cash', 0)):,.2f}",
                    "portfolio_value": f"${float(account.get('portfolio_value', 0)):,.2f}",
                    "trading_blocked": account.get('trading_blocked', False)
                })
            else:
                st.error("❌ Failed to retrieve account information")
                
        except Exception as e:
            st.error(f"❌ Alpaca API Test Failed")
            st.exception(e)

st.markdown("---")

# Summary
st.subheader("📋 Summary")

issues = []
if not plaid_client_id or len(plaid_client_id) != 24:
    issues.append("Plaid Client ID invalid/missing")
if not plaid_secret:
    issues.append("Plaid Secret missing")
if not alpaca_api_key:
    issues.append("Alpaca API Key missing")
if not alpaca_secret:
    issues.append("Alpaca Secret missing")

if issues:
    st.error(f"❌ Found {len(issues)} issue(s):")
    for issue in issues:
        st.write(f"  • {issue}")
    
    st.info("💡 Run `python fix_credentials.py` to fix these issues")
else:
    st.success("✅ All credentials configured correctly!")
    st.balloons()
    st.info("👆 Click the test buttons above to verify API connectivity")

# Debug info
with st.expander("🔍 Debug Information"):
    st.write("**Environment Variables:**")
    env_vars = {k: v for k, v in os.environ.items() if any(x in k for x in ['PLAID', 'ALPACA'])}
    st.json({k: f"{v[:8]}..." if v else "NOT SET" for k, v in env_vars.items()})
    
    if hasattr(st, 'secrets'):
        st.write("**Streamlit Secrets Available:**")
        st.write(list(st.secrets.keys()))
