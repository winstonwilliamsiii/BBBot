# 🚀 MT5 Paper Trading Setup - TONIGHT'S CHECKLIST

## Current Status
- ✅ MetaTrader5 Python package installed (v5.0.5488)
- ✅ MT5 Terminal running (Process ID: 42292)
- ⚠️  **ACTION NEEDED:** Log into MT5 demo account

---

## Quick Setup (5 Minutes)

### STEP 1: Log into MT5 Demo Account

1. **Open MetaTrader 5** (it's already running)
   
2. **Log into Demo Account:**
   - Click **File** → **Open an Account**
   - OR: If you have an existing demo account, click the **account number** in the top-right corner
   - Select your **demo account** from the list
   - Enter your demo account password
   - Click **Login**

3. **Verify Login:**
   - You should see your account balance in the top-right
   - The "Terminal" panel at the bottom should show "Connected"
   - You should see real-time prices in the "Market Watch" panel

> 💡 **Don't have a demo account?**
> - Go to **File** → **Open an Account**
> - Choose any broker (e.g., MetaQuotes-Demo)
> - Click **Open a demo account**
> - Fill in the form (name, email, etc.)
> - Choose account type: **Standard** or **Demo**
> - Select currency: **USD**
> - Leverage: **1:100** (recommended for paper trading)
> - Click **Next** and note down your login credentials

---

### STEP 2: Start the MT5 REST Server

Once logged in, open PowerShell in this directory and run:

```powershell
.\START_MT5_PAPER_TRADING.ps1
```

The server will start on **http://localhost:8080**

---

### STEP 3: Test Your First Trade

Open a new PowerShell window and run:

```powershell
# Health check
curl http://localhost:8080/health

# Connect to MT5
curl -X POST http://localhost:8080/connect

# Get account info
curl http://localhost:8080/account

# Get current EUR/USD price
curl http://localhost:8080/price/EURUSD
```

---

## Quick Trade Examples

### Buy 0.01 lot of EUR/USD (Micro lot)
```powershell
$tradeData = @{
    symbol = "EURUSD"
    action = "buy"
    volume = 0.01
    stop_loss = 1.0800
    take_profit = 1.0900
    comment = "Paper trade test"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/trade" `
    -Method POST `
    -ContentType "application/json" `
    -Body $tradeData
```

### View Open Positions
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/positions"
```

### Close All EUR/USD Positions
```powershell
$closeData = @{
    symbol = "EURUSD"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/close" `
    -Method POST `
    -ContentType "application/json" `
    -Body $closeData
```

---

## Trading Symbols Available Tonight

### Forex Pairs (Paper Trading)
- **EURUSD** - Euro / US Dollar (most liquid)
- **GBPUSD** - British Pound / US Dollar
- **USDJPY** - US Dollar / Japanese Yen
- **AUDUSD** - Australian Dollar / US Dollar
- **USDCAD** - US Dollar / Canadian Dollar
- **USDCHF** - US Dollar / Swiss Franc

### Commodities (if supported by broker)
- **XAUUSD** - Gold / US Dollar
- **XAGUSD** - Silver / US Dollar
- **USOIL** - US Oil (WTI Crude)
- **UKOIL** - UK Oil (Brent Crude)

---

## Important Settings for Paper Trading

### Recommended Lot Sizes (Demo Account)
- **Micro lot:** 0.01 (1,000 units)
- **Mini lot:** 0.10 (10,000 units)  
- **Standard lot:** 1.00 (100,000 units)

Start with **0.01 lots** for testing!

### Risk Management
Always set:
- **Stop Loss (SL):** Maximum loss you're willing to take
- **Take Profit (TP):** Target profit level

Example for EUR/USD at 1.0850:
- Buy price: 1.0850
- Stop loss: 1.0830 (20 pips below = -$2 risk on 0.01 lot)
- Take profit: 1.0880 (30 pips above = $3 profit on 0.01 lot)

---

## Troubleshooting

### "Authorization failed" Error
**Cause:** Not logged into MT5 account

**Fix:**
1. Open MT5 terminal
2. Click account number in top-right
3. Select demo account and log in
4. Wait 5 seconds for connection
5. Run `python test_mt5_connection.py` to verify

### Server Won't Start
**Fix:**
```powershell
# Kill any existing server
Get-Process -Name "python" | Where-Object {$_.CommandLine -like "*mt5_rest*"} | Stop-Process

# Restart
.\START_MT5_PAPER_TRADING.ps1
```

### Symbol Not Found
**Fix:**
1. Open MT5 **Market Watch** (Ctrl+M)
2. Right-click → **Show All**
3. Find and enable the symbol you want to trade

---

## 🎯 Tonight's Goal

**Mission:** Place 1-3 paper trades manually via REST API

**Steps:**
1. ✅ Log into MT5 demo account
2. ✅ Start REST server
3. ✅ Test connection
4. ✅ Check account balance
5. ✅ Get current prices for EUR/USD
6. ✅ Place a small buy order (0.01 lot)
7. ✅ Monitor position
8. ✅ Close position manually

---

## Files Created for You

1. **START_MT5_PAPER_TRADING.ps1** - One-click server startup
2. **test_mt5_connection.py** - Verify MT5 connection
3. **QUICK_START_MT5_TRADING.md** - Full API reference
4. **requirements-mt5.txt** - Windows-only MT5 dependencies (NOT in main requirements.txt)

> ⚠️ **Important:** MetaTrader5 is Windows-only and has been isolated to `requirements-mt5.txt` to prevent breaking Linux/Mac deployments (Streamlit Cloud, Vercel, Railway)

---

## Next Steps After Tonight

- [ ] Build Python trading bot using the REST API
- [ ] Integrate with your portfolio dashboard
- [ ] Create automated trading strategies
- [ ] Set up alerts for price movements
- [ ] Track paper trading performance

---

**Ready to start? Follow STEP 1 above to log into MT5!** 🎯
