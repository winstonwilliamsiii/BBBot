# 🚨 SECURITY INCIDENT: Exposed API Credentials

## Incident Summary
**Date:** January 12, 2026
**Commit:** `dd2ee4c323a8ea7ed71a12b9c7b79ef6732e9976`
**Severity:** 🔴 **CRITICAL**
**Status:** ⚠️ **ACTIVE - REQUIRES IMMEDIATE ACTION**

## What Happened
The file `.streamlit/secrets.toml` containing real API credentials was committed and pushed to GitHub public repository. The following credentials are now exposed in repository history:

### Exposed Credentials:
1. **Plaid API** (Banking)
   - Client ID: `68b8718ec2f428002456a84c`
   - Secret: `1849c4090173dfbce2bda5453e7048`
   
2. **Appwrite API** (Backend)
   - Project ID: `68869ef500017ca73772`
   - API Key: `standard_96d4a373241caa900a3bf2a...` (full key exposed)
   - Database ID: `6944821e4f5f5f4f7d10`

3. **Capital One API**
   - Client ID: `Cffefdaec9a5b6d9bfc074eb7f6e8637`
   - Secret: `F09d79fa5d14b8599042c9f1ebb66518`

4. **Alpaca Trading API**
   - API Key: `PKAYRIJUWUPO5VVWVTIWDXPRJ3`
   - Secret: `HDegV257ex4j1Wc7C3714mVBLoyircYYMTxTozZKWeaA`

5. **Tiingo Market Data**
   - API Key: `E6c794cd1e5e48519194065a2a43b2396298288b`

6. **Alpha Vantage**
   - API Key: `C73GF4GJR1F1ARIL`

---

## 🚨 IMMEDIATE ACTIONS (DO NOW)

### Step 1: Revoke All Exposed Credentials (Priority Order)

#### 1. Alpaca Trading API (HIGHEST PRIORITY)
- **Risk:** Someone could place trades with your account
- **Action:** 
  1. Go to https://alpaca.markets/docs/dashboard-overview/
  2. Login → API Keys section
  3. **DELETE** the exposed key: `PKAYRIJUWUPO5VVWVTIWDXPRJ3`
  4. Generate new API keys
  5. Update local `.env` file ONLY (never commit)

#### 2. Plaid Banking API
- **Risk:** Access to connected bank account data
- **Action:**
  1. Go to https://dashboard.plaid.com/developers/keys
  2. **Rotate** or **delete** the exposed secret
  3. Generate new credentials
  4. Update `.env` locally

#### 3. Appwrite Backend API
- **Risk:** Unauthorized database access
- **Action:**
  1. Go to https://cloud.appwrite.io/console/project-68869ef500017ca73772/settings
  2. Navigate to **API Keys** section
  3. **Delete** the exposed key starting with `standard_96d4a373...`
  4. Create new API key with minimal permissions
  5. Update `.env` locally

#### 4. Capital One API
- **Risk:** Access to Capital One API sandbox (less critical if sandbox)
- **Action:**
  1. Visit https://developer.capitalone.com/
  2. Go to your application settings
  3. **Regenerate** client secret
  4. Update `.env` locally

#### 5. Tiingo & Alpha Vantage
- **Risk:** API quota abuse, rate limit exhaustion
- **Action:**
  1. Tiingo: https://www.tiingo.com/account/api/token
  2. Alpha Vantage: https://www.alphavantage.co/support/#api-key
  3. Generate new API keys
  4. Update `.env` locally

---

### Step 2: Remove Secrets from Git History

⚠️ **Warning:** This will rewrite Git history and force all collaborators to re-clone

#### Option A: Remove Specific File from History (Recommended)
```powershell
# Install git-filter-repo if not already installed
pip install git-filter-repo

# Remove .streamlit/secrets.toml from all history
git filter-repo --path .streamlit/secrets.toml --invert-paths --force

# Force push to GitHub (WARNING: Destructive)
git push origin main --force
```

#### Option B: Use BFG Repo-Cleaner (Alternative)
```powershell
# Download BFG from https://rtyley.github.io/bfg-repo-cleaner/
java -jar bfg.jar --delete-files secrets.toml

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin main --force
```

#### Option C: Revert Commit (Easiest but secrets remain in history)
```powershell
# This creates a new commit that undoes dd2ee4c3
git revert dd2ee4c3
git push origin main
```
⚠️ **Note:** Option C does NOT remove secrets from Git history - they're still accessible

---

### Step 3: Add .streamlit/secrets.toml to .gitignore

```powershell
# Add to .gitignore if not already there
echo ".streamlit/secrets.toml" >> .gitignore
git add .gitignore
git commit -m "security: Add secrets.toml to .gitignore"
git push origin main
```

---

### Step 4: Create Template File Instead

```powershell
# Create a safe template file
cp .streamlit/secrets.toml .streamlit/secrets.toml.template

# Replace all real values with placeholders in the template
# Then commit the template ONLY
git add .streamlit/secrets.toml.template
git commit -m "docs: Add secrets.toml template with placeholders"
git push origin main
```

