# Streamlit Cloud Secrets Configuration

## ⚠️ CRITICAL: Kalshi API Credentials

The Kalshi RSA private key is **NOT** stored in version control. You must add it to Streamlit Cloud Secrets manually.

## Setup Instructions

1. Navigate to [Streamlit Cloud](https://share.streamlit.io/)
2. Select your app: **bbbot305**
3. Click **Settings** ⚙️
4. Select **Secrets** tab
5. Add the following:

```toml
# Kalshi Prediction Markets API (RSA Authentication)
KALSHI_API_KEY_ID = "a6991a4a-d654-4bb5-85f9-3884ae105134"
KALSHI_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
[PASTE YOUR FULL RSA PRIVATE KEY HERE - 27 LINES]
-----END RSA PRIVATE KEY-----"""
```

## Security Notes

- ✅ Private key is in `.gitignore` and removed from git tracking
- ✅ Use triple quotes `"""` for multi-line PEM format
- ✅ Key format: PEM with header/footer lines
- ✅ No spaces or modifications to the key content

## Verification

After adding secrets:
1. Streamlit Cloud will auto-redeploy (2-3 minutes)
2. Navigate to **Prediction Analytics** page
3. Debug panel should show: ✅ Authenticated: True
4. Portfolio should display your actual Kalshi positions

## Reference

- Setup guide: [KALSHI_API_SETUP.md](KALSHI_API_SETUP.md)
- API endpoint: https://trading-api.kalshi.com
- Authentication: RSA-PSS-SHA256 signing
