"""
Plaid Link Integration for Bentley Budget Bot
Handles OAuth flow, token exchange, and bank connection
"""

import os
from dotenv import load_dotenv

# Force reload environment variables with cache-busting
load_dotenv(override=True)

# Try to use config_env reload if available
try:
    from config_env import reload_env
    reload_env()
except ImportError:
    pass

import streamlit as st
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
import mysql.connector
from datetime import datetime


def get_secret(key: str, default: str = None) -> str:
    """
    Get a secret value from Streamlit secrets (cloud) or environment variables (local).
    """
    # Try Streamlit secrets first (for Streamlit Cloud)
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    
    # Fall back to environment variables (for local development)
    return os.getenv(key, default)


class PlaidLinkManager:
    """Manages Plaid Link connections and token exchange"""
    
    def __init__(self):
        """Initialize Plaid API client"""
        # Reload environment one more time to be sure
        load_dotenv(override=True)
        
        # Check Streamlit secrets first, then env vars
        self.client_id = get_secret('PLAID_CLIENT_ID', '').strip()
        self.secret = get_secret('PLAID_SECRET', '').strip()
        self.env = get_secret('PLAID_ENV', 'sandbox').strip()
        
        # Debug: Print what we got (masked)
        if not self.client_id or self.client_id == 'your_plaid_client_id_here':
            # Show debug info
            all_env = {k: v for k, v in os.environ.items() if 'PLAID' in k}
            st.error(f"❌ PLAID_CLIENT_ID not configured properly")
            st.info(f"Found env vars: {list(all_env.keys())}")
            st.code(f"CLIENT_ID value: {self.client_id[:8]}... (length: {len(self.client_id)})")
            raise ValueError(
                f"PLAID_CLIENT_ID not configured.\n"
                f"For Streamlit Cloud: Add to Settings → Secrets\n"
                f"For local: Add to .env file"
            )
        if not self.secret or self.secret == 'your_plaid_secret_here':
            st.error(f"❌ PLAID_SECRET not configured properly")
            st.code(f"SECRET value: {self.secret[:8]}... (length: {len(self.secret)})")
            raise ValueError(
                f"PLAID_SECRET not configured.\n"
                f"For Streamlit Cloud: Add to Settings → Secrets\n"
                f"For local: Add to .env file"
            )
        
        # Credentials validated - continue silently
        # Configure Plaid client
        configuration = Configuration(
            host=self._get_plaid_host(),
            api_key={
                'clientId': self.client_id,
                'secret': self.secret,
            }
        )
        
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
    
    def _get_plaid_host(self):
        """Get Plaid API host based on environment"""
        env_hosts = {
            'sandbox': 'https://sandbox.plaid.com',
            'development': 'https://development.plaid.com',
            'production': 'https://production.plaid.com'
        }
        return env_hosts.get(self.env, 'https://sandbox.plaid.com')
    
    def create_link_token(self, user_id: str, client_name: str = "Bentley Budget Bot"):
        """
        Create a link token for Plaid Link initialization
        
        Returns:
            dict: {'link_token': 'link-sandbox-...', 'expiration': '...'}
            None: If token creation fails
        
        Args:
            user_id: Unique identifier for the user
            client_name: Name to display in Plaid Link
            
        Returns:
            dict: Link token response with link_token and expiration
        """
        try:
            request = LinkTokenCreateRequest(
                user=LinkTokenCreateRequestUser(client_user_id=str(user_id)),
                client_name=client_name,
                products=[Products("transactions")],
                country_codes=[CountryCode("US")],
                language='en',
            )
            
            response = self.client.link_token_create(request)
            return {
                'link_token': response['link_token'],
                'expiration': response['expiration'],
            }
        except Exception as e:
            st.error(f"Failed to create link token: {e}")
            return None
    
    def exchange_public_token(self, public_token: str):
        """
        Exchange public token for access token
        
        Args:
            public_token: Public token from Plaid Link
            
        Returns:
            dict: Access token and item ID
        """
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)
            
            return {
                'access_token': response['access_token'],
                'item_id': response['item_id'],
            }
        except Exception as e:
            st.error(f"Failed to exchange token: {e}")
            return None
    
    def get_accounts(self, access_token: str):
        """Get accounts associated with access token"""
        from plaid.model.accounts_get_request import AccountsGetRequest
        
        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            return response['accounts']
        except Exception as e:
            st.error(f"Failed to get accounts: {e}")
            return []
    
    def get_transactions(self, access_token: str, start_date: str, end_date: str):
        """
        Get transactions for a date range
        
        Args:
            access_token: Plaid access token
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        from plaid.model.transactions_get_request import TransactionsGetRequest
        
        try:
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date
            )
            response = self.client.transactions_get(request)
            return response['transactions']
        except Exception as e:
            st.error(f"Failed to get transactions: {e}")
            return []


def save_plaid_item(user_id: str, item_id: str, access_token: str, institution_name: str):
    """Save Plaid item to database"""
    try:
        from frontend.utils.budget_analysis import BudgetAnalyzer
        
        analyzer = BudgetAnalyzer()
        conn = analyzer._get_connection()
        
        if conn:
            cursor = conn.cursor()
            
            # Insert or update plaid_items
            sql = """
                INSERT INTO plaid_items (item_id, user_id, access_token, institution_name)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    access_token = VALUES(access_token),
                    institution_name = VALUES(institution_name),
                    updated_at = CURRENT_TIMESTAMP
            """
            cursor.execute(sql, (item_id, user_id, access_token, institution_name))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return True
    except Exception as e:
        st.error(f"Failed to save Plaid item: {e}")
        return False


def render_plaid_link_button(user_id: str):
    """
    Render Plaid Link button - Simple manual entry workflow
    """
    import streamlit.components.v1 as components
    
    # Initialize all session state variables to prevent AttributeError
    if 'plaid_public_token_pending' not in st.session_state:
        st.session_state.plaid_public_token_pending = None
    if 'plaid_institution_name' not in st.session_state:
        st.session_state.plaid_institution_name = None
    if 'show_manual_form' not in st.session_state:
        st.session_state.show_manual_form = True
    
    # Check if we have a pending token to process
    if st.session_state.plaid_public_token_pending:
        public_token = st.session_state.plaid_public_token_pending
        institution_name = st.session_state.get('plaid_institution_name', 'Bank')
        
        with st.spinner(f"Connecting to {institution_name}..."):
            try:
                # Initialize Plaid manager
                plaid_manager = PlaidLinkManager()
                
                # Exchange token
                token_data = plaid_manager.exchange_public_token(public_token)
                
                if token_data:
                    # Save to database
                    success = save_plaid_item(
                        user_id,
                        token_data['item_id'],
                        token_data['access_token'],
                        institution_name
                    )
                    
                    if success:
                        st.success(f"✅ Successfully connected to {institution_name}!")
                        st.balloons()
                        
                        # Clear pending state
                        st.session_state.plaid_public_token_pending = None
                        st.session_state.plaid_institution_name = None
                        
                        # Wait a moment then reload
                        import time
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("Failed to exchange token. Please try again.")
                    st.session_state.plaid_public_token_pending = None
            except Exception as e:
                st.error(f"Error processing connection: {e}")
                st.session_state.plaid_public_token_pending = None
    
    # Show configuration status
    with st.expander("🔧 Plaid Configuration Status"):
        plaid_client_id = get_secret('PLAID_CLIENT_ID', '')
        plaid_secret = get_secret('PLAID_SECRET', '')
        plaid_env = get_secret('PLAID_ENV', 'sandbox')
        
        if plaid_client_id and len(plaid_client_id) > 10:
            st.success(f"✅ Client ID: {plaid_client_id[:8]}... ({len(plaid_client_id)} chars)")
        else:
            st.error(f"❌ Client ID: Not configured or too short")
        
        if plaid_secret and len(plaid_secret) > 10:
            st.success(f"✅ Secret: {plaid_secret[:8]}... ({len(plaid_secret)} chars)")
        else:
            st.error(f"❌ Secret: Not configured or too short")
        
        st.info(f"🌍 Environment: {plaid_env}")
    
    # Try to initialize Plaid Link button
    try:
        # Initialize Plaid manager
        plaid_manager = PlaidLinkManager()
        
        # Create link token
        link_data = plaid_manager.create_link_token(user_id)
        
        if not link_data:
            raise ValueError("Unable to create link token")
        
        link_token = link_data.get('link_token')
        if not link_token:
            raise ValueError("Link token not found in response")
        
        # Render interactive Plaid Link button with enhanced error handling
        plaid_link_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 15px;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                }}
                #link-button {{
                    background: linear-gradient(135deg, #06B6D4 0%, #0891B2 100%);
                    color: white;
                    border: none;
                    padding: 14px 28px;
                    font-size: 16px;
                    font-weight: 600;
                    border-radius: 8px;
                    cursor: pointer;
                    width: 100%;
                    transition: all 0.2s ease;
                    box-shadow: 0 2px 8px rgba(6, 182, 212, 0.3);
                }}
                #link-button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(6, 182, 212, 0.5);
                }}
                #link-button:disabled {{
                    background: #999;
                    cursor: not-allowed;
                    transform: none;
                    opacity: 0.6;
                }}
                #status {{
                    margin-top: 12px;
                    font-size: 13px;
                    color: #334155;
                    text-align: center;
                    font-weight: 500;
                    padding: 8px;
                    border-radius: 4px;
                }}
                .status-error {{
                    background: #fee;
                    color: #c00;
                }}
                .status-success {{
                    background: #efe;
                    color: #060;
                }}
            </style>
        </head>
        <body>
            <button id="link-button" onclick="openPlaid()" disabled>
                🔗 Connect Your Bank
            </button>
            <div id="status">⏳ Initializing Plaid...</div>
            
            <script>
                console.log('[Plaid] Starting initialization...');
                console.log('[Plaid] Token: {link_token[:20]}...');
                
                let linkHandler = null;
                const statusEl = document.getElementById('status');
                const buttonEl = document.getElementById('link-button');
                
                // Check if Plaid SDK loaded
                if (typeof Plaid === 'undefined') {{
                    console.error('[Plaid] SDK not loaded!');
                    statusEl.textContent = '❌ Plaid SDK failed to load';
                    statusEl.className = 'status-error';
                    return;
                }}
                
                try {{
                    console.log('[Plaid] Creating handler...');
                    linkHandler = Plaid.create({{
                        token: '{link_token}',
                        onSuccess: function(public_token, metadata) {{
                            console.log('[Plaid] ✅ Success!', metadata);
                            statusEl.textContent = '✅ Connected to ' + metadata.institution.name + '!';
                            statusEl.className = 'status-success';
                            
                            // Show alert with token
                            alert(
                                '✅ Bank Connected Successfully!\\n\\n' +
                                'Bank: ' + metadata.institution.name + '\\n' +
                                'Public Token: ' + public_token.substring(0, 30) + '...\\n\\n' +
                                'Copy this token and paste it below:'
                            );
                            
                            // Auto-fill if possible (browser security may block)
                            try {{
                                parent.postMessage({{
                                    type: 'PLAID_SUCCESS',
                                    public_token: public_token,
                                    institution: metadata.institution
                                }}, '*');
                            }} catch(e) {{
                                console.warn('[Plaid] Could not post message:', e);
                            }}
                        }},
                        onExit: function(err, metadata) {{
                            console.log('[Plaid] Exit:', err, metadata);
                            if (err) {{
                                console.error('[Plaid] Error:', err);
                                statusEl.textContent = '❌ ' + (err.error_message || err.display_message || 'Connection failed');
                                statusEl.className = 'status-error';
                            }} else {{
                                statusEl.textContent = 'Connection cancelled';
                            }}
                            buttonEl.disabled = false;
                        }},
                        onLoad: function() {{
                            console.log('[Plaid] ✅ Loaded successfully');
                            statusEl.textContent = '✅ Ready to connect!';
                            buttonEl.disabled = false;
                        }},
                        onEvent: function(eventName, metadata) {{
                            console.log('[Plaid] Event:', eventName, metadata);
                        }}
                    }});
                    console.log('[Plaid] Handler created successfully');
                }} catch(e) {{
                    console.error('[Plaid] Initialization error:', e);
                    statusEl.textContent = '❌ Error: ' + e.message;
                    statusEl.className = 'status-error';
                    buttonEl.disabled = true;
                }}
                
                function openPlaid() {{
                    console.log('[Plaid] Opening Link...');
                    buttonEl.disabled = true;
                    statusEl.textContent = '⏳ Opening Plaid Link...';
                    
                    if (!linkHandler) {{
                        alert('Plaid Link is not initialized. Please refresh the page.');
                        buttonEl.disabled = false;
                        return;
                    }}
                    
                    try {{
                        linkHandler.open();
                    }} catch(e) {{
                        console.error('[Plaid] Open error:', e);
                        alert('Error opening Plaid Link: ' + e.message);
                        statusEl.textContent = '❌ Failed to open';
                        statusEl.className = 'status-error';
                        buttonEl.disabled = false;
                    }}
                }}
            </script>
        </body>
        </html>
        """
        
        st.markdown("### 🏦 Connect Your Bank")
        components.html(plaid_link_html, height=120)
        
    except ValueError as e:
        # Show error but still render form
        st.warning(f"⚠️ {str(e)}")
        st.info("💡 You can still manually enter connection details below.")
        
    except Exception as e:
        # Show error but still render form
        st.error(f"⚠️ Plaid Link unavailable: {str(e)}")
        st.info("💡 Fill in connection details manually:")
    
    # Always show the manual entry form
    st.markdown("---")
    st.markdown("### 📝 Enter Connection Details")
    
    with st.form("plaid_connection_form", clear_on_submit=False):
        st.info("💡 After connecting above, or if you have the token from elsewhere, enter it here:")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            institution = st.text_input(
                "Bank Name",
                placeholder="e.g., Chase, Bank of America",
                help="Name of your bank"
            )
        
        with col2:
            public_token = st.text_input(
                "Public Token",
                type="password",
                placeholder="public-sandbox-...",
                help="Token from Plaid connection"
            )
        
        submitted = st.form_submit_button(
            "✅ Complete Connection",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if not public_token or not institution:
                st.error("⚠️ Please fill in both fields")
            elif not public_token.startswith(('public-', 'access-')):
                st.error("⚠️ Invalid token format. Token should start with 'public-'")
            else:
                st.session_state.plaid_public_token_pending = public_token
                st.session_state.plaid_institution_name = institution
                st.rerun()
    
    # Help section
    with st.expander("❓ Need Help?"):
        st.markdown("""
        **How to connect:**
        
        1. **Click blue button above** to open Plaid Link
        2. **Select bank** (Sandbox: "Chase" or "Bank of America")
        3. **Login** with:
           - Username: `user_good`
           - Password: `pass_good`
        4. **Copy token** from alert
        5. **Paste below** and click Submit
        
        **Troubleshooting:**
        - Check browser console (F12) for errors
        - Disable popup blockers
        - Token starts with "public-sandbox-"
        """)
