#!/bin/sh

# Vercel startup script
echo "Starting Bentley Budget Bot..."
exec streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false