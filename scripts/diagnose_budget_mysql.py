"""
Diagnostic Script for Budget MySQL Connection
==============================================
Checks what database configuration is being used by the Budget Dashboard
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Force reload
load_dotenv(override=True)

def get_secret(key: str, default: str = None) -> str:
    """Get a secret value from Streamlit secrets or environment variables"""
    # Try Streamlit secrets first
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    
    # Fall back to environment variables
    return os.getenv(key, default)


def main():
    st.set_page_config(page_title="Budget MySQL Diagnostic", page_icon="🔍", layout="wide")
    
    st.title("🔍 Budget MySQL Connection Diagnostic")
    
    st.markdown("---")
    
    # Show what the BudgetAnalyzer would use
    st.header("Current Configuration")
    
    # Priority order for each setting
    settings = {
        'Host': [
            ('BUDGET_MYSQL_HOST', get_secret('BUDGET_MYSQL_HOST')),
            ('MYSQL_HOST', get_secret('MYSQL_HOST')),
            ('DB_HOST', get_secret('DB_HOST')),
            ('Default', '127.0.0.1')
        ],
        'Port': [
            ('BUDGET_MYSQL_PORT', get_secret('BUDGET_MYSQL_PORT')),
            ('MYSQL_PORT', get_secret('MYSQL_PORT')),
            ('DB_PORT', get_secret('DB_PORT')),
            ('Default', '3307')
        ],
        'User': [
            ('BUDGET_MYSQL_USER', get_secret('BUDGET_MYSQL_USER')),
            ('MYSQL_USER', get_secret('MYSQL_USER')),
            ('DB_USER', get_secret('DB_USER')),
            ('Default', 'root')
        ],
        'Password': [
            ('BUDGET_MYSQL_PASSWORD', get_secret('BUDGET_MYSQL_PASSWORD')),
            ('MYSQL_PASSWORD', get_secret('MYSQL_PASSWORD')),
            ('DB_PASSWORD', get_secret('DB_PASSWORD')),
            ('Default', '')
        ],
        'Database': [
            ('BUDGET_MYSQL_DATABASE', get_secret('BUDGET_MYSQL_DATABASE')),
            ('MYSQL_DATABASE', get_secret('MYSQL_DATABASE')),
            ('DB_NAME', get_secret('DB_NAME')),
            ('Default', 'mydb')
        ]
    }
    
    # Display priority chain and final value
    for setting_name, priority_chain in settings.items():
        st.subheader(f"🔧 {setting_name}")
        
        # Find first available value
        final_value = None
        source = None
        
        for var_name, value in priority_chain:
            if value:
                if final_value is None:
                    final_value = value
                    source = var_name
                    st.success(f"✅ **{var_name}** = `{value if setting_name != 'Password' else '***' * (len(value) // 3)}` (SELECTED)")
                else:
                    st.info(f"⏭️ {var_name} = `{value if setting_name != 'Password' else '***' * (len(value) // 3)}` (Available but not used)")
            else:
                st.warning(f"❌ {var_name} = Not set")
        
        st.markdown("---")
    
    # Construct final config
    st.header("📋 Final Configuration Used by BudgetAnalyzer")
    
    final_config = {
        'host': get_secret('BUDGET_MYSQL_HOST', get_secret('MYSQL_HOST', get_secret('DB_HOST', '127.0.0.1'))),
        'port': get_secret('BUDGET_MYSQL_PORT', get_secret('MYSQL_PORT', get_secret('DB_PORT', '3307'))),
        'user': get_secret('BUDGET_MYSQL_USER', get_secret('MYSQL_USER', get_secret('DB_USER', 'root'))),
        'password': get_secret('BUDGET_MYSQL_PASSWORD', get_secret('MYSQL_PASSWORD', get_secret('DB_PASSWORD', ''))),
        'database': get_secret('BUDGET_MYSQL_DATABASE', get_secret('MYSQL_DATABASE', get_secret('DB_NAME', 'mydb')))
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.code(f"""
Host:     {final_config['host']}
Port:     {final_config['port']}
User:     {final_config['user']}
Password: {'***' * (len(final_config['password']) // 3) if final_config['password'] else '(empty)'}
Database: {final_config['database']}
        """)
    
    with col2:
        st.markdown("### ✅ Expected for Production:")
        st.code("""
Host:     nozomi.proxy.rlwy.net
Port:     54537
User:     root
Password: cBlIUSygvPJCgPbNKHePJekQlClRamri
Database: mansa_bot
        """)
    
    # Test connection
    st.markdown("---")
    st.header("🔌 Connection Test")
    
    if st.button("Test Connection"):
        try:
            import mysql.connector
            
            with st.spinner("Connecting..."):
                conn = mysql.connector.connect(
                    host=final_config['host'],
                    port=int(final_config['port']),
                    user=final_config['user'],
                    password=final_config['password'],
                    database=final_config['database'],
                    connect_timeout=10
                )
                
                with conn.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()[0]
                
                conn.close()
                
                st.success(f"✅ Connection successful! MySQL version: {version}")
                
        except Exception as e:
            st.error(f"❌ Connection failed: {e}")
            
            # Show fix instructions
            st.markdown("---")
            st.header("🔧 How to Fix")
            
            st.markdown("""
            ### For Streamlit Cloud Production:
            
            1. Go to https://share.streamlit.io/
            2. Find your app and click **⚙️ Settings**
            3. Click **Secrets** in the left sidebar
            4. Add or update these values:
            
            ```toml
            MYSQL_HOST = "nozomi.proxy.rlwy.net"
            MYSQL_PORT = "54537"
            MYSQL_USER = "root"
            MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
            MYSQL_DATABASE = "mansa_bot"
            ```
            
            5. Click **Save** (app will auto-restart)
            
            ### Alternative: Use BUDGET_* Prefix
            
            If you want separate database for budget data:
            
            ```toml
            BUDGET_MYSQL_HOST = "nozomi.proxy.rlwy.net"
            BUDGET_MYSQL_PORT = "54537"
            BUDGET_MYSQL_USER = "root"
            BUDGET_MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
            BUDGET_MYSQL_DATABASE = "mansa_bot"
            ```
            """)


if __name__ == "__main__":
    main()
