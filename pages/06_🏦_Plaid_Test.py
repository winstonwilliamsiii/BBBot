"""
Plaid Integration Test Page
============================
Test your Plaid API connection using Direct API integration.

Features:
- Link token generation
- Bank connection flow via Plaid Link
- Token exchange
- Account data retrieval
- Transaction fetching

Access via BBBot multi-page app:
    http://localhost:8501/
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

import streamlit as st
import sys
from pathlib import Path

# Add frontend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Direct Plaid API manager
try:
    from frontend.utils.plaid_link import PlaidLinkManager, save_plaid_item
    PLAID_MANAGER_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ Plaid module not available: {e}")
    PLAID_MANAGER_AVAILABLE = False

from frontend.utils.styling import apply_custom_styling, add_footer

# Page config
st.set_page_config(
    page_title="Plaid Integration | BBBot",
    page_icon="🏦",
    layout="wide"
)

# Apply custom styling
apply_custom_styling()

st.title("🏦 Plaid Banking Integration")

# Connected badge (shown when access token exists)
try:
    if st.session_state.get('access_token'):
        badge_style = (
            "display:inline-block;padding:4px 10px;"
            "border-radius:999px;background:#16a34a;"
            "color:white;font-weight:600;font-size:0.9rem;"
        )
        st.markdown(
            f'<div style="{badge_style}">Connected ✓</div>',
            unsafe_allow_html=True,
        )
except Exception:
    pass

st.markdown("""
Connect your bank accounts securely using **Plaid Link**.

### How it works:
1. ✅ Click "Create Link Token" to initialize Plaid
2. ✅ Click "Open Plaid Link" to select your bank
3. ✅ Login with your bank credentials (Sandbox: user_good / pass_good)
4. ✅ Copy the public token and exchange it for access
5. ✅ View your connected accounts and transactions
""")

st.markdown("---")

# Check if Plaid manager is available
if not PLAID_MANAGER_AVAILABLE:
    st.error("❌ Plaid manager not available. Check installation.")
    st.stop()

# Configuration
st.markdown("## ⚙️ Configuration")

# Debug: Show secrets availability
with st.expander("🔍 Debug: Credentials Status"):
    st.write("**Checking credential sources...**")
    if hasattr(st, 'secrets'):
        secret_keys = list(st.secrets.keys()) if hasattr(st.secrets, 'keys') else []
        st.success(f"✅ st.secrets available ({len(secret_keys)} keys)")
        plaid_keys = [k for k in secret_keys if 'PLAID' in k.upper()]
        if plaid_keys:
            st.write(f"Found Plaid keys: {plaid_keys}")
        else:
            st.warning("⚠️ No PLAID_* keys found in secrets")
            st.write(f"Available keys: {secret_keys}")
    else:
        st.error("❌ st.secrets not available")
    
    # Check env vars
    env_plaid_keys = [k for k in os.environ.keys() if 'PLAID' in k]
    if env_plaid_keys:
        st.write(f"Environment PLAID vars: {env_plaid_keys}")
    else:
        st.write("No PLAID_* environment variables found")

user_id = st.text_input("User ID", value="winston_test_123", help="Unique identifier for this connection")

manager = PlaidLinkManager()

# Session state for Plaid flow
if 'link_token' not in st.session_state:
    st.session_state.link_token = None
if 'public_token' not in st.session_state:
    st.session_state.public_token = None
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'item_id' not in st.session_state:
    st.session_state.item_id = None

st.markdown("---")
st.markdown("## 🔑 Step 1: Create Link Token")

colA, colB = st.columns([1, 1])

with colA:
    if st.button("🪙 Create Link Token", use_container_width=True):
        with st.spinner("Creating link token via Plaid API..."):
            token = manager.create_link_token(user_id)
            if token and token.get('link_token'):
                st.session_state.link_token = token.get('link_token')
                st.success("✅ Link token created")
            else:
                st.error(
                    "❌ Failed to create link token. "
                    "Check your Plaid credentials in .env file."
                )

with colB:
    if st.button("🧹 Clear Session", use_container_width=True):
        st.session_state.link_token = None
        st.session_state.public_token = None
        st.session_state.access_token = None
        st.session_state.item_id = None
        st.success("Session cleared")
        st.rerun()

# Render Plaid Link minimal UI when we have a link_token
if st.session_state.link_token:
    st.markdown("---")
    st.markdown("## 🚪 Step 2: Open Plaid Link")
    import streamlit.components.v1 as components
    plaid_html = f"""
    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js">
    </script>
    <button id="open-link" style="
        padding:10px 16px;
        border-radius:6px;
        background:#0a84ff;
        color:white;
        border:none;
        cursor:pointer;
        font-size:16px;
    ">Open Plaid Link</button>
    <script>
      var handler = Plaid.create({{
        token: '{st.session_state.link_token}',
        onSuccess: function(public_token, metadata) {{
          alert('PUBLIC_TOKEN:' + public_token);
        }},
        onExit: function(err, metadata) {{
          console.log('Plaid exit', err, metadata);
        }}
      }});
      document.getElementById('open-link').onclick = function() {{
        handler.open();
      }};
    </script>
    """
    components.html(plaid_html, height=120)

    st.caption(
        "On success, an alert will show your public token. "
        "Copy it and paste below."
    )

    st.markdown("---")
    st.markdown("## 🔄 Step 3: Exchange Public Token")
    st.session_state.public_token = st.text_input(
        "Public Token",
        value=st.session_state.public_token or "",
        help="Paste token starting with public-sandbox-"
    )
    institution_name = st.text_input(
        "Institution Name (optional)",
        value="Plaid Sandbox"
    )
    if st.button(
        "✅ Exchange Token",
        use_container_width=True,
        disabled=not st.session_state.public_token
    ):
        with st.spinner("Exchanging token..."):
            result = manager.exchange_public_token(
                st.session_state.public_token
            )
            if result and result.get('access_token'):
                st.session_state.access_token = result['access_token']
                st.session_state.item_id = result['item_id']
                st.success("✅ Token exchanged and bank connected")
                try:
                    st.balloons()
                    st.snow()
                    try:
                        st.toast("🎉 Bank connected!", icon="✅")
                    except Exception:
                        pass
                except Exception:
                    pass
                st.code(result)
                try:
                    save_plaid_item(
                        user_id,
                        result['item_id'],
                        result['access_token'],
                        institution_name
                    )
                    st.success("💾 Saved Plaid item to database")
                except Exception as e:
                    st.warning(f"Could not save to DB: {e}")
            else:
                st.error("❌ Failed to exchange token")

if st.session_state.access_token:
    st.markdown("---")
    st.markdown("## 🧾 Step 4: View Accounts")
    try:
        accounts = manager.get_accounts(st.session_state.access_token)
        if accounts:
            st.success(f"Found {len(accounts)} accounts")
            st.json(accounts)
        else:
            st.info("No accounts returned or error from API")
    except Exception as e:
        st.warning(f"Accounts fetch error: {e}")

    # Connection status and quick clear
    st.markdown("---")
    colS1, colS2 = st.columns([1, 1])
    with colS1:
        st.metric("Connection Status", "Connected", delta="✓")
        st.caption(f"Item ID: {st.session_state.item_id}")
    with colS2:
        if st.button(
            "🧹 Clear Session (Finish)",
            use_container_width=True
        ):
            st.session_state.link_token = None
            st.session_state.public_token = None
            st.session_state.access_token = None
            st.session_state.item_id = None
            st.success("Session cleared. You can start a new test.")
            st.rerun()

# Instructions
st.markdown("---")
st.markdown("## 📖 How to Use")

tab1, tab2 = st.tabs(["Quick Start", "Troubleshooting"])

with tab1:
    st.markdown("""