---

## 📋 Post-Incident Checklist

- [ ] All exposed API keys revoked/rotated
- [ ] New credentials generated
- [ ] Local `.env` updated with new credentials
- [ ] Verified new credentials work locally
- [ ] Secrets removed from Git history (`git filter-repo` or BFG)
- [ ] `.streamlit/secrets.toml` added to `.gitignore`
- [ ] Force pushed cleaned history to GitHub
- [ ] Created `secrets.toml.template` with placeholders
- [ ] Updated Streamlit Cloud secrets with new credentials
- [ ] Tested Streamlit Cloud app with new credentials
- [ ] Documented incident in security log
- [ ] Set up pre-commit hooks to prevent future leaks

---

## 🛡️ Prevention Measures

### 1. Add Pre-Commit Hook
Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
if git diff --cached --name-only | grep -q "secrets.toml"; then
    echo "❌ ERROR: Attempting to commit secrets.toml"
    echo "This file contains sensitive credentials and should never be committed."
    exit 1
fi
```

### 2. Use Git-Secrets Tool
```powershell
# Install git-secrets
pip install git-secrets

# Set up to scan for API keys
git secrets --install
git secrets --register-aws
git secrets --add 'ALPACA.*'
git secrets --add 'PLAID.*'
git secrets --add 'APPWRITE.*'
```

### 3. Update .gitignore Comprehensively
```gitignore
# Secrets and credentials
.env
.env.*
!.env.example
.streamlit/secrets.toml
secrets.toml
*secret*
*credentials*
*.pem
*.key

# API Keys
api_keys.txt
credentials.json
```

### 4. Use Environment Variables ONLY
- Local: Use `.env` file (gitignored)
- Streamlit Cloud: Use Streamlit Secrets UI
- Production: Use environment variables or secret managers (AWS Secrets Manager, Azure Key Vault)

---

## 🔍 Check for Unauthorized Access

### Monitor Your Accounts:

1. **Alpaca**
   - Check https://alpaca.markets/docs/dashboard-overview/ for unusual trades
   - Review account activity logs
   - Check for unauthorized positions

2. **Plaid**
   - Review API usage at https://dashboard.plaid.com/activity
   - Check for suspicious link tokens or item connections

3. **Appwrite**
   - Check database logs for unauthorized reads/writes
   - Review API usage statistics
   - Look for unknown IP addresses

4. **API Rate Limits**
   - Monitor for quota exhaustion
   - Watch for unusual traffic spikes

---

## 📞 Incident Response Contacts

| Service | Support URL | Priority |
|---------|------------|----------|
| Alpaca | https://alpaca.markets/support | 🔴 CRITICAL |
| Plaid | https://dashboard.plaid.com/support | 🔴 CRITICAL |
| Appwrite | https://appwrite.io/support | 🟠 HIGH |
| Capital One | https://developer.capitalone.com/support | 🟡 MEDIUM |
| Tiingo | support@tiingo.com | 🟢 LOW |
| Alpha Vantage | support@alphavantage.co | 🟢 LOW |

---

## 📝 Lessons Learned

### What Went Wrong:
1. ❌ Real credentials committed to `.streamlit/secrets.toml`
2. ❌ File not in `.gitignore` before committing
3. ❌ No pre-commit hooks to catch sensitive data
4. ❌ No code review before pushing

### What to Do Differently:
1. ✅ ALWAYS check `.gitignore` before adding new config files
2. ✅ Use templates with placeholders for example configs
3. ✅ Set up pre-commit hooks to scan for secrets
4. ✅ Use git-secrets or similar tools
5. ✅ Review `git diff --cached` before every commit
6. ✅ Never commit files with names containing "secret", "key", "credential"

---

## 🎯 Success Criteria

This incident is resolved when:
1. ✅ All exposed credentials are revoked
2. ✅ New credentials generated and tested
3. ✅ Secrets removed from Git history
4. ✅ `.gitignore` updated
5. ✅ Pre-commit hooks installed
6. ✅ No unauthorized access detected in logs
7. ✅ Streamlit Cloud app working with new credentials

---

## 📅 Timeline

| Time | Action | Status |
|------|--------|--------|
| 13:39 EST | Commit dd2ee4c3 pushed with secrets | ✅ Identified |
| 14:00 EST | Security issue detected | ⏳ In Progress |
| TBD | All credentials revoked | ⏳ Pending |
| TBD | Git history cleaned | ⏳ Pending |
| TBD | Prevention measures implemented | ⏳ Pending |
| TBD | Incident closed | ⏳ Pending |

---

## 📚 References

- [GitHub: Removing Sensitive Data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [git-filter-repo Documentation](https://github.com/newren/git-filter-repo)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [OWASP: Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

---

**Last Updated:** January 12, 2026, 14:00 EST  
**Next Review:** After all credentials rotated and Git history cleaned
