# Windows Task Scheduler Setup for TradingView Alerts

## Quick Start (Windows Only)

Since you're on **Windows**, use **Task Scheduler** instead of cron jobs.

### Option 1: Automated Setup (Easiest)

1. Open PowerShell as Administrator
2. Run:
```powershell
cd C:\Users\winst\BentleyBudgetBot\mvp2-alerts
.\SETUP_WINDOWS_TASKS.bat
```

This automatically creates 4 scheduled tasks for:
- **7:00 AM** - Morning market open
- **9:40 AM** - Mid-morning update
- **11:30 AM** - Late morning update
- **3:00 PM** - Market close

### Option 2: Manual Setup in Task Scheduler

1. Press `Win + R` and type `taskschd.msc` (open Task Scheduler)
2. Click **Create Basic Task** in right panel
3. Name: `TradingView-Alerts-7AM`
4. Click **Next** → **Trigger** → Select **Daily**
5. Set time to **07:00** (7:00 AM)
6. Check **Repeat task every:** and set to **1 week** on **Mon-Fri only**
7. Click **Next** → **Action** → Select **Start a program**
8. Fill in:
   - **Program/script:** `C:\Program Files\nodejs\node.exe`
   - **Add arguments:** `C:\Users\winst\BentleyBudgetBot\mvp2-alerts\index.js --run-once`
   - **Start in:** `C:\Users\winst\BentleyBudgetBot\mvp2-alerts`
9. Click **Finish**

**Repeat Steps 2-9 for these tasks:**
- `TradingView-Alerts-9:40AM` @ 09:40
- `TradingView-Alerts-11:30AM` @ 11:30
- `TradingView-Alerts-3PM` @ 15:00

## Verify Tasks Are Running

```powershell
# List all TradingView tasks
schtasks /query | findstr "TradingView"

# View task details
schtasks /query /tn "TradingView-Alerts-7AM" /v

# Check last run time
schtasks /query /tn "TradingView-Alerts-7AM" /v | findstr "Last Run"
```

## Monitor Task Execution

### View Task Logs

1. **Event Viewer** → Windows Logs → System
2. Search for tasks with ID `1000` (Task Started) or `201` (Task Scheduler)
3. Filter by Source: `TaskScheduler`

### PowerShell Method

```powershell
# View recent task executions
Get-EventLog -LogName System -Source TaskScheduler -Newest 20

# View specific task last run
Get-ScheduledTaskInfo -TaskName "TradingView-Alerts-7AM"

# Check if task is enabled
Get-ScheduledTask -TaskName "TradingView-Alerts-7AM" | Select-Object State
```

## Troubleshooting

### Tasks Not Running

**Check if Node.js path is correct:**
```powershell
Test-Path "C:\Program Files\nodejs\node.exe"
```

**Verify task is enabled:**
```powershell
Enable-ScheduledTask -TaskName "TradingView-Alerts-7AM"
```

**Run task manually to test:**
```powershell
Start-ScheduledTask -TaskName "TradingView-Alerts-7AM"
```

### "Access Denied" Errors

Run PowerShell as Administrator:
```powershell
# Right-click PowerShell → Run as Administrator
```

### Discord Messages Not Sending

Check `.env` file has valid webhook URL:
```powershell
Get-Content C:\Users\winst\BentleyBudgetBot\mvp2-alerts\.env | Select-String "DISCORD_WEBHOOK"
```

## Better Alternative: Railway (Cloud Recommended)

If you want to **avoid Windows Task Scheduler complexity**, deploy to **Railway**:

1. Push code to GitHub
2. Link repository to Railway
3. Add MySQL plugin
4. Set environment variables
5. Railway automatically keeps service running 24/7
6. Cron schedules run in `index.js` on Railway servers

**Advantage:** No Windows machine needed to stay on—alerts run in the cloud.

## Summary

| Method | Pros | Cons |
|--------|------|------|
| **Windows Task Scheduler** | Native to Windows, simple setup | Requires PC to be running |
| **Railway (Cloud)** | 24/7 uptime, no local setup | Requires GitHub + Railway account |
| **Cron (Linux/Mac)** | Lightweight, standard | Not applicable to Windows |

Pick one and deploy! 🚀
