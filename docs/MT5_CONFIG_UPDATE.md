# MT5 Configuration Update Instructions

Based on your STREAMLIT_CLOUD_COMPLETE_SECRETS.toml, update your `.env.development` with these credentials:

```dotenv
# MT5 TRADING - DEVELOPMENT
# ============================================
# Local MT5 development settings
# Note: Port 8002 is used because 8000 is occupied by Airbyte
MT5_USER=winston_ms
MT5_PASSWORD=wvS7ftBb
MT5_HOST=MetaQuotes-Demo
MT5_PORT=443
MT5_API_URL=http://localhost:8002
MT5_REST_API_URL=http://localhost:8002
MT5_REST_API_TIMEOUT=30
```

## Next Steps:

1. Update your `.env.development` file with the credentials above
2. Run: `START_MT5_SERVER.bat`
3. Go to Multi-Broker Trading page and click "Connect MT5"

The server will use your logged-in MT5 desktop session to execute trades.
