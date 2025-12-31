# Cron Jobs Setup for TradingView Alerts

Deploy scheduled alerts using system cron jobs (Linux/Mac) or Task Scheduler (Windows).

## Cron Schedule

Your alerts are configured to run at:
- **7:00 AM ET** - Morning market open alert
- **9:40 AM ET** - Mid-morning gainers/losers
- **11:30 AM ET** - Late morning portfolio update  
- **3:00 PM ET** - Market close alert

## Linux/Mac Setup

### Step 1: Install Node.js (if not already installed)

```bash
# macOS
brew install node

# Ubuntu/Debian
sudo apt-get install nodejs npm
```

### Step 2: Navigate to project directory

```bash
cd /path/to/BentleyBudgetBot/mvp2-alerts
npm install
```

### Step 3: Create a shell script wrapper

```bash
cat > /usr/local/bin/trading-alerts.sh << 'EOF'
#!/bin/bash
cd /path/to/BentleyBudgetBot/mvp2-alerts
source .env
/usr/local/bin/node index.js >> /var/log/trading-alerts.log 2>&1
EOF

chmod +x /usr/local/bin/trading-alerts.sh
```

### Step 4: Add to crontab

```bash
crontab -e
```

Paste these lines:

```cron
# TradingView Alerts - Run at 7:00 AM, 9:40 AM, 11:30 AM, 3:00 PM ET (weekdays only)
0 7 * * 1-5 /usr/local/bin/trading-alerts.sh
40 9 * * 1-5 /usr/local/bin/trading-alerts.sh
30 11 * * 1-5 /usr/local/bin/trading-alerts.sh
0 15 * * 1-5 /usr/local/bin/trading-alerts.sh
```

### Step 5: Verify cron is running

```bash
# Check installed crontabs
crontab -l

# Monitor logs
tail -f /var/log/trading-alerts.log

# List active processes
ps aux | grep node
```

## Windows 10/11 Setup

### Step 1: Open Task Scheduler

```powershell
# Or press Win + R and type: taskschd.msc
```

### Step 2: Create Basic Task

1. Click **Create Basic Task**
2. Name: `TradingView-Alerts-7AM`
3. Click **Next** → Trigger: **Daily** → Set time to 7:00 AM
4. Set for weekdays only (repeat weekly Mon-Fri)
5. Action: **Start a program**
   - Program: `C:\Program Files\nodejs\node.exe`
   - Arguments: `C:\Users\winst\BentleyBudgetBot\mvp2-alerts\index.js`
   - Start in: `C:\Users\winst\BentleyBudgetBot\mvp2-alerts`
6. Finish

### Step 3: Create 3 more tasks for remaining times

Repeat Step 2 for:
- **TradingView-Alerts-9:40AM** → 9:40 AM
- **TradingView-Alerts-11:30AM** → 11:30 AM
- **TradingView-Alerts-3PM** → 3:00 PM

### Step 4: Verify tasks are running

```powershell
# Check scheduled tasks
Get-ScheduledTask | Where-Object {$_.TaskName -like "*TradingView*"}

# View task history
Get-ScheduledTaskInfo -TaskName "TradingView-Alerts-7AM"
```

## Docker/Railway Alternative (Recommended)

If using Railway cloud deployment, cron jobs run **automatically** via the Node.js scheduler in `index.js`.

No additional setup needed—just deploy and Railway keeps your service running 24/7.

## Troubleshooting

**Cron not running?**
```bash
# Check if cron daemon is active
sudo systemctl status cron

# Check cron logs
sudo tail -f /var/log/syslog | grep CRON
```

**Node command not found?**
```bash
# Find Node path
which node
# Use full path in crontab: /usr/local/bin/node (not just 'node')
```

**MySQL connection errors?**
- Verify `.env` file has correct credentials
- Check Railway MySQL is accessible from your network
- Test connection: `mysql -h nozomi.proxy.rlwy.net -u root -p...`

**Discord webhook failing?**
- Verify webhook URL hasn't expired
- Check webhook is still valid in Discord server
- Review Railway/cron logs for HTTP errors

## Monitoring

**Check recent logs:**
```bash
# Last 50 lines
tail -50 /var/log/trading-alerts.log

# Follow live logs
tail -f /var/log/trading-alerts.log

# Search for errors
grep ERROR /var/log/trading-alerts.log
```

**Verify database insertions:**
```bash
mysql -h nozomi.proxy.rlwy.net -u root -p'YOUR_PASSWORD' bbbot1
SELECT COUNT(*) FROM alerts_log WHERE sent_at > NOW() - INTERVAL 1 DAY;
```

## Notes

- Times are in **America/New_York** timezone (ET)
- Only runs on **weekdays** (Mon-Fri)
- Use `node index.js` to test manually
- Railway auto-deploys—no cron setup needed if using cloud
