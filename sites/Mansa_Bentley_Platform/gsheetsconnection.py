# example/st_app.py

import streamlit as st
try:
	from streamlit_gsheets import GSheetsConnection
except Exception:
	st.error("Missing dependency 'streamlit-gsheets'. Install it with: pip install streamlit-gsheets")
	raise

url = "https://docs.google.com/spreadsheets/d/1nQahl9pYaEETzbxxjOPYvtPySewuyJOH7Bp_b4Zwt5I/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

data = conn.read(spreadsheet=url, usecols=[0, 1])
st.dataframe(data)
