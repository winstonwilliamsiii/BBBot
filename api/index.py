#!/usr/bin/env python3
"""
Vercel entry point for Bentley Budget Bot
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import and run the Streamlit app
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", "streamlit_app.py", "--server.port", "8501"]
    stcli.main()