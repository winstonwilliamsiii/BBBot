# Titan Bot - Quick Reference Card

## Your Setup is Ready! ✅

You're already logged into Alpaca and the Bentley Dashboard. Here's how to use them:

---

## 🚀 FASTEST WAY TO RUN: PowerShell Script

### Step 1: Get Your API Keys (one-time)
```
1. Visit: https://app.alpaca.markets
2. Click: "Paper Trading" (for testing) or "Live Trading" (real money)
3. Find: "API Keys" section
4. Action: Click "View" and copy both keys
5. Keep: Safe - don't share these!
```

### Step 2: Run the Bot
```powershell
cd c:\Users\winst\BentleyBudgetBot
.\run_titan_bot.ps1 -ApiKey "pk_PASTE_YOUR_KEY_HERE" -SecretKey "sk_PASTE_YOUR_SECRET_HERE"
```

### Step 3: See the Magic
```
🤖 Initializing Titan Bot...
✅ Titan bot initialized successfully
   Trading Mode: Paper Test Account
   Trades Enabled: No (dry-run)
   Broker: https://paper-api.alpaca.markets

💡 Dry run mode - no actual trades executed
   To enable trading, add: -Execute flag
```

---

## 🎯 WHEN READY TO EXECUTE TRADES

### First Real Trade (Start Small!)
```powershell
.\run_titan_bot.ps1 `
  -ApiKey "pk_YOUR_KEY" `
  -SecretKey "sk_YOUR_KEY" `
  -Execute `
  -MaxTrades 1
```

### Multiple Trades
```powershell
.\run_titan_bot.ps1 `
  -ApiKey "pk_YOUR_KEY" `
  -SecretKey "sk_YOUR_KEY" `
  -Execute `
  -MaxTrades 5
```

### Live Trading (⚠️ REAL MONEY - Be Careful!)
```powershell
.\run_titan_bot.ps1 `
  -ApiKey "pk_YOUR_LIVE_KEY" `
  -SecretKey "sk_YOUR_LIVE_KEY" `
  -Execute `
  -Live
```

---

## 📊 DASHBOARD BUTTONS NOW WORK!

### In Streamlit Dashboard:

1. **Open**: `streamlit run streamlit_app.py`
2. **Navigate**: 🌐 Multi-Broker Trading Hub
3. **Tab**: 📈 Alpaca (Stocks/Crypto)
4. **Expand**: 🔗 Alpaca Connection
5. **Input**: Paste your API Key and Secret Key
6. **Click**: 🔑 "Connect with API Keys" button
7. **Result**: ✅ Keys persist and connection works!

---

## 📋 WHAT EACH MODE DOES

| Mode | Trades? | Money Risk? | Use When |
|------|---------|-----------|----------|
| **Dry-Run** *(default)* | ❌ No | ✅ None | First test |
| **Execute** | ✅ Yes | `️⚠️ Real Money` | All systems go |
| **Paper** *(default)* | ✅ Yes (fake $) | ✅ None | Test trading |
| **Live** | ✅ Yes (real $) | ⚠️ Yes | Production |

---

## ⚡ COMMAND COMPARISON

### Safest (Test Everything First)
```powershell
# No flags = dry-run, paper account, no trading
.\run_titan_bot.ps1 -ApiKey "pk_xxx" -SecretKey "sk_xxx"
```

### Moderate (Test Trades, No Real Money)
```powershell
# -Execute = enable trading on paper account
.\run_titan_bot.ps1 -ApiKey "pk_xxx" -SecretKey "sk_xxx" -Execute
```

### Dangerous (Real Money!) 🔥
```powershell
# -Live = real money! Only for experienced traders!
.\run_titan_bot.ps1 -ApiKey "pk_xxx" -SecretKey "sk_xxx" -Execute -Live
```

---

## 🔍 VERIFY TRADES EXECUTED

### In Alpaca Dashboard
```
https://app.alpaca.markets
├─ Click: Paper Trading (or Live Trading)
└─ Check: Recent Orders tab
```

### In Bentley Database
```sql
SELECT * FROM titan_trades ORDER BY created_at DESC LIMIT 10;
```

### In Bot Logs
```powershell
# Logs show in terminal output while bot runs
# Each trade displayed with Symbol, Quantity, Status
```

---

## 🐛 TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| "API Key and Secret required" | Paste both keys from Alpaca dashboard |
| "Connection refused" at MySQL | Run: `./start_mysql_docker.ps1` |
| Dashboard buttons still stuck | Hard refresh: `Ctrl+Shift+R` |
| "401 Auth failed" error | Regenerate API keys in Alpaca |
| Trades not executing | Enable `-Execute` flag |

---

## 🔒 SECURITY CHECKLIST

- [ ] Never commit API keys to git
- [ ] Keep keys in `.env` file (it's gitignored)
- [ ] Test paper account first
- [ ] Start with 1-3 trades maximum
- [ ] Enable IP restrictions in Alpaca
- [ ] Rotate keys monthly in production
- [ ] Clear keys after testing if shared machine

---

## 📚 HELPFUL LINKS

| Resource | URL |
|----------|-----|
| Alpaca Dashboard | https://app.alpaca.markets |
| API Documentation | https://docs.alpaca.markets |
| Paper Trading Info | https://app.alpaca.markets/paper |
| Account Funding | https://app.alpaca.markets/accounts/funding |

---

## ✅ YOUR BOT IS READY!

**Current Status**: All systems operational ✅

- Buttons fixed ✅
- CLI support added ✅
- Dashboard working ✅
- Documentation ready ✅

**Next Action**: 
1. Get your Alpaca API keys
2. Run: `.\run_titan_bot.ps1 -ApiKey "YOUR_KEY" -SecretKey "YOUR_SECRET"`
3. Watch the bot analyze and execute trades!

---

## 💬 NEED HELP?

1. Check: `TITAN_BOT_QUICK_START.md` for detailed guide
2. Review: `TITAN_BOT_FIXES_SUMMARY.md` for technical details
3. Try: `.\run_titan_bot.ps1 -ApiKey "?"` for inline help
4. Run: In dry-run mode first to see what bot would do

**Good luck, trader! Happy profitable trading! 🚀📈**
