import streamlit as st
import pymysql

st.title("🔍 Database Connection Test - Streamlit Secrets")

try:
    # Test Streamlit secrets configuration
    if "mysql" in st.secrets:
        st.success("✅ MySQL secrets found in Streamlit configuration")
        
        db_config = st.secrets["mysql"]
        
        st.write("**Database Configuration:**")
        st.write(f"- Host: {db_config['host']}")
        st.write(f"- Port: {db_config['port']}")
        st.write(f"- User: {db_config['user']}")
        st.write(f"- Database: {db_config['database']}")
        
        # Test connection
        with st.spinner("Testing database connection..."):
            conn = pymysql.connect(
                host=db_config["host"],
                port=int(db_config["port"]),
                user=db_config["user"],
                password=db_config["password"],
                database=db_config["database"]
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            st.success("✅ Database connection successful!")
            st.balloons()
    else:
        st.error("❌ MySQL secrets not configured")
        st.info("""
        **To configure secrets for Streamlit Cloud:**
        
        1. Go to https://share.streamlit.io/
        2. Find your app and click Settings → Secrets
        3. Add this configuration:
        
        ```toml
        [mysql]
        host = "your_host"
        port = 3306
        user = "your_user" 
        password = "your_password"
        database = "your_database"
        ```
        """)
        
except Exception as e:
    st.error(f"❌ Connection failed: {e}")
    
# Also test Plaid secrets
st.markdown("---")
st.subheader("🏦 Plaid Configuration Test")

try:
    if "PLAID_CLIENT_ID" in st.secrets:
        st.success("✅ Plaid secrets configured")
        plaid_env = st.secrets.get("PLAID_ENV", "sandbox")
        st.write(f"Environment: {plaid_env}")
    else:
        st.warning("⚠️ Plaid secrets not configured")
        st.info("""
        Add these to your Streamlit secrets:
        ```toml
        PLAID_CLIENT_ID = "your_client_id"
        PLAID_SECRET = "your_secret"
        PLAID_ENV = "sandbox"
        ```
        """)
except Exception as e:
    st.error(f"Error checking Plaid secrets: {e}")