# Streamlit Cloud Deployment Guide

## 🚀 Deploying to Streamlit Cloud

### Prerequisites
- GitHub account with your repository
- Streamlit Cloud account (https://share.streamlit.io/)

### Step 1: Prepare Your Repository

Ensure these files are in your repo:
- ✅ `streamlit_app.py` (main app file)
- ✅ `requirements.txt` (dependencies)
- ✅ `.streamlit/secrets.toml.example` (secrets template)
- ✅ `.gitignore` includes `.env` and `.streamlit/secrets.toml`

### Step 2: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Click "New app"
3. Select your GitHub repository
4. Choose branch: `main`
5. Main file path: `streamlit_app.py`
6. Click "Deploy"

### Step 3: Configure Secrets

**⚠️ CRITICAL: Add your broker credentials as secrets**

1. Once deployed, click on your app
2. Click "Settings" (⚙️) → "Secrets"
3. Add your credentials in TOML format:

```toml
# Alpaca Trading
ALPACA_API_KEY = "PKAYRIJUWUPO5VVWVTIWDXPRJ3"
ALPACA_SECRET_KEY = "HDegV257ex4j1Wc7C3714mVBLoyircYYMTxTozZKWeaA"
ALPACA_PAPER = "true"

# MetaTrader 5 (if using)
MT5_API_URL = "http://localhost:8000"
MT5_USER = "your_account"
MT5_PASSWORD = "your_password"
MT5_HOST = "MetaQuotes-Demo"
MT5_PORT = "443"

# Interactive Brokers (if using)
IBKR_GATEWAY_URL = "https://localhost:5000"

# Appwrite Backend
APPWRITE_ENDPOINT = "https://cloud.appwrite.io/v1"
APPWRITE_PROJECT_ID = "68869ef500017ca73772"
APPWRITE_API_KEY = "your_api_key"
APPWRITE_DATABASE_ID = "6944821e4f5f5f4f7d10"

# MySQL Database
MYSQL_HOST = "nozomi.proxy.rlwy.net"
MYSQL_PORT = "54537"
MYSQL_USER = "root"
MYSQL_PASSWORD = "your_password"
MYSQL_DATABASE = "mansa_bot"

# Financial Data APIs
TIINGO_API_KEY = "your_key"
ALPHA_VANTAGE_API_KEY = "your_key"

# Plaid Banking
PLAID_CLIENT_ID = "68b8718ec2f428002456a84c"
PLAID_SECRET = "1849c4090173dfbce2bda5453e7048"
PLAID_ENV = "sandbox"
```

4. Click "Save"
5. App will automatically restart with new secrets

### Step 4: Verify Deployment

1. Open your deployed app URL
2. Navigate to "💼 Broker Trading" page
3. Click "Test Alpaca" button
4. Should show: ✅ Configuration source: **Streamlit Secrets**

---

## 🔄 Differences: Local vs Cloud

### Local Development
- Uses `.env` file
- Reads with `os.getenv()`
- Full broker access (MT5, IBKR need local connections)

### Streamlit Cloud
- Uses Streamlit Secrets (in dashboard)
- Reads with `st.secrets.get()`
- Only cloud-accessible brokers work (Alpaca, cloud APIs)

---

## 🛠️ Code Structure for Dual Support

Our code automatically detects the environment:

```python
# Try st.secrets first (Cloud), fall back to environment variables (Local)
try:
    api_key = st.secrets.get("ALPACA_API_KEY", "")
    source = "Streamlit Secrets"
except (AttributeError, FileNotFoundError):
    api_key = os.getenv("ALPACA_API_KEY", "")
    source = "Environment Variables (.env)"
```

---

## 📋 Broker Support by Environment

| Broker | Local | Streamlit Cloud |
|--------|-------|-----------------|
| **Alpaca** | ✅ Full Support | ✅ Full Support |
| **MT5** | ✅ Full Support | ❌ Requires local server |
| **IBKR** | ✅ Full Support | ❌ Requires local Gateway |
| **Binance** (future) | ✅ Full Support | ✅ Full Support |

**Note:** MT5 and IBKR require local servers/gateways, so they only work in local development. Alpaca works everywhere since it's a cloud API.

---

## 🔒 Security Best Practices

### DO ✅
- Use Streamlit Secrets for cloud deployment
- Keep `.env` in `.gitignore`
- Use paper trading credentials for testing
- Rotate API keys regularly
- Use read-only keys where possible

### DON'T ❌
- Never commit `.env` to Git
- Never commit `secrets.toml` to Git
- Don't share API keys in screenshots
- Don't use live trading keys in public repos

---

## 🐛 Troubleshooting

### "Credentials not configured" error on Streamlit Cloud

**Solution:**
1. Check Secrets are added in Streamlit Cloud dashboard
2. Verify TOML format is correct (use quotes around values)
3. Check for typos in secret names
4. Restart app after adding secrets

### Working locally but not in cloud

**Cause:** Using `.env` locally but forgot to add secrets in cloud

**Solution:** Copy all values from `.env` to Streamlit Secrets in TOML format

### Secrets not updating

**Solution:**
1. Click "Save" in secrets editor
2. Wait for automatic restart
3. Hard refresh browser (Ctrl+F5)
4. Check "Manage app" logs for errors

---

## 📱 App URLs

After deployment, you'll get URLs like:
- **Main:** `https://username-repo-name.streamlit.app`
- **Share:** Use this URL to share with others

---

## 🔄 Continuous Deployment

Streamlit Cloud automatically redeploys when you:
- Push to your GitHub repository
- Change secrets in dashboard
- Update Python version in settings

---

## 📊 Monitoring

Check app health:
1. "Manage app" → "Logs" - Real-time logs
2. "Analytics" - Usage statistics
3. "Settings" → "Resources" - CPU/Memory usage

---

## 🆘 Support

- [Streamlit Community](https://discuss.streamlit.io/)
- [Streamlit Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)

---

**Your app is now live and trading-ready! 🎉📈**
