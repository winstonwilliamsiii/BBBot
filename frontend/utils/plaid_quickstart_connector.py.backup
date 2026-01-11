"""
Plaid Quickstart Backend Connector
Connects Streamlit frontend to local Plaid Docker sample backend
"""

import requests
import streamlit as st
import json
from typing import Optional, Dict, Any

class PlaidQuickstartClient:
    """Client for Plaid Quickstart Docker backend"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize client for Plaid quickstart backend
        
        Args:
            base_url: Base URL of the Docker container (default: http://localhost:8000)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> bool:
        """Check if the backend is running"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def create_link_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Create a link token via the quickstart backend
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            dict: {'link_token': '...', 'expiration': '...'} or None
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/create_link_token",
                json={"user_id": user_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'link_token': data.get('link_token'),
                    'expiration': data.get('expiration')
                }
            else:
                st.error(f"Backend error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to Plaid backend. Is Docker container running?")
            st.code("""
# Start the Plaid quickstart:
cd plaid-quickstart
docker-compose up

# Or if using npm:
npm start
""")
            return None
        except Exception as e:
            st.error(f"Error creating link token: {e}")
            return None
    
    def exchange_public_token(self, public_token: str) -> Optional[Dict[str, Any]]:
        """
        Exchange public token for access token
        
        Args:
            public_token: Public token from Plaid Link
            
        Returns:
            dict: {'access_token': '...', 'item_id': '...'} or None
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/set_access_token",
                json={"public_token": public_token},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'access_token': data.get('access_token'),
                    'item_id': data.get('item_id')
                }
            else:
                st.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            st.error(f"Error exchanging token: {e}")
            return None
    
    def get_transactions(self, start_date: str, end_date: str) -> Optional[list]:
        """
        Get transactions from the backend
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            list: Transaction objects or None
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/transactions",
                json={
                    "start_date": start_date,
                    "end_date": end_date
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('transactions', [])
            else:
                st.error(f"Failed to get transactions: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Error getting transactions: {e}")
            return None
    
    def get_accounts(self) -> Optional[list]:
        """Get connected accounts"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/accounts",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('accounts', [])
            else:
                return None
                
        except Exception as e:
            st.error(f"Error getting accounts: {e}")
            return None


def render_quickstart_plaid_link(user_id: str, backend_url: str = "http://localhost:8000"):
    """
    Render Plaid Link connected to quickstart backend
    
    Args:
        user_id: User identifier
        backend_url: URL of the Plaid quickstart backend
    """
    import streamlit.components.v1 as components
    
    # Initialize client
    client = PlaidQuickstartClient(backend_url)
    
    # Check backend health
    st.markdown("### 🔌 Backend Status")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if client.health_check():
            st.success("✅ Backend Running")
        else:
            st.error("❌ Backend Offline")
            st.code(f"Expected at: {backend_url}")
            st.info("""
**Start the backend:**
```bash
cd plaid-quickstart
docker-compose up
```
Or check the port (might be 8080 or 3000)
""")
            return
    
    with col2:
        st.caption(f"Endpoint: {backend_url}")
    
    # Initialize session state
    if 'plaid_public_token' not in st.session_state:
        st.session_state.plaid_public_token = None
    if 'plaid_access_token' not in st.session_state:
        st.session_state.plaid_access_token = None
    if 'plaid_institution' not in st.session_state:
        st.session_state.plaid_institution = None
    
    # Create link token
    st.markdown("---")
    st.markdown("### 🏦 Connect Your Bank")
    
    with st.spinner("Generating link token..."):
        link_data = client.create_link_token(user_id)
    
    if not link_data:
        st.error("Failed to create link token. Check backend logs.")
        return
    
    link_token = link_data['link_token']
    st.success(f"✅ Link token generated: {link_token[:30]}...")
    
    # Render Plaid Link using modern react-plaid-link approach
    plaid_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.plaid.com/link/stable/link-initialize.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }}
            #link-button {{
                background: linear-gradient(135deg, #06B6D4 0%, #0891B2 100%);
                color: white;
                border: none;
                padding: 16px 32px;
                font-size: 16px;
                font-weight: 600;
                border-radius: 8px;
                cursor: pointer;
                width: 100%;
                box-shadow: 0 4px 12px rgba(6, 182, 212, 0.3);
                transition: all 0.2s ease;
            }}
            #link-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(6, 182, 212, 0.5);
            }}
            #link-button:disabled {{
                background: #999;
                cursor: not-allowed;
                opacity: 0.7;
                transform: none;
            }}
            #status {{
                margin-top: 15px;
                padding: 12px;
                border-radius: 6px;
                text-align: center;
                font-size: 14px;
                font-weight: 500;
            }}
            .success {{ background: #d1fae5; color: #065f46; }}
            .error {{ background: #fee2e2; color: #991b1b; }}
            .info {{ background: #dbeafe; color: #1e40af; }}
            .spinner {{
                border: 3px solid #f3f3f3;
                border-top: 3px solid #3498db;
                border-radius: 50%;
                width: 16px;
                height: 16px;
                animation: spin 1s linear infinite;
                display: inline-block;
                margin-right: 8px;
                vertical-align: middle;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <button id="link-button" disabled>
            <span class="spinner"></span> Initializing Plaid Link...
        </button>
        <div id="status" class="info">Connecting to Plaid...</div>
        
        <script>
            console.log('[Plaid] Link token:', '{link_token}'.substring(0, 30) + '...');
            
            const statusEl = document.getElementById('status');
            const buttonEl = document.getElementById('link-button');
            let linkHandler = null;
            
            // Initialize Plaid Link
            (function initPlaid() {{
                try {{
                    linkHandler = Plaid.create({{
                        token: '{link_token}',
                        onLoad: function() {{
                            console.log('[Plaid] Link loaded successfully');
                            buttonEl.disabled = false;
                            buttonEl.innerHTML = '🔗 Open Plaid Link';
                            statusEl.textContent = 'Ready to connect your bank';
                            statusEl.className = 'info';
                        }},
                        onSuccess: async function(public_token, metadata) {{
                            console.log('[Plaid] Success!', {{
                                institution: metadata.institution,
                                accounts: metadata.accounts.length
                            }});
                            
                            buttonEl.disabled = true;
                            buttonEl.innerHTML = '⏳ Processing...';
                            statusEl.innerHTML = '<span class="spinner"></span> Exchanging token...';
                            statusEl.className = 'info';
                            
                            try {{
                                // Exchange public token for access token
                                const response = await fetch('{backend_url}/api/set_access_token', {{
                                    method: 'POST',
                                    headers: {{ 
                                        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
                                    }},
                                    body: 'public_token=' + encodeURIComponent(public_token)
                                }});
                                
                                if (!response.ok) {{
                                    throw new Error('HTTP ' + response.status);
                                }}
                                
                                const data = await response.json();
                                console.log('[Plaid] Token exchanged:', {{
                                    item_id: data.item_id,
                                    access_token: data.access_token ? 'present' : 'missing'
                                }});
                                
                                if (data.access_token && data.item_id) {{
                                    buttonEl.innerHTML = '✅ Connected!';
                                    statusEl.textContent = '✅ Connected to ' + metadata.institution.name + '!';
                                    statusEl.className = 'success';
                                    
                                    // Notify Streamlit
                                    window.parent.postMessage({{
                                        type: 'PLAID_SUCCESS',
                                        public_token: public_token,
                                        access_token: data.access_token,
                                        item_id: data.item_id,
                                        institution: metadata.institution.name,
                                        accounts: metadata.accounts
                                    }}, '*');
                                }} else {{
                                    throw new Error('Missing access_token or item_id in response');
                                }}
                            }} catch (err) {{
                                console.error('[Plaid] Exchange error:', err);
                                buttonEl.disabled = false;
                                buttonEl.innerHTML = '🔗 Try Again';
                                statusEl.textContent = '❌ Token exchange failed: ' + err.message;
                                statusEl.className = 'error';
                            }}
                        }},
                        onExit: function(err, metadata) {{
                            buttonEl.disabled = false;
                            buttonEl.innerHTML = '🔗 Open Plaid Link';
                            
                            if (err) {{
                                console.error('[Plaid] Exit with error:', err);
                                statusEl.textContent = '❌ Error: ' + (err.error_message || err.display_message || 'Connection failed');
                                statusEl.className = 'error';
                            }} else {{
                                console.log('[Plaid] User exited');
                                statusEl.textContent = 'Connection cancelled - Click button to try again';
                                statusEl.className = 'info';
                            }}
                        }},
                        onEvent: function(eventName, metadata) {{
                            console.log('[Plaid] Event:', eventName, metadata);
                        }}
                    }});
                    
                    console.log('[Plaid] Handler created, waiting for onLoad...');
                    
                }} catch (err) {{
                    console.error('[Plaid] Initialization error:', err);
                    buttonEl.disabled = false;
                    buttonEl.innerHTML = '❌ Failed to Initialize';
                    statusEl.textContent = '❌ Failed to initialize Plaid Link: ' + err.message;
                    statusEl.className = 'error';
                }}
            }})();
            
            // Open Plaid Link when button clicked
            buttonEl.addEventListener('click', function() {{
                if (!linkHandler) {{
                    console.error('[Plaid] Handler not initialized');
                    statusEl.textContent = '❌ Plaid Link not ready - please refresh';
                    statusEl.className = 'error';
                    return;
                }}
                console.log('[Plaid] Opening Link...');
                statusEl.textContent = 'Opening Plaid Link...';
                statusEl.className = 'info';
                linkHandler.open();
            }});
        </script>
    </body>
    </html>
    """
    
    components.html(plaid_html, height=180)
    
    # Show test credentials
    with st.expander("🔐 Sandbox Test Credentials"):
        st.info("""
**For Sandbox Testing:**

**Bank:** Chase (or Bank of America)

**Credentials:**
- Username: `user_good`
- Password: `pass_good`
- MFA: `1234` (if prompted)
""")
    
    # Show transactions if connected
    if st.session_state.get('plaid_access_token'):
        st.markdown("---")
        st.markdown("### 📊 Fetch Transactions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Start Date", value=None)
        
        with col2:
            end_date = st.date_input("End Date", value=None)
        
        if st.button("Fetch Transactions", type="primary"):
            if start_date and end_date:
                with st.spinner("Fetching transactions..."):
                    transactions = client.get_transactions(
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d")
                    )
                    
                    if transactions:
                        st.success(f"✅ Found {len(transactions)} transactions")
                        
                        # Display in table
                        import pandas as pd
                        df = pd.DataFrame(transactions)
                        st.dataframe(df)
                    else:
                        st.warning("No transactions found")
            else:
                st.error("Please select both start and end dates")


if __name__ == "__main__":
    # Test the connector
    st.set_page_config(page_title="Plaid Quickstart Test", layout="wide")
    
    st.title("🏦 Plaid Quickstart Integration Test")
    
    # Backend URL config
    backend_url = st.text_input(
        "Backend URL",
        value="http://localhost:8000",
        help="URL where your Plaid quickstart Docker container is running"
    )
    
    user_id = st.text_input("User ID", value="test_user_123")
    
    if st.button("Test Connection"):
        render_quickstart_plaid_link(user_id, backend_url)