### Quick Start Guide

1. **Create Link Token:** Click the button above to initialize Plaid

2. **Open Plaid Link:** Click "Open Plaid Link" button

3. **Select Bank:** Choose a bank (e.g., Chase, Bank of America)

4. **Login Credentials (Sandbox):**
   - Username: `user_good`
   - Password: `pass_good`

5. **Copy Token:** After success, copy the public token from the alert

6. **Exchange Token:** Paste and exchange for permanent access

7. **View Data:** See your connected accounts and balances

### Credentials Setup

Make sure your `.env` file has:
```bash
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ENV=sandbox
```

Get credentials from: https://dashboard.plaid.com/team/keys
""")

with tab2:
    st.markdown("""
### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Link token failed" | Check PLAID_CLIENT_ID and PLAID_SECRET in .env |
| "No credentials" | Ensure .env file exists in project root |
| Plaid Link doesn't open | Check browser console (F12) for errors |
| "Invalid credentials" | Verify sandbox credentials at Plaid dashboard |
| Module import error | Run: `pip install plaid-python` |

### Get Plaid Credentials

1. Sign up at: https://dashboard.plaid.com/signup
2. Navigate to: Team Settings → Keys
3. Copy your sandbox credentials
4. Add to `.env` file in project root

### Test Credentials

Run diagnostic:
```bash
python quick_plaid_test.py
```
""")

# Debug info
with st.expander("🐛 Debug Information"):
    st.json({
        "user_id": user_id,
        "has_link_token": bool(st.session_state.get('link_token')),
        "has_access_token": bool(st.session_state.get('access_token')),
        "session_state": dict(st.session_state)
    })

# Footer
st.markdown("---")
st.caption("🏦 Secure bank connections powered by Plaid")

# Add BBBot footer
add_footer()

