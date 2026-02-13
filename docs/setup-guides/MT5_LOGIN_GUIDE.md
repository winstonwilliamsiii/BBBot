# MT5 AdmiralsGroup Demo Login Instructions

## Your Credentials:
- **Account Number**: 5615791854
- **Username**: winston_ms
- **Password**: wvS7ftBb
- **Server**: AdmiralsGroup-Demo

## Step-by-Step Login Process:

### 1. Open MetaTrader 5 Terminal
   - The terminal is already running (PID: 42292)
   - Find the MT5 window on your taskbar

### 2. Login to Your Account

**Option A - If you see a login dialog:**
   - Enter Account: `5615791854`
   - Password: `wvS7ftBb`
   - Server: Select `AdmiralsGroup-Demo` from dropdown
   - Click **Login**

**Option B - From Menu:**
   1. Click **File** → **Login to Trade Account**
   2. Enter Account: `5615791854`
   3. Password: `wvS7ftBb`
   4. Server: Select `AdmiralsGroup-Demo`
   5. Check "Save account information" (optional)
   6. Click **Login**

**Option C - Account Switcher:**
   1. Look at bottom-right corner of MT5
   2. Click on the connection status area
   3. Select **Login to Trade Account**
   4. Follow steps above

### 3. Verify Connection
   - Bottom-right corner should show:
     - ✅ Green connection bars
     - 📊 Account number: 5615791854
     - 💰 Your balance
   - Should say "AdmiralsGroup-Demo" 

### 4. If Server Not Found:
   1. Click **File** → **Open an Account**
   2. Click **Add Broker**
   3. Search for "Admirals" or "Admiral Markets"
   4. Select **AdmiralsGroup-Demo** server
   5. Then login with credentials above

---

## After Logging In:
Run this command to verify connection:
```powershell
python quick_mt5_test.py
```

The Python API will then automatically connect to your logged-in MT5 account! 🚀
