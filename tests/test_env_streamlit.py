import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

st.title("🔍 Environment Variables Test")

# Test environment variables
plaid_client_id = os.getenv('PLAID_CLIENT_ID')
mysql_host = os.getenv('BUDGET_MYSQL_HOST')

st.write("**Environment Variables Status:**")
st.write(f"- PLAID_CLIENT_ID: {repr(plaid_client_id)}")
st.write(f"- BUDGET_MYSQL_HOST: {repr(mysql_host)}")

if plaid_client_id and plaid_client_id != 'None':
    st.success("✅ Environment variables loaded correctly!")
else:
    st.error("❌ Environment variables not loaded - showing None")
    st.info("Try restarting your Streamlit app completely")