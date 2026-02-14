"""
🏦 Plaid Link Standalone Window
================================
Opens Plaid Link in a NEW WINDOW (not iframe) - this is why Link wasn't loading

When you click the button in 06_Plaid_Test.py, this page receives the link_token
and displays Plaid Link in a proper browser context where it CAN load.
"""

import streamlit as st
from urllib.parse import parse_qs, urlparse

st.set_page_config(
    page_title="Plaid Link",
    page_icon="🏦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Get link_token from URL query parameter
# Usage: streamlit-app.com/pages/06a_...?link_token=link-sandbox-xxx&callback_port=8502

query_params = st.query_params

link_token = query_params.get("link_token", [""])[0] if isinstance(query_params.get("link_token"), list) else query_params.get("link_token", "")
callback_port = query_params.get("callback_port", ["8502"])[0] if isinstance(query_params.get("callback_port"), list) else query_params.get("callback_port", "8502")

st.markdown("""
<style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    .container { max-width: 600px; margin: 2rem auto; text-align: center; }
</style>
""", unsafe_allow_html=True)

if not link_token:
    st.error("❌ No link_token provided")
    st.info("""
    This page should be opened from the Plaid Test page with a link_token parameter.
    
    **URL format:**
    ```
    http://localhost:8502/pages/06a_...?link_token=link-sandbox-xxx
    ```
    """)
    st.stop()

st.title("🏦 Plaid Link")
st.markdown("**Complete your bank connection** below")

# Render Plaid Link in a STANDALONE context (not iframe)
import streamlit.components.v1 as components

plaid_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .plaid-container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            margin-top: 0;
            color: #1f2937;
        }}
        .status {{
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
            font-weight: 500;
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
            padding: 10px 20px;
            background: #0a84ff;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            font-size: 16px;
        }}
        button:hover {{
            background: #0066dd;
        }}
        button:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}
    </style>
</head>
<body>
    <div class="plaid-container">
        <h1>🏦 Plaid Link</h1>
        <p>Connect your bank account securely</p>
        
        <div id="status" class="status loading">
            ⏳ Loading Plaid Link...
        </div>
        
        <button id="open-link" disabled>
            Open Bank Connection
        </button>
        
        <div id="result" style="margin-top: 2rem; display: none;"></div>
    </div>

    <script>
        // Token from query parameter
        const linkToken = "{link_token}";
        
        if (!linkToken || linkToken === "None") {{
            document.getElementById('status').className = 'status error';
            document.getElementById('status').innerHTML = '❌ Error: No link token provided';
            document.getElementById('open-link').disabled = true;
        }} else {{
            try {{
                // Initialize Plaid Link
                const handler = Plaid.create({{
                    token: linkToken,
                    onSuccess: function(public_token, metadata) {{
                        // Success! Now exchange the public token
                        document.getElementById('status').className = 'status success';
                        document.getElementById('status').innerHTML = '✅ Successfully connected!';
                        
                        // Send public_token back to parent Streamlit window
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'plaid_success',
                                public_token: public_token,
                                metadata: metadata
                            }}, window.location.origin);
                        }}
                        
                        // Also show the token for manual copy-paste
                        document.getElementById('result').style.display = 'block';
                        document.getElementById('result').innerHTML = `
                            <p><strong>Public Token:</strong></p>
                            <code style="background: #f3f4f6; padding: 8px; border-radius: 4px; display: block; word-break: break-all; margin: 1rem 0;">
                                ${{public_token}}
                            </code>
                            <p style="color: #666; font-size: 0.875rem;">
                                Copy this token and paste it in the Plaid Test page. Then close this window.
                            </p>
                        `;
                    }},
                    onExit: function(err, metadata) {{
                        console.log('Plaid exit', err, metadata);
                        document.getElementById('status').className = 'status error';
                        if (err) {{
                            document.getElementById('status').innerHTML = '❌ Connection cancelled or failed';
                        }} else {{
                            document.getElementById('status').innerHTML = '⚠️ Connection cancelled';
                        }}
                    }},
                    onLoad: function() {{
                        // Link is fully loaded
                        document.getElementById('status').className = 'status success';
                        document.getElementById('status').innerHTML = '✅ Plaid Link loaded. Click the button to open.';
                        document.getElementById('open-link').disabled = false;
                    }},
                    onEvent: function(eventName, metadata) {{
                        console.log('Plaid event:', eventName, metadata);
                    }}
                }});
                
                // Button click handler
                document.getElementById('open-link').onclick = function() {{
                    handler.open();
                }};
                
            }} catch (e) {{
                document.getElementById('status').className = 'status error';
                document.getElementById('status').innerHTML = '❌ Error initializing Plaid: ' + e.message;
            }}
        }}
    </script>
</body>
</html>
"""

components.html(plaid_html, height=600)

st.markdown("---")
st.caption("💡 This window is **not** inside Streamlit's iframe, so Plaid Link can load properly")
