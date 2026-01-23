# Environment Variables Reference

Complete documentation of all environment variables used across the Bentley Budget Bot application.

## Quick Reference

### Development (localhost)
```bash
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=bentley_bot_dev
```

### Production (Streamlit Cloud)
Configure via Streamlit Cloud Dashboard → App Settings → Secrets

---

## Database Variables (Trading Bot & Core App)

### Primary Variables (RECOMMENDED)
Use these in your configuration for consistency:

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `DB_HOST` | string | ✅ Yes | `localhost` | MySQL server hostname or IP |
| `DB_PORT` | number | ✅ Yes | `3306` | MySQL server port |
| `DB_USER` | string | ✅ Yes | `root` | Database user |
| `DB_PASSWORD` | string | ✅ Yes | ` ` | Database password (KEEP SECRET!) |
| `DB_NAME` | string | ✅ Yes | `bentley_bot_dev` | Database name |

**Example (Development)**:
```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=bentley_bot_dev
```

**Example (Production)**:
```dotenv
DB_HOST=your-rds-instance.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_USER=bentley_prod_user
DB_PASSWORD=super_secure_password_12345
DB_NAME=bentley_bot_prod
```

### Legacy MySQL Variables (BACKWARD COMPATIBILITY)
Used by some older code. If setting, use same values as `DB_*` variables:

| Variable | Type | Required | Default | Notes |
|----------|------|----------|---------|-------|
| `MYSQL_HOST` | string | ❌ No | `localhost` | Falls back to `DB_HOST` if not set |
| `MYSQL_PORT` | number | ❌ No | `3306` | Falls back to `DB_PORT` if not set |
| `MYSQL_USER` | string | ❌ No | `root` | Falls back to `DB_USER` if not set |
| `MYSQL_PASSWORD` | string | ❌ No | ` ` | Falls back to `DB_PASSWORD` if not set |
| `MYSQL_DATABASE` | string | ❌ No | `bentleybot` | Falls back to `DB_NAME` if not set |

---

## Environment Identifier

| Variable | Type | Required | Values | Description |
|----------|------|----------|--------|-------------|
| `ENVIRONMENT` | string | ✅ Yes | `development`, `production` | Determines which config to load |
| `DEPLOYMENT_TARGET` | string | ✅ Yes | `localhost`, `streamlit-cloud`, `docker` | Where the app is running |

**Examples**:
```dotenv
ENVIRONMENT=development
DEPLOYMENT_TARGET=localhost

# OR

ENVIRONMENT=production
DEPLOYMENT_TARGET=streamlit-cloud
```

---

## Streamlit Configuration

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `STREAMLIT_SERVER_PORT` | number | ❌ No | `8501` | Port Streamlit runs on |
| `STREAMLIT_SERVER_ADDRESS` | string | ❌ No | `localhost` | Address Streamlit listens on |
| `STREAMLIT_LOGGER_LEVEL` | string | ❌ No | `info` | Log level (debug, info, warning, error) |
| `STREAMLIT_CLIENT_LOGGER_LEVEL` | string | ❌ No | `info` | Client-side log level |
| `STREAMLIT_CLIENT_CACHE_CONTROL_HEADERS` | boolean | ❌ No | `false` | Cache control headers |

**Example**:
```dotenv
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_LOGGER_LEVEL=info
```

---

## Financial Data APIs

### Yahoo Finance
| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `YFINANCE_TIMEOUT` | number | ❌ No | `30` | Request timeout in seconds |
| `YFINANCE_BATCH_SIZE` | number | ❌ No | `8` | Number of tickers to fetch in batch |

### Alpaca Trading
| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ALPACA_API_KEY` | string | ❌ No | ` ` | Alpaca API key |
| `ALPACA_SECRET_KEY` | string | ❌ No | ` ` | Alpaca secret key |
| `ALPACA_BASE_URL` | string | ❌ No | `https://paper-api.alpaca.markets` | Alpaca endpoint |
| `ALPACA_ENVIRONMENT` | string | ❌ No | `paper` | `paper` or `live` |

### Tiingo
| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `TIINGO_API_KEY` | string | ❌ No | ` ` | Tiingo API key |

