#!/bin/bash
# Deploy to Streamlit Cloud Script

# 1. Commit the Plaid fixes
git add frontend/components/plaid_link.py frontend/utils/plaid_link.py
git commit -m "fix: Update Plaid credentials to support nested secrets.toml format

- Updated get_secret() in frontend/components/plaid_link.py to handle nested [plaid] section
- Added _get_secret() helper in frontend/utils/plaid_link.py for nested secrets
- Maintains backward compatibility with flat .env format
- Fixes 'client_id must be properly formatted' error when using Streamlit Cloud"

# 2. Push to GitHub
git push origin main

# 3. Streamlit Cloud will auto-redeploy from GitHub

echo "✅ Changes pushed to GitHub"
echo "📱 Streamlit Cloud will auto-redeploy in a few seconds..."
echo "🌐 Your app will be available at: https://share.streamlit.io/YOUR_USERNAME/BentleyBudgetBot/main/streamlit_app.py"
