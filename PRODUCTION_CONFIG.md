# Production Configuration Guide

Complete setup and configuration guide for deploying Bentley Budget Bot to production (Streamlit Cloud).

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Setup](#step-by-step-setup)
4. [Streamlit Cloud Configuration](#streamlit-cloud-configuration)
5. [Database Setup](#database-setup)
6. [Security Hardening](#security-hardening)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Scaling & Performance](#scaling--performance)

---

## Architecture Overview

```
┌────────────────────────────────────────────────────┐
│         Users (Web Browser)                        │
│     https://your-app.streamlit.app                 │
└────────────────┬─────────────────────────────────┘
                 │
        ┌────────▼─────────┐
        │ Streamlit Cloud  │
        │  (Hosted Tier)   │
        └────────┬─────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│  Cache  │ │   API   │ │Database │
│ (Redis) │ │ (LLM)   │ │ (MySQL) │
└─────────┘ └─────────┘ └─────────┘
```

### Key Components

| Component | Technology | Provider | Purpose |
|-----------|-----------|----------|---------|
| **App** | Streamlit | Streamlit Cloud | Web interface |
| **Database** | MySQL 8.0 | Railway MySQL | Data persistence |
| **LLM** | DeepSeek/OpenAI | Cloud API | AI features |
| **Cache** | Redis (optional) | AWS ElastiCache | Performance |
| **Storage** | S3 (optional) | AWS S3 | File uploads |

---

## Prerequisites

### Required Accounts
- [ ] GitHub account (code repository)
- [ ] Streamlit Cloud account (free tier available)
- [ ] Railway account (for MySQL hosting)
  - OR: Self-managed MySQL server
  - OR: DigitalOcean, PlanetScale, etc.

### Required Tools
- [ ] Git (version control)
- [ ] Python 3.10+ (local development)
- [ ] MySQL CLI (database testing)
- [ ] SSH client (database access)

### Network Requirements
- [ ] Public MySQL endpoint accessible from Streamlit Cloud
- [ ] MySQL port 3306 open (or custom port)
- [ ] VPN/SSH tunnel configured (if needed for security)

---

## Step-by-Step Setup

### Phase 1: GitHub Repository

#### 1.1 Push Code to GitHub
```bash
# Ensure all changes committed locally
git add .
git commit -m "chore: prepare for production deployment"

# Push to main branch
git push origin main

# Verify on GitHub
# https://github.com/your-org/BentleyBudgetBot
```

#### 1.2 Verify Important Files
Check that these files are in the repository:
```
✓ streamlit_app.py (main app file)
✓ requirements.txt (dependencies)
✓ .streamlit/config.toml (Streamlit config)
✓ scripts/setup/init_trading_bot_db.py (schema)
✓ .env.example (configuration template)
✓ .gitignore (excludes .env, secrets)
```

---

### Phase 2: Set Up Production Database

#### 2.1 Choose Database Provider

**Option A: Railway (Recommended - Simple & Reliable)**
```bash
# 1. Go to AWS Console → RDS
# 2. Create new database:
#    - Engine: MySQL 8.0
#    - Instance class: db.t3.micro (free tier eligible)
#    - Storage: 20GB gp2
#    - DB name: bentley_bot_prod
#    - Username: admin (or bentley_prod_user)
#    - Generate strong password
#    - Publicly accessible: Yes
#    - VPC security group: Create new
#      - Inbound: Port 3306 from Anywhere (0.0.0.0/0)

# 3. Record these details:
#    - Endpoint: bentley-bot-db.xxxxx.us-east-1.rds.amazonaws.com
#    - Port: 3306
#    - Username: bentley_prod_user
#    - Password: [strong-password]
#    - Database: bentley_bot_prod
```

**Option B: DigitalOcean MySQL**
```bash
# 1. Go to DigitalOcean → Managed Databases
# 2. Create MySQL database cluster
# 3. Record connection details
```

**Option C: PlanetScale MySQL**
```bash
# 1. Go to PlanetScale → Create database
# 2. Get connection string
# 3. Format: mysql://[user]:[password]@[host]:[port]/[database]
```

#### 2.2 Initialize Production Database

**Via SSH Tunnel (if needed for security)**
```bash
# Create SSH tunnel to database server
ssh -L 3307:localhost:3306 your-server.com

# Then connect to localhost:3307
```

**Initialize schema**
```bash
# Set production environment variables
export DB_HOST="your-rds-endpoint.us-east-1.rds.amazonaws.com"
export DB_PORT="3306"
export DB_USER="bentley_prod_user"
export DB_PASSWORD="your_super_secure_password"
export DB_NAME="bentley_bot_prod"

# Run initialization script
python scripts/setup/init_trading_bot_db.py

# Verify tables created
mysql -u bentley_prod_user -p -h your-rds-endpoint.us-east-1.rds.amazonaws.com \
  -e "USE bentley_bot_prod; SHOW TABLES;"
```

---

### Phase 3: Streamlit Cloud Setup

#### 3.1 Connect GitHub Repository

1. Go to: https://share.streamlit.io/
2. Click **"New App"**
3. Select:
   - GitHub account: Your account
   - Repository: `BentleyBudgetBot`
   - Branch: `main`
   - File: `streamlit_app.py`
4. Click **"Deploy"**

**Status**: App will deploy within 1-2 minutes

#### 3.2 Configure Secrets

1. Go to App Settings → **Secrets**
2. Add production configuration:

```toml
# ============================================
# DATABASE CONFIGURATION
# ============================================
DB_HOST = "your-rds-endpoint.us-east-1.rds.amazonaws.com"
DB_PORT = "3306"
DB_USER = "bentley_prod_user"
DB_PASSWORD = "your_super_secure_password"
DB_NAME = "bentley_bot_prod"

# ============================================
# ENVIRONMENT IDENTIFIER
# ============================================
ENVIRONMENT = "production"
DEPLOYMENT_TARGET = "streamlit-cloud"

# ============================================
# AI & LLM (Optional)
# ============================================
DEEPSEEK_API_KEY = "sk-..."
DEEPSEEK_MODEL = "deepseek-chat"

# OR

OPENAI_API_KEY = "sk-..."

# ============================================
# FINANCIAL APIs (Optional)
# ============================================
ALPACA_API_KEY = "your-alpaca-key"
ALPACA_SECRET_KEY = "your-alpaca-secret"
ALPACA_BASE_URL = "https://api.alpaca.markets"
ALPACA_ENVIRONMENT = "live"  # Or "paper" for testing

# ============================================
# BANKING (Optional)
# ============================================
PLAID_CLIENT_ID = "your-plaid-client-id"
PLAID_SECRET = "your-plaid-secret"
PLAID_ENVIRONMENT = "production"

# ============================================
# FEATURE FLAGS
# ============================================
ENABLE_EXPERIMENTAL_FEATURES = "false"
ENABLE_DEBUG_DASHBOARD = "false"
ENABLE_PORTFOLIO_UPLOAD = "true"
ENABLE_CHATBOT = "true"
ENABLE_BUDGET_DASHBOARD = "true"
ENABLE_ECONOMIC_CALENDAR = "true"

# ============================================
# LOGGING
# ============================================
LOG_LEVEL = "INFO"
DEBUG_MODE = "false"
```

3. Click **"Save"**
4. Streamlit automatically restarts the app (1-2 minutes)

#### 3.3 Verify Deployment

```bash
# Wait 2-3 minutes
# Visit your app URL: https://your-app-name.streamlit.app

# Check for:
# ✓ App loads without errors
# ✓ No "Database Connection Not Available" message
# ✓ Trading Bot tab is accessible
# ✓ Can navigate to different pages
```

---

## Streamlit Cloud Configuration

### App Settings

#### 1. Advanced Settings
```
App Settings → Advanced Settings:

- Python version: 3.10
- Timezone: UTC (or your preference)
- Max upload size: 500MB
- Client error details: Minimal (for production)
```

#### 2. Resources
```
Resources → Tier Selection:

Free tier: 
  - Good for development/testing
  - 1 GB RAM
  - Limited concurrent users

Pro tier:
  - For production
  - More resources
  - Priority support
```

#### 3. Developer Settings
```
Developer Settings:

- Enable HTTPS: ✓ (always on)
- Allow public access: ✓
- Enable telemetry: Optional
```

---

## Database Setup

### Connection String Format

```
# MySQL connection string
mysql+pymysql://username:password@host:port/database

# Example:
mysql+pymysql://bentley_prod_user:MySecurePassword123@bentley-db.us-east-1.rds.amazonaws.com:3306/bentley_bot_prod
```

### Testing Database Connection

#### From Streamlit Cloud

Add this temporary code to `streamlit_app.py` to test:
```python
import streamlit as st
from sqlalchemy import create_engine, text
import os

if st.button("Test Database Connection"):
    try:
        engine = create_engine(
            f"mysql+pymysql://{os.getenv('DB_USER')}:"
            f"{os.getenv('DB_PASSWORD')}@"
            f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/"
            f"{os.getenv('DB_NAME')}",
            pool_pre_ping=True
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        st.success("✅ Database connection successful!")
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
```

#### From Local Machine
```bash
# Test connection
python verify_trading_bot_fix.py

# Should show:
# ✅ Trading Bot Database Ready!
```

### Backup Strategy

```bash
# Weekly automated backups (AWS RDS default)
# Manual backup before major changes:

# 1. AWS Console → RDS → Databases
# 2. Select database → Maintenance
# 3. Click "Create Manual Snapshot"

# Restore from snapshot:
# 1. RDS → Snapshots
# 2. Select snapshot → "Restore to new DB instance"
```

---

## Security Hardening

### 1. Database Security

```sql
-- Create production user with limited privileges
CREATE USER 'bentley_prod_user'@'%' IDENTIFIED BY 'your_super_secure_password';

-- Grant only necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE ON bentley_bot_prod.* 
  TO 'bentley_prod_user'@'%';

-- Revoke ALTER and DROP permissions
REVOKE ALTER, DROP ON bentley_bot_prod.* FROM 'bentley_prod_user'@'%';

-- Flush privileges
FLUSH PRIVILEGES;
```

### 2. Network Security

```
AWS RDS Security Group:

Inbound Rules:
  ├─ Protocol: TCP
  ├─ Port: 3306
  ├─ Source: Streamlit Cloud IP range
  │  (or specific IP if available)
  └─ Description: Bentley Bot Production

Outbound Rules:
  └─ Allow all (default)
```

### 3. Secrets Management

```toml
# DO NOT include in .env files:
- Database passwords
- API keys
- Authentication tokens
- Credit card information

# Always use Streamlit Secrets for these!
```

### 4. SSL/TLS Configuration

```
Database Connection (RDS):
  - Enforce SSL: Enabled
  - Certificate: AWS RDS CA certificate
  
Streamlit URL:
  - HTTPS: Automatic (Streamlit Cloud)
  - Certificate: Let's Encrypt
```

### 5. Access Control

```
Streamlit Cloud Permissions:
  - Owner: Your GitHub account
  - Collaborators: Add as needed
  - Public access: Anyone can view
  
GitHub Repository:
  - Branch protection: Enable for main
  - Require PR reviews: At least 1
  - Require status checks: Pass all tests
```

---

## Monitoring & Maintenance

### 1. Application Logs

**View Streamlit Cloud Logs**:
```
App Settings → Manage Repository → View logs

Look for:
- Database connection issues
- Missing environment variables
- Unhandled exceptions
- Performance warnings
```

**Common Error Patterns**:
```
[ERROR] ModuleNotFoundError: Missing dependency
  → Solution: Add to requirements.txt

[ERROR] pymysql.err.OperationalError: Connection failed
  → Solution: Check DB_* secrets, verify network

[ERROR] KeyError: 'DB_HOST'
  → Solution: Secrets not loaded, redeploy
```

### 2. Database Monitoring

```bash
# Check database size
mysql -u root -p -e "
  SELECT 
    table_schema as 'Database',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as 'Size (MB)'
  FROM information_schema.tables
  GROUP BY table_schema;"

# Monitor slow queries (if enabled)
mysql -u root -p -e "SHOW PROCESSLIST;"

# Check table statistics
mysql -u bentley_bot_prod -p -e "
  SELECT 
    table_name, 
    table_rows,
    round(((data_length + index_length) / 1024 / 1024), 2) as size_mb
  FROM information_schema.tables
  WHERE table_schema = 'bentley_bot_prod';"
```

### 3. Performance Optimization

```python
# In code: Connection pooling is already configured
from sqlalchemy import create_engine

engine = create_engine(
    connection_string,
    pool_pre_ping=True,      # Check connection before use
    pool_recycle=3600,       # Recycle connections hourly
    pool_size=10,            # Number of connections to keep
    max_overflow=20          # Additional connections if needed
)
```

### 4. Health Checks

**Weekly Checklist**:
```
- [ ] App accessible from https://your-app.streamlit.app
- [ ] No console errors
- [ ] Database connection working
- [ ] All features functional
- [ ] No memory leaks or hanging processes
- [ ] Load times acceptable (<3 seconds)
```

**Monthly Checklist**:
```
- [ ] Review application logs for errors
- [ ] Check database size and growth
- [ ] Verify backups are working
- [ ] Review user feedback and issues
- [ ] Update dependencies if available
- [ ] Rotate API keys if needed
```

---

## Scaling & Performance

### When to Scale

**Free Tier Limitations**:
- 1GB RAM
- Restarts if inactive for 7+ days
- Limited concurrent users (~5-10)

**When to upgrade to Pro Tier**:
```
Signs you need Pro:
✗ App frequently hits memory limits
✗ User base growing rapidly
✗ Database queries timing out
✗ Need guaranteed uptime
✗ Building features with heavy computation
```

### Scaling Strategy

```
Phase 1: Optimize Current Setup (Free)
  ├─ Cache data with @st.cache_data
  ├─ Lazy load components
  ├─ Optimize database queries
  └─ Monitor memory usage

Phase 2: Upgrade to Pro Tier
  ├─ More RAM (up to 16GB)
  ├─ Multiple compute units
  ├─ Faster startup
  └─ 99.9% SLA available

Phase 3: Add Services
  ├─ Redis for caching
  ├─ Larger RDS instance
  ├─ Load balancer (if DIY)
  └─ CDN for static files
```

### Database Scaling

```sql
-- Add indexes for slow queries
CREATE INDEX idx_trading_signals_timestamp 
  ON trading_signals(timestamp);

CREATE INDEX idx_trades_history_ticker 
  ON trades_history(ticker);

-- Archive old data (after 1 year)
DELETE FROM trading_signals 
  WHERE timestamp < DATE_SUB(NOW(), INTERVAL 1 YEAR);
```

---

## Cost Optimization

### AWS RDS Pricing Example (us-east-1)
```
Free Tier (12 months):
  - db.t2.micro: FREE
  - 20 GB storage: FREE
  - Data transfer: FREE (within region)

After Free Tier:
  - db.t3.micro: ~$12/month
  - 20 GB storage: ~$2/month
  - Data transfer: ~$1/month
  
Total monthly: ~$15-20
```

### Cost Reduction Tips
```
1. Use AWS free tier while available
2. Stop instance during off-hours (dev)
3. Right-size instance (start small)
4. Monitor unused resources
5. Use reserved instances (1 year commitment)
6. Set up CloudWatch alarms for cost
```

---

## Troubleshooting Production Issues

### Issue: App Crashes on Deploy

```
Error: ImportError: No module named 'mysql'

Solution:
1. Check requirements.txt has all imports
2. Run locally: pip install -r requirements.txt
3. Add missing package to requirements.txt
4. Commit and push
5. Streamlit auto-redeployment
```

### Issue: Database Connection Timeout

```
Error: pymysql.err.OperationalError: (2003, "Can't connect")

Solution:
1. Verify RDS is running (AWS Console)
2. Check security group allows port 3306
3. Verify DB_HOST is correct (check connection string)
4. Test from local machine:
   mysql -u bentley_prod_user -p -h [DB_HOST]
5. If still failing, redeploy from GitHub to refresh secrets
```

### Issue: Out of Memory

```
Error: App crashed due to memory limit

Solution:
1. Check logs for memory-heavy operations
2. Add caching: @st.cache_data(ttl=300)
3. Lazy load large datasets
4. Use generators instead of loading all data
5. Upgrade to Pro tier if issue persists
```

---

## Related Documentation
- [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) - Configuration reference
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment procedures
- [TRADING_BOT_CONNECTION_FIX.md](TRADING_BOT_CONNECTION_FIX.md) - Database fix details
- [.github/workflows/deploy.yml](.github/workflows/deploy.yml) - Automation
