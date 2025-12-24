# 🔐 Bentley Budget Bot - Security Guide

## 🚨 CRITICAL: API Keys Were Exposed in Public Repository

### Immediate Actions Required

1. **Revoke ALL exposed API keys immediately:**
   - ✅ Tiingo API: `E6c794cd1e5e48519194065a2a43b2396298288b` - **REVOKE NOW**
   - ✅ MySQL passwords: `bentley_secure_2025`, `root_secure_2025` - **CHANGE NOW**
   - ✅ Any other credentials found in commit history

2. **Generate new API keys** from your service providers:
   - [Tiingo API Dashboard](https://www.tiingo.com/account/api)
   - MySQL: Update passwords using your database admin tools
   - Barchart, Polygon, Yahoo Finance, etc.

3. **Add new keys to your .env file** (see setup below)

---

## 🛡️ Security Setup Guide

### Step 1: Create Your .env File

```bash
# Copy the template
cp .env.example .env

# Edit with your actual credentials (NEVER commit this file!)
notepad .env  # Windows
nano .env     # Linux/Mac
```

### Step 2: Add Your Actual API Keys to .env

Open `.env` and replace all `your_*_here` placeholders with your actual credentials:

```bash
# Example:
TIINGO_API_KEY=your_new_tiingo_key_here
MYSQL_PASSWORD=your_strong_password_here
```

### Step 3: Verify .gitignore

Ensure `.env` is in your `.gitignore` file (already done):

```gitignore
.env
.env.local
*.env
```

### Step 4: Load Environment Variables

#### For Local Development:

**Windows (PowerShell):**
```powershell
# Install python-dotenv if not already installed
pip install python-dotenv

# Load .env file in your Python scripts
from dotenv import load_dotenv
load_dotenv()
```

**Linux/Mac:**
```bash
# Source the .env file
export $(cat .env | xargs)

# Or use python-dotenv as above
```

#### For Docker Compose:

Your Docker services will automatically load `.env` file:

```yaml
# docker-compose.yml already configured
environment:
  - TIINGO_API_KEY=${TIINGO_API_KEY}
  - MYSQL_PASSWORD=${MYSQL_PASSWORD}
```

#### For Airflow:

```bash
# Set Airflow variables
airflow variables set TIINGO_API_KEY "your_key"
airflow variables set MYSQL_PASSWORD "your_password"

# Or use Airflow Connections for database credentials
```

---

## 🔒 Updated Files for Security

### Files Already Secured:

1. **`.vscode/#Tingo Crypto and News Data_Fetch.py`**
   - ✅ Now uses `os.getenv('TIINGO_API_KEY')`
   - ✅ Raises error if not set

2. **`workflows/airflow/dags/tiingo_data_historical.py`**
   - ✅ Now uses `os.getenv('TIINGO_API_KEY')`
   - ✅ Validates environment variable

3. **`.gitignore`**
   - ✅ Enhanced to exclude all sensitive files
   - ✅ Blocks `.env`, secrets, credentials

### Files That Need Manual Review:

- `docker-compose-mlflow.yml` - Hardcoded passwords (use environment variables)
- `workflows/airflow/dags/bentleybot_trading_dag.py` - MySQL config needs env vars
- `service_dashboard.html` - Default credentials should be changed

---

## 📋 Security Checklist

### Before Committing Code:

- [ ] Run `git status` to check what you're committing
- [ ] Verify `.env` is NOT in the commit
- [ ] Search for API keys: `git grep -i "api_key\|password\|secret"`
- [ ] Check commit diff: `git diff --cached`

### Regular Security Audit:

```bash
# Search for potential secrets in codebase
grep -r "api_key\s*=\s*['\"]" . --exclude-dir=node_modules --exclude-dir=.git
grep -r "password\s*=\s*['\"]" . --exclude-dir=node_modules --exclude-dir=.git
grep -r "secret\s*=\s*['\"]" . --exclude-dir=node_modules --exclude-dir=.git
```

### Git History Cleanup (if needed):

If secrets were committed, use BFG Repo-Cleaner:

```bash
# Install BFG
# Download from: https://rtyley.github.io/bfg-repo-cleaner/

# Remove file with secrets
bfg --delete-files your-secrets-file.py

# Replace strings containing secrets
bfg --replace-text passwords.txt

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (WARNING: This rewrites history)
git push --force
```

---

## 🔐 Best Practices

### 1. Environment Variables

**Always use environment variables for:**
- API keys and tokens
- Database passwords
- Secret keys and salts
- OAuth credentials
- SSH keys or certificates

### 2. Secrets Management Tools

For production, consider using:

- **AWS Secrets Manager** - For AWS deployments
- **Azure Key Vault** - For Azure deployments
- **HashiCorp Vault** - Self-hosted secrets management
- **Doppler** - Developer-friendly secrets management
- **GitHub Secrets** - For CI/CD pipelines

### 3. Docker Secrets

For Docker Swarm/Kubernetes:

```bash
# Create a secret
echo "my_api_key" | docker secret create tiingo_api_key -

# Use in docker-compose.yml
services:
  app:
    secrets:
      - tiingo_api_key
```

### 4. Airflow Connections & Variables

Store credentials in Airflow's encrypted backend:

```bash
# Using CLI
airflow connections add 'mysql_default' \
    --conn-type 'mysql' \
    --conn-host 'localhost' \
    --conn-login 'airflow' \
    --conn-password 'your_password'

# Or use the Web UI: Admin > Connections
```

### 5. Code Review

**Before merging PRs:**
- Use tools like `gitleaks` or `trufflehog` to scan for secrets
- Review all changed files for hardcoded credentials
- Verify `.env.example` is updated but `.env` is not committed

---

## 🚀 Quick Start After Security Setup

1. **Install dependencies:**
```bash
pip install python-dotenv
```

2. **Create and populate .env:**
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

3. **Test environment loading:**
```python
from dotenv import load_dotenv
import os

load_dotenv()
print("Tiingo API Key loaded:", bool(os.getenv('TIINGO_API_KEY')))
```

4. **Start services:**
```bash
docker-compose up -d
```

---

## 📞 Support

If you discover a security issue:
1. **Do NOT create a public GitHub issue**
2. Contact the maintainer directly
3. Revoke compromised credentials immediately

---

## 🔗 Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [Python dotenv Documentation](https://pypi.org/project/python-dotenv/)
- [Docker Secrets Management](https://docs.docker.com/engine/swarm/secrets/)

---

**Last Updated:** November 21, 2025
**Status:** 🔴 Critical security update applied
