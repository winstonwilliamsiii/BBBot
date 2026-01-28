# Bentley Bot - Notification Setup Guide
## Discord, Gmail, and Appwrite Integration
**Date**: January 28, 2026

---

## 🎯 OVERVIEW

Your notification system is now configured as:

| Environment | Event | Notification Method | Purpose |
|-------------|-------|---------------------|---------|
| **Demo** | Migration complete/failed | Console logs only | Local testing, no external alerts |
| **Staging** | Migration complete | **Appwrite → Gmail** | Email to wwilliams@mansacap.com: "ML training initiated" |
| **Staging** | Migration failed | **Appwrite → Gmail** | Email to wwilliams@mansacap.com: "Migration failed" |
| **Production** | Migration complete | **GitHub → Gmail** | Email to wwilliams@mansacap.com: "Production live" |
| **Production** | Trading signals active | **Discord Webhook** | Alert to Discord server: Trade signals broadcasting |
| **Production** | Migration failed | **Discord** | Urgent alert on Discord platform |

---

## 📋 SETUP CHECKLIST

### ✅ Step 1: Discord Webhook Setup (5 minutes)

#### **1.1 Create Discord Webhook**
```bash
# Go to your Discord server
1. Navigate to: https://discord.gg/rRFyNavT
2. Click Server Settings → Integrations → Webhooks
3. Click "New Webhook"
4. Name: "Bentley Bot - Production Signals"
5. Select channel for trade signals (e.g., #trading-signals)
6. Copy webhook URL (looks like: https://discord.com/api/webhooks/123456789/abc...)
```

#### **1.2 Add to GitHub Secrets**
```bash
# Go to your GitHub repository
1. Navigate to: Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: DISCORD_WEBHOOK_PROD
4. Value: [paste webhook URL from step 1.1]
5. Click "Add secret"
```

#### **1.3 Test Discord Webhook**
```bash
# Test from command line
curl -H "Content-Type: application/json" \
  -d '{"content": "🧪 Test message from Bentley Bot"}' \
  https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE
```

**Expected**: Message appears in your Discord channel

---

### ✅ Step 2: Gmail Setup for GitHub Actions (10 minutes)

#### **2.1 Create Gmail App Password**
```bash
# Go to Google Account
1. Navigate to: https://myaccount.google.com/security
2. Search for "App passwords" (must have 2FA enabled first)
3. Click "App passwords"
4. Select app: "Mail"
5. Select device: "Other" → Name it "Bentley Bot GitHub Actions"
6. Click "Generate"
7. Copy 16-character password (looks like: abcd efgh ijkl mnop)
```

#### **2.2 Add to GitHub Secrets**
```bash
# Go to GitHub repository → Settings → Secrets and variables → Actions
1. Add EMAIL_USERNAME = your-gmail@gmail.com
2. Add EMAIL_PASSWORD = [16-char app password from step 2.1]
```

#### **2.3 Test Email**
```bash
# You can test manually or wait for first production deployment
# Email will be sent to: wwilliams@mansacap.com
```

---

### ✅ Step 3: Appwrite Function Setup (15 minutes)

#### **3.1 Deploy Appwrite Function**
```bash
# Navigate to Appwrite console
1. Go to your Appwrite project
2. Click "Functions" → "Create Function"
3. Name: "staging-alert"
4. Runtime: Node.js 18
5. Entrypoint: index.js
6. Upload files:
   - appwrite-functions/staging-alert/index.js
   - appwrite-functions/staging-alert/package.json
```

#### **3.2 Configure Environment Variables in Appwrite**
```bash
# In Appwrite function settings → Environment Variables
1. GMAIL_USER = your-gmail@gmail.com
2. GMAIL_APP_PASSWORD = [same 16-char password from Step 2.1]
```

#### **3.3 Get Appwrite Function URL**
```bash
# In Appwrite function → Settings → Domains
Copy the function URL (looks like: https://cloud.appwrite.io/v1/functions/abc123/executions)
```

#### **3.4 Add to GitHub Secrets**
```bash
# Go to GitHub repository → Settings → Secrets and variables → Actions
1. Add APPWRITE_FUNCTION_URL = [function URL from step 3.3]
2. Add APPWRITE_PROJECT_ID = [your Appwrite project ID]
3. Add APPWRITE_API_KEY = [create API key in Appwrite Console → API Keys]
```

---

## 🧪 TESTING YOUR SETUP

### **Test 1: Demo Environment (No Alerts)**
```bash
# Push to dev branch
git checkout dev
git commit --allow-empty -m "test: Trigger demo migration"
git push origin dev

# Expected: GitHub Actions runs, console logs only, no external alerts
```

### **Test 2: Staging Environment (Appwrite → Gmail)**
```bash
# Push to staging branch
git checkout staging
git commit --allow-empty -m "test: Trigger staging migration"
git push origin staging

# Expected: 
# - GitHub Actions runs
# - Appwrite function triggers
# - Gmail received at wwilliams@mansacap.com with subject:
#   "🧠 Bentley Bot - ML Training Phase Initiated (2 Weeks)"
```

### **Test 3: Production Environment (Discord + Gmail)**
```bash
# Push to main branch
git checkout main
git commit --allow-empty -m "test: Trigger production migration"
git push origin main

# Expected:
# - GitHub Actions runs (with S3 backup)
# - Email to wwilliams@mansacap.com: "Production Migration ✅ Complete"
# - Discord message in your server: "🚀 PRODUCTION LIVE - Trading Signals Active"
```

