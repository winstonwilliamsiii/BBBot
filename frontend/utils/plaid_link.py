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
    reload_env(force=True)
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
            print(f"DEBUG: Plaid env vars found: {list(all_env.keys())}")
            raise ValueError(
                f"PLAID_CLIENT_ID not configured.\n"
                f"For Streamlit Cloud: Add to Settings → Secrets\n"
                f"For local: Add to .env file"
            )
        if not self.secret or self.secret == 'your_plaid_secret_here':
            raise ValueError(
                f"PLAID_SECRET not configured.\n"
                f"For Streamlit Cloud: Add to Settings → Secrets\n"
                f"For local: Add to .env file"
            )
        
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
    
    # Initialize session state for manual form
    if 'show_manual_form' not in st.session_state:
        st.session_state.show_manual_form = True
    
    # Check if we have a pending token to process
    if 'plaid_public_token_pending' in st.session_state:
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
                        del st.session_state.plaid_public_token_pending
                        if 'plaid_institution_name' in st.session_state:
                            del st.session_state.plaid_institution_name
                        
                        # Wait a moment then reload
                        import time
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("Failed to exchange token. Please try again.")
                    if 'plaid_public_token_pending' in st.session_state:
                        del st.session_state.plaid_public_token_pending
            except Exception as e:
                st.error(f"Error processing connection: {e}")
                if 'plaid_public_token_pending' in st.session_state:
                    del st.session_state.plaid_public_token_pending
    
    # Try to initialize Plaid Link button
    try:
        # Initialize Plaid manager
        plaid_manager = PlaidLinkManager()
        
        # Create link token
        link_data = plaid_manager.create_link_token(user_id)
        
        if not link_data:
            raise ValueError("Unable to create link token")
        
        link_token = link_data['link_token']
        
        # Render interactive Plaid Link button
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
                    background: #ccc;
                    cursor: not-allowed;
                    transform: none;
                }}
                #status {{
                    margin-top: 12px;
                    font-size: 13px;
                    color: #334155;
                    text-align: center;
                    font-weight: 500;
                }}
            </style>
        </head>
        <body>
            <button id="link-button" onclick="openPlaid()">
                🔗 Connect Your Bank
            </button>
            <div id="status">⏳ Loading...</div>
            
            <script>
                let linkHandler = null;
                
                try {{
                    linkHandler = Plaid.create({{
                        token: '{link_token}',
                        onSuccess: function(public_token, metadata) {{
                            console.log('[Plaid] Success:', metadata.institution.name);
                            alert('✅ Connected!\\n\\nBank: ' + metadata.institution.name + '\\nToken: ' + public_token.substring(0, 30) + '...\\n\\nFill in the form below.');
                            document.getElementById('status').textContent = '✅ Connected to ' + metadata.institution.name;
                        }},
                        onExit: function(err, metadata) {{
                            if (err) {{
                                document.getElementById('status').textContent = '❌ ' + (err.error_message || 'Error');
                            }} else {{
                                document.getElementById('status').textContent = 'Cancelled';
                            }}
                            document.getElementById('link-button').disabled = false;
                        }},
                        onLoad: function() {{
                            document.getElementById('status').textContent = '✅ Ready!';
                            document.getElementById('link-button').disabled = false;
                        }}
                    }});
                }} catch(e) {{
                    document.getElementById('status').textContent = '❌ Error: ' + e.message;
                }}
                
                function openPlaid() {{
                    document.getElementById('link-button').disabled = true;
                    document.getElementById('status').textContent = '⏳ Opening...';
                    try {{
                        linkHandler.open();
                    }} catch(e) {{
                        alert('Error: ' + e.message);
                        document.getElementById('link-button').disabled = false;
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
            """)
            public_token = st.session_state.plaid_public_token
            
            with st.spinner("Connecting to your bank..."):
                # Exchange token
                token_data = plaid_manager.exchange_public_token(public_token)
                
                if token_data:
                    # Save to database
                    institution_name = st.session_state.get('plaid_institution', {}).get('name', 'Bank')
                    success = save_plaid_item(
                        user_id,
                        token_data['item_id'],
                        token_data['access_token'],
                        institution_name
                    )
                    
                    if success:
                        st.success(f"✅ Successfully connected to {institution_name}!")
                        st.balloons()
                        
                        # Clear session state
                        del st.session_state.plaid_public_token
                        if 'plaid_institution' in st.session_state:
                            del st.session_state.plaid_institution
                        
                        st.rerun()
        
        # Render Plaid Link as HTML/JS component with message listener
        plaid_link_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
            <style>
                body {{ margin: 0; padding: 0; }}
                #link-button {{
                    background: linear-gradient(135deg, #06B6D4 0%, #0891B2 100%);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    font-size: 16px;
                    font-weight: 600;
                    border-radius: 8px;
                    cursor: pointer;
                    width: 100%;
                    transition: all 0.3s ease;
                }}
                #link-button:hover {{
                    transform: scale(1.02);
                    box-shadow: 0 4px 12px rgba(6, 182, 212, 0.4);
                }}
                #link-button:active {{
                    transform: scale(0.98);
                }}
                #status {{
                    margin-top: 10px;
                    font-size: 12px;
                    color: #888;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <button id="link-button">
                🔗 Connect Your Bank
            </button>
            <div id="status"></div>
            
            <script>
                console.log('Plaid Link initializing with token:', '{link_token}'.substring(0, 20) + '...');
                
                var linkHandler = Plaid.create({{
                    token: '{link_token}',
                    onSuccess: function(public_token, metadata) {{
                        console.log('✅ Plaid Link success!');
                        console.log('Institution:', metadata.institution.name);
                        console.log('Public token received:', public_token.substring(0, 20) + '...');
                        
                        // Update status
                        document.getElementById('status').textContent = '✅ Connected! Processing...';
                        
                        // Store data in localStorage for Streamlit to read
                        const callbackData = {{
                            public_token: public_token,
                            institution_name: metadata.institution.name,
                            institution_id: metadata.institution.institution_id,
                            accounts: metadata.accounts.map(a => ({{
                                id: a.id,
                                name: a.name,
                                type: a.type,
                                subtype: a.subtype
                            }})),
                            timestamp: new Date().getTime()
                        }};
                        
                        // Use localStorage as bridge to Streamlit
                        localStorage.setItem('plaid_callback', JSON.stringify(callbackData));
                        
                        // Trigger page reload to process the callback
                        window.parent.location.reload();
                    }},
                    onExit: function(err, metadata) {{
                        console.log('Plaid Link exited');
                        if (err != null) {{
                            console.error('❌ Plaid error:', err);
                            document.getElementById('status').textContent = '❌ Error: ' + (err.error_message || 'Connection failed');
                        }} else {{
                            console.log('User closed Plaid Link');
                            document.getElementById('status').textContent = 'Connection cancelled';
                        }}
                    }},
                    onLoad: function() {{
                        console.log('✅ Plaid Link loaded successfully');
                        document.getElementById('status').textContent = 'Ready to connect';
                    }}
                }});
                
                // Open Plaid Link when button is clicked
                document.getElementById('link-button').onclick = function() {{
                    console.log('🔘 Button clicked - opening Plaid Link...');
                    document.getElementById('status').textContent = 'Opening Plaid Link...';
                    try {{
                        linkHandler.open();
                    }} catch(e) {{
                        console.error('❌ Error opening Plaid Link:', e);
                        document.getElementById('status').textContent = '❌ Error: ' + e.message;
                    }}
                }};
                
                console.log('✅ Plaid Link button ready');
            </script>
        </body>
        </html>
        """
        
        # Render component (note: components.html doesn't support 'key' parameter)
        components.html(plaid_link_html, height=80)
        
    except ValueError as e:
        st.warning(str(e))
        st.info("""
        **To enable bank connections:**
        
        1. 📝 Sign up at: https://plaid.com/dashboard
        2. 🔑 Get your credentials (Client ID & Secret)
        3. ⚙️ Update .env file with real values
        4. 🔄 Restart the app
        """)
    except Exception as e:
        st.error(f"Plaid Link error: {e}")
        import traceback
        with st.expander("🐛 Debug Info"):
            st.code(traceback.format_exc())