### Alpha Vantage
| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ALPHA_VANTAGE_API_KEY` | string | ❌ No | ` ` | Alpha Vantage API key |

### Webull
| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `WEBULL_APP_KEY` | string | ❌ No | ` ` | Webull app key |
| `WEBULL_APP_SECRET` | string | ❌ No | ` ` | Webull app secret |

---

## Banking Integration (Plaid)

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `PLAID_CLIENT_ID` | string | ❌ No | ` ` | Plaid client ID |
| `PLAID_SECRET` | string | ❌ No | ` ` | Plaid secret (KEEP SECRET!) |
| `PLAID_ENVIRONMENT` | string | ❌ No | `sandbox` | `sandbox`, `development`, or `production` |
| `PLAID_BASE_URL` | string | ❌ No | `https://sandbox.plaid.com` | Plaid endpoint |

**Example (Development)**:
```dotenv
PLAID_CLIENT_ID=your_sandbox_client_id
PLAID_SECRET=your_sandbox_secret
PLAID_ENVIRONMENT=sandbox
PLAID_BASE_URL=https://sandbox.plaid.com
```

---

## AI & LLM Configuration

### DeepSeek (Recommended for Financial Analysis)
| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `DEEPSEEK_API_KEY` | string | ❌ No | ` ` | DeepSeek API key |
| `DEEPSEEK_MODEL` | string | ❌ No | `deepseek-chat` | Model name |

### OpenAI (Alternative)
| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `OPENAI_API_KEY` | string | ❌ No | ` ` | OpenAI API key |

### Google Gemini
| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `GEMINI_API_KEY` | string | ❌ No | ` ` | Google Gemini API key |

---

## Backend Services

### Appwrite
| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `APPWRITE_ENDPOINT` | string | ❌ No | `http://localhost:80` | Appwrite server URL |
| `APPWRITE_PROJECT_ID` | string | ❌ No | ` ` | Appwrite project ID |
| `APPWRITE_API_KEY` | string | ❌ No | ` ` | Appwrite API key (KEEP SECRET!) |
| `APPWRITE_DATABASE_ID` | string | ❌ No | ` ` | Appwrite database ID |

### MLflow
| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `MLFLOW_TRACKING_URI` | string | ❌ No | `http://localhost:5000` | MLflow tracking server |
| `MLFLOW_BACKEND_STORE_URI` | string | ❌ No | `sqlite:///mlflow.db` | MLflow backend database |
| `MLFLOW_ARTIFACT_ROOT` | string | ❌ No | `./mlruns` | MLflow artifact storage |

---

## Logging & Debugging

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `LOG_LEVEL` | string | ❌ No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ENABLE_PROFILING` | boolean | ❌ No | `false` | Enable performance profiling |
| `ENABLE_ERROR_TRACING` | boolean | ❌ No | `false` | Enable detailed error tracing |
| `DEBUG_MODE` | boolean | ❌ No | `false` | Enable debug mode |

---

## File Paths

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `UPLOAD_DIRECTORY` | string | ❌ No | `./uploads` | Directory for file uploads |
| `LOG_DIRECTORY` | string | ❌ No | `./logs` | Directory for log files |
| `DATA_DIRECTORY` | string | ❌ No | `./data` | Directory for data files |

---

## Feature Flags

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ENABLE_EXPERIMENTAL_FEATURES` | boolean | ❌ No | `false` | Enable experimental features |
| `ENABLE_DEBUG_DASHBOARD` | boolean | ❌ No | `false` | Enable debug dashboard |
| `ENABLE_PORTFOLIO_UPLOAD` | boolean | ❌ No | `true` | Enable portfolio CSV uploads |
| `ENABLE_CHATBOT` | boolean | ❌ No | `true` | Enable AI chatbot |
| `ENABLE_BUDGET_DASHBOARD` | boolean | ❌ No | `true` | Enable budget tracking |
| `ENABLE_ECONOMIC_CALENDAR` | boolean | ❌ No | `true` | Enable economic calendar |

---

## Variable Priority & Fallback

The application checks variables in this order:

```
1. Streamlit Secrets (.streamlit/secrets.toml) - PRODUCTION ONLY
2. Environment variables in shell/system
3. .env.local (machine-specific) - DEVELOPMENT ONLY
4. .env.{ENVIRONMENT} (e.g., .env.development) - DEVELOPMENT ONLY
5. .env - FALLBACK
6. Hardcoded defaults in code - LAST RESORT
```

### Example Resolution Chain for `DB_HOST`:
```
Production:  Streamlit Secret "DB_HOST" → System ENV → Hardcoded default
Development: .env.local → .env.development → System ENV → Hardcoded default
```

---

## Security Best Practices

### ✅ DO:
- ✅ Use `.env.local` for machine-specific secrets (dev)
- ✅ Use Streamlit Cloud Secrets for production credentials
- ✅ Commit `.env.example` (with placeholder values)
- ✅ Commit `.env.development` (no sensitive data)
- ✅ Rotate passwords regularly
- ✅ Use strong passwords (minimum 16 characters)

### ❌ DON'T:
- ❌ Commit `.env` file to Git
- ❌ Commit `.env.local` to Git
- ❌ Commit `.env.production` to Git
- ❌ Put actual passwords in comments
- ❌ Share secrets in pull requests
- ❌ Use test credentials in production

---

## Common Configuration Scenarios

### Scenario 1: Local Development
```dotenv
ENVIRONMENT=development
DEPLOYMENT_TARGET=localhost

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=bentley_bot_dev

STREAMLIT_SERVER_PORT=8501
DEBUG_MODE=true
```

### Scenario 2: Production on Streamlit Cloud
Set these as Secrets in Streamlit Cloud dashboard:
```
ENVIRONMENT=production
DEPLOYMENT_TARGET=streamlit-cloud
DB_HOST=your-rds-host.amazonaws.com
DB_PORT=3306
DB_USER=bentley_prod
DB_PASSWORD=your-secure-password
DB_NAME=bentley_bot_prod
DEEPSEEK_API_KEY=your-api-key
```

### Scenario 3: Docker Development
```dotenv
ENVIRONMENT=development
DEPLOYMENT_TARGET=docker

DB_HOST=mysql
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=bentley_bot_dev

STREAMLIT_SERVER_ADDRESS=0.0.0.0
DEBUG_MODE=true
```

### Scenario 4: Remote Development with SSH Tunnel
```dotenv
ENVIRONMENT=development
DEPLOYMENT_TARGET=localhost

DB_HOST=127.0.0.1
DB_PORT=3307  # Local forwarded port
DB_USER=remote_user
DB_PASSWORD=remote_password
DB_NAME=bentley_bot_dev
```

---

## Verification Checklist

Before deploying, verify:

- [ ] All required `DB_*` variables are set
- [ ] Database password is strong (16+ characters)
- [ ] No passwords in `.env.development` (use `.env.local`)
- [ ] `.env.local` is in `.gitignore`
- [ ] `.env.example` has placeholder values only
- [ ] Streamlit Cloud Secrets are configured (production)
- [ ] Database can be reached from deployment environment
- [ ] Correct API keys are set for enabled features
- [ ] Log level is appropriate for environment
- [ ] Feature flags match environment needs

---

## Troubleshooting

### "Database Connection Failed"
1. Verify `DB_HOST` and `DB_PORT` are correct
2. Check `DB_USER` and `DB_PASSWORD`
3. Ensure database `DB_NAME` exists
4. Test connection: `mysql -u {DB_USER} -p -h {DB_HOST} -P {DB_PORT}`

### "Variable not found"
1. Check spelling and case (environment variables are case-sensitive on Unix)
2. Verify file is in correct location (`.env.development` for dev)
3. Run `source .env.development` to reload (bash) or `./.env.development` (PowerShell)
4. Restart Streamlit app after changing variables

### "API key rejected"
1. Verify API key is correct (copy-paste carefully)
2. Check if key has required permissions
3. Verify key hasn't expired
4. Check if key is rate-limited

---

## Related Documents
- [DEPLOYMENT.md](DEPLOYMENT.md) - How to deploy with proper configuration
- [PRODUCTION_CONFIG.md](PRODUCTION_CONFIG.md) - Production environment setup
- [.env.example](.env.example) - Example configuration file
- [.env.development](.env.development) - Development configuration file
