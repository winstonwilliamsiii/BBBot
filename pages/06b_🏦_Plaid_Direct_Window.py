"""
Direct Plaid Link Window - Opens in new tab WITHOUT iframe
===============================================================

This page uses a workaround for the Streamlit iframe issue:
1. When user clicks "Create Link Token", generate the token
2. Generate an HTML file server-side with token EMBEDDED in the HTML
3. Open that HTML file in a new tab using streamlit.js
4. User completes Plaid flow in the new tab (NOT in iframe)
5. Results sent back via postMessage

This is the ONLY reliable way to use Plaid with Streamlit.
"""

import os
from dotenv import load_dotenv
load_dotenv(override=True)

import streamlit as st
import sys
from pathlib import Path
import json
import base64
import time

# Add frontend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import Plaid manager
try:
    from frontend.utils.plaid_link import PlaidLinkManager, save_plaid_item
    PLAID_MANAGER_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ Plaid manager not found: {e}")
    PLAID_MANAGER_AVAILABLE = False

from frontend.utils.styling import apply_custom_styling, add_footer


def generate_plaid_html(link_token: str) -> str:
    """Generate HTML that fetches link_token dynamically with proper async/await"""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plaid Link</title>
    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .plaid-container {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }}
        
        h1 {{
            color: #1f2937;
            margin-bottom: 0.5rem;
            font-size: 1.875rem;
        }}
        
        .subtitle {{
            color: #6b7280;
            margin-bottom: 1.5rem;
            font-size: 1rem;
        }}
        
        .status {{
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .status.loading {{
            background: #dbeafe;
            color: #1e40af;
        }}
        
        .status.success {{
            background: #dcfce7;
            color: #15803d;
        }}
        
        .status.error {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        button {{
            width: 100%;
            padding: 12px 24px;
            background: #0a84ff;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 16px;
            transition: background 0.2s;
        }}
        
        button:hover:not(:disabled) {{
            background: #0066dd;
        }}
        
        button:disabled {{
            background: #d1d5db;
            cursor: not-allowed;
        }}
        
        .spinner {{
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: currentColor;
            animation: spin 0.8s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        code {{
            background: #f3f4f6;
            padding: 0.5rem 0.75rem;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.875rem;
            word-break: break-all;
            display: block;
            margin: 1rem 0;
        }}
    </style>
</head>
<body>
    <div class="plaid-container">
        <h1>🏦 Plaid Link</h1>
        <p class="subtitle">Connect your bank account</p>
        
        <div id="status" class="status loading">
            <span class="spinner"></span>
            <span id="status-text">Initializing Plaid SDK...</span>
        </div>
        
        <button id="open-link" disabled style="margin-top: 1rem;">
            Open Bank Connection
        </button>
        
        <div id="result" style="display: none; margin-top: 2rem;">
            <h3 style="color: #15803d; margin-bottom: 1rem;">✅ Success!</h3>
            <p><strong>Your Public Token:</strong></p>
            <code id="token-display"></code>
            <p style="color: #6b7280; font-size: 0.875rem; line-height: 1.5;">
                This token has been sent to the parent window. You can close this window.
            </p>
        </div>
    </div>

    <script>
        console.log('🔍 Plaid window opened - NOT in iframe');
        
        // Initialize Plaid with proper async/await
        (async function initPlaid() {{
            try {{
                // Method 1: Use embedded token from Python
                const linkToken = '{link_token}';
                
                if (!linkToken || linkToken === 'None' || linkToken.length === 0) {{
                    throw new Error('Link token missing from Python');
                }}
                
                console.log('✅ Link token available (method 1 - embedded):', linkToken.substring(0, 20) + '...');
                
                // Now initialize Plaid with the resolved token
                initializeHandler(linkToken);
                
            }} catch (embeddedError) {{
                console.warn('Embedded token unavailable, trying fetch:', embeddedError.message);
                
                // Method 2: Fallback to fetch from API
                try {{
                    const response = await fetch('/api/plaid/link_token');
                    
                    if (!response.ok) {{
                        throw new Error(`API error: ${{response.status}}`);
                    }}
                    
                    const {{ link_token }} = await response.json();
                    
                    if (!link_token) {{
                        throw new Error('No link_token in API response');
                    }}
                    
                    console.log('✅ Link token fetched from API:', link_token.substring(0, 20) + '...');
                    initializeHandler(link_token);
                    
                }} catch (fetchError) {{
                    console.error('❌ Both methods failed:', fetchError);
                    updateStatus('error', 'Failed to load Plaid: ' + fetchError.message);
                }}
            }}
        }})();
        
        function updateStatus(className, message) {{
            const status = document.getElementById('status');
            status.className = 'status ' + className;
            document.getElementById('status-text').textContent = message;
        }}
        
        function initializeHandler(linkToken) {{
            console.log('Creating Plaid handler with token:', linkToken.substring(0, 20) + '...');
            
            try {{
                const handler = Plaid.create({{
                    token: linkToken,
                    
                    onLoad: function() {{
                        console.log('✅ Plaid Link SDK fully loaded (onLoad callback)');
                        updateStatus('success', '✅ Ready! Click button below.');
                        document.getElementById('open-link').disabled = false;
                    }},
                    
                    onSuccess: function(public_token, metadata) {{
                        console.log('✅ Success:', public_token.substring(0, 20) + '...', metadata);
                        
                        // Update UI
                        updateStatus('success', '✅ Connected!');
                        document.getElementById('result').style.display = 'block';
                        document.getElementById('token-display').textContent = public_token;
                        
                        // Send to parent window
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'plaid_success',
                                public_token: public_token,
                                metadata: metadata
                            }}, '*');
                            console.log('Sent public_token to parent window');
                        }}
                    }},
                    
                    onExit: function(err, metadata) {{
                        console.log('User exited Plaid:', err, metadata);
                        if (err) {{
                            updateStatus('error', '❌ Error or cancelled');
                        }}
                    }},
                    
                    onEvent: function(eventName, metadata) {{
                        console.log('Event:', eventName, metadata);
                    }}
                }});
                
                console.log('✅ Handler created successfully');
                
                // Button click
                document.getElementById('open-link').addEventListener('click', function() {{
                    console.log('Opening Plaid Link...');
                    handler.open();
                }});
                
            }} catch (error) {{
                console.error('❌ Failed to create handler:', error);
                updateStatus('error', 'Error: ' + error.message);
            }}
        }}
    </script>
</body>
</html>"""
    
    return html


# Page config
st.set_page_config(
    page_title="Plaid Direct Window | BBBot",
    page_icon="🏦",
    layout="wide"
)

apply_custom_styling()

st.title("🏦 Plaid Link - Direct Window (No Iframe)")

st.markdown("""
This page opens Plaid Link in a **separate browser tab** (NOT in Streamlit's iframe).
This is the ONLY way to make Plaid Link work reliably with Streamlit.
""")

if not PLAID_MANAGER_AVAILABLE:
    st.error("Plaid manager not available.")
    st.stop()

# Session state
if 'plaid_link_token' not in st.session_state:
    st.session_state.plaid_link_token = None
if 'plaid_public_token' not in st.session_state:
    st.session_state.plaid_public_token = None
if 'plaid_access_token' not in st.session_state:
    st.session_state.plaid_access_token = None
if 'plaid_item_id' not in st.session_state:
    st.session_state.plaid_item_id = None

user_id = st.session_state.get("user_id", "demo_user")
manager = PlaidLinkManager()

st.markdown("---")

# Step 1: Create Link Token
col1, col2 = st.columns([2, 1])

with col1:
    if st.button("🪙 Create Link Token & Open Window", use_container_width=True, type="primary"):
        with st.spinner("Creating link token..."):
            token_data = manager.create_link_token(user_id)
            if token_data and token_data.get('link_token'):
                st.session_state.plaid_link_token = token_data['link_token']
                st.success("✅ Link token created. Window should open...")
                
                # Generate HTML with embedded token
                html_content = generate_plaid_html(token_data['link_token'])
                
                # Store in session for serving
                st.session_state.plaid_html = html_content
                
                # Use JavaScript to open in new window
                st.markdown(f"""
                <script>
                // Small delay to ensure page ready
                setTimeout(function() {{
                    // Create a blob from the HTML
                    const htmlStr = `{html_content.replace("`", r"\`")}`;
                    const blob = new Blob([htmlStr], {{type: 'text/html'}});
                    const url = URL.createObjectURL(blob);
                    
                    // Open in new window
                    const newWindow = window.open(url, 'PlaidLink', 'width=600,height=700,resizable=yes,scrollbars=yes');
                    
                    if (!newWindow) {{
                        alert('⚠️ Popup blocked! Please allow popups for this site.');
                    }} else {{
                        console.log('✅ Plaid window opened');
                        
                        // Listen for messages from the Plaid window
                        window.addEventListener('message', function(event) {{
                            if (event.data && event.data.type === 'plaid_success') {{
                                console.log('Received public token:', event.data.public_token);
                                
                                // Send to Streamlit via custom component
                                if (window.streamlitAddComponentComplete) {{
                                    const msg = {{
                                        'public_token': event.data.public_token,
                                        'metadata': event.data.metadata
                                    }};
                                    // This triggers Streamlit to rerun
                                    console.log('Public token ready for exchange');
                                }}
                            }}
                        }});
                    }}
                }}, 100);
                </script>
                """, unsafe_allow_html=True)
            else:
                st.error("❌ Failed to create link token")

with col2:
    if st.button("🧹 Clear", use_container_width=True):
        st.session_state.plaid_link_token = None
        st.session_state.plaid_public_token = None
        st.rerun()

st.markdown("---")

# Step 2: Exchange Public Token
if st.session_state.plaid_link_token:
    st.markdown("### 🔄 Exchange Public Token")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        public_token = st.text_input(
            "Public Token",
            value=st.session_state.plaid_public_token or "",
            placeholder="Paste token starting with public-sandbox-",
            help="After connecting in the new window, paste the public token here"
        )
    
    with col2:
        st.markdown("")  # Vertical alignment
        exchange_btn = st.button("✅ Exchange", use_container_width=True)
    
    if exchange_btn and public_token:
        st.session_state.plaid_public_token = public_token
        
        with st.spinner("Exchanging token for access token..."):
            result = manager.exchange_public_token(public_token)
            
            if result and result.get('access_token'):
                st.session_state.plaid_access_token = result['access_token']
                st.session_state.plaid_item_id = result['item_id']
                
                st.success("✅ Token exchanged successfully!")
                st.balloons()
                
                # Show result
                st.code(json.dumps(result, indent=2), language="json")
                
                # Try to save
                try:
                    save_plaid_item(
                        user_id,
                        result['item_id'],
                        result['access_token'],
                        "Plaid Sandbox"
                    )
                    st.success("💾 Saved Plaid item to database")
                except Exception as e:
                    st.warning(f"Could not save to DB: {e}")
            else:
                st.error(f"❌ Failed to exchange token: {result}")

# Step 3: Show connected status
if st.session_state.plaid_access_token:
    st.markdown("---")
    st.markdown("### ✅ Connected!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Status", "Connected ✓")
    
    with col2:
        st.metric("Item ID", st.session_state.plaid_item_id[:12] + "...")
    
    with col3:
        if st.button("Get Accounts"):
            try:
                accounts = manager.get_accounts(st.session_state.plaid_access_token)
                st.json(accounts)
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")

# Debug info
with st.expander("🔍 Debug Info"):
    st.write(f"Link Token: {st.session_state.plaid_link_token[:20] if st.session_state.plaid_link_token else 'None'}...")
    st.write(f"Access Token: {st.session_state.plaid_access_token[:20] if st.session_state.plaid_access_token else 'None'}...")
    st.write(f"Item ID: {st.session_state.plaid_item_id or 'None'}")