---

## 📊 REQUIRED GITHUB SECRETS SUMMARY

```bash
# Total: 10 secrets needed

# Discord (1 secret)
DISCORD_WEBHOOK_PROD = https://discord.com/api/webhooks/...

# Gmail (2 secrets)
EMAIL_USERNAME = your-gmail@gmail.com
EMAIL_PASSWORD = abcd efgh ijkl mnop

# Appwrite (3 secrets)
APPWRITE_FUNCTION_URL = https://cloud.appwrite.io/v1/functions/...
APPWRITE_PROJECT_ID = 65f1a2b3c4d5e
APPWRITE_API_KEY = standard_abc123...

# Production Database (4 secrets - REQUIRED for backup)
DB_PROD_HOST = your-db-host.com
DB_PROD_PORT = 3306              # ⚠️ CRITICAL: Must be set or backup will fail!
DB_PROD_USER = your_db_user
DB_PROD_PASSWORD = your_db_password
```

### ⚠️ **CRITICAL: Database Backup Configuration**

The production migration workflow creates automatic database backups **before** running migrations. If `DB_PROD_PORT` is not set or is empty, the backup job will fail with:

```
Error: Empty value for 'port' specified
```

**Required Action:**
1. Go to: Repository → Settings → Secrets and variables → Actions
2. Verify these 4 secrets are configured:
   - `DB_PROD_HOST` = Your production database hostname
   - **`DB_PROD_PORT`** = `3306` (MySQL default) or your custom port
   - `DB_PROD_USER` = Database username with backup privileges
   - `DB_PROD_PASSWORD` = Database user password

**Test your backup configuration:**
```bash
# Manually test mysqldump command
mysqldump \
  --host=$DB_PROD_HOST \
  --port=$DB_PROD_PORT \
  --user=$DB_PROD_USER \
  --password=$DB_PROD_PASSWORD \
  --all-databases \
  > test_backup.sql
```

---

## 🔍 TROUBLESHOOTING

### **Production backup failing with "Empty value for 'port' specified"**
```bash
# Error message in GitHub Actions:
# mysqldump: Error: Empty value for 'port' specified

# Solution:
1. Go to: Repository → Settings → Secrets and variables → Actions
2. Check if DB_PROD_PORT exists
3. If missing or empty, add it:
   - Name: DB_PROD_PORT
   - Value: 3306 (or your database port number)
4. Re-run the failed workflow

# ⚠️ NOTE: Production migrations REQUIRE database backups
# The backup job must succeed before migrations run
```

### **Discord webhook not working**
```bash
# Check:
1. Webhook URL copied correctly (no extra spaces)
2. Webhook not deleted in Discord server
3. Bot has permission to post in channel

# Test manually:
curl -H "Content-Type: application/json" \
  -d '{"content": "Test"}' \
  $DISCORD_WEBHOOK_PROD
```

### **Gmail not working**
```bash
# Check:
1. 2FA enabled on Google account
2. App password generated correctly (16 chars, no spaces)
3. EMAIL_USERNAME is full email (your-email@gmail.com)

# Common error: "Invalid login"
Solution: Generate NEW app password, update GitHub secret
```

### **Appwrite function not triggering**
```bash
# Check:
1. Function deployed successfully in Appwrite Console
2. APPWRITE_FUNCTION_URL includes /staging-alert endpoint
3. APPWRITE_API_KEY has execution permissions
4. Environment variables set in Appwrite function

# View logs:
Go to Appwrite Console → Functions → staging-alert → Executions
```

---

## 🎯 NOTIFICATION FLOW DIAGRAM

```
GitHub Actions Workflow Triggered
│
├─ Demo (dev branch)
│  └─ Console logs only ✅
│
├─ Staging (staging branch)
│  └─ Appwrite Function
│     └─ Gmail to wwilliams@mansacap.com
│        └─ Subject: "🧠 ML Training Phase Initiated"
│
└─ Production (main branch)
   ├─ GitHub Email Action
   │  └─ Gmail to wwilliams@mansacap.com
   │     └─ Subject: "[BBBot] Production Migration ✅"
   │
   └─ Discord Webhook
      └─ Discord Server: https://discord.gg/rRFyNavT
         └─ Message: "🚀 PRODUCTION LIVE - Trading Signals Active"
```

---

## 💡 FUTURE ENHANCEMENTS

### **Signal Subscription System**
```sql
-- Track subscribers in database
CREATE TABLE signal_subscribers (
  user_id INT,
  platform VARCHAR(20), -- discord only
  platform_id VARCHAR(100),
  subscription_tier VARCHAR(20), -- free, basic, premium
  expiry_date DATE
);
```

### **Discord Bot Commands**
```javascript
// Enhanced Discord bot for interactive alerts
// Future: Add slash commands for subscribers
// /subscribe - Start receiving signals
// /status - Check portfolio status
// /alerts - Configure alert preferences
```

---

## 📞 SUPPORT

If notifications aren't working:
1. Check GitHub Actions logs: `https://github.com/winstonwilliamsiii/BBBot/actions`
2. Check Appwrite function logs: Appwrite Console → Functions → Executions
3. Test webhooks manually using curl commands above
4. Verify all 10 GitHub secrets are set correctly (especially `DB_PROD_PORT`!)

---

**Last Updated**: January 28, 2026  
**Status**: ✅ Production Ready (Telegram Removed)  
**Next**: Ensure Discord webhook and Gmail app password are configured
