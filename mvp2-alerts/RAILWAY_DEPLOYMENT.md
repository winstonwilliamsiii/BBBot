# MVP3 Alerts - Railway Cloud Deployment

Deploy TradingView alerts to Railway with cloud MySQL and Discord integration.

## Prerequisites

1. **Railway Account**: [railway.app](https://railway.app)
2. **GitHub Repository**: Push `mvp2-alerts` folder to your repo
3. **Discord Webhook**: Already configured in `.env`

## Step 1: Create Railway MySQL Plugin

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Create new project → Add MySQL plugin
3. Copy these credentials to `.env`:
   ```
   RAILWAY_MYSQL_HOST=<host from Railway>
   RAILWAY_MYSQL_PORT=<port from Railway>
   RAILWAY_MYSQL_USER=<user from Railway>
   RAILWAY_MYSQL_PASSWORD=<password from Railway>
   ```

## Step 2: Deploy Node.js Service

1. In Railway project → Create new service → GitHub repo
2. Select `mvp2-alerts` directory
3. Configure environment:
   - **Root Directory**: `mvp2-alerts`
   - **Start Command**: `npm install && npm start`
   - Add variables from `.env`

## Step 3: Create Database Table

Run this in Railway MySQL console or via node script:

```sql
USE bbbot1;

CREATE TABLE IF NOT EXISTS alerts_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  symbol VARCHAR(20) NOT NULL,
  change_percent DECIMAL(6,2) NOT NULL,
  price DECIMAL(12,2),
  currency VARCHAR(10) DEFAULT 'USD',
  alert_type VARCHAR(50) NOT NULL,
  discord_delivered BOOLEAN DEFAULT FALSE,
  discord_error TEXT,
  sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_symbol (symbol),
  INDEX idx_sent_at (sent_at),
  INDEX idx_alert_type (alert_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## Step 4: Configure Environment Variables in Railway

1. Go to Railway Dashboard → Your Project → Variables
2. **Click "Add Variable"** and paste each of these:

```
DISCORD_WEBHOOK=https://discord.com/api/webhooks/1455710847270649959/qR9mM3HNbmNyHXkdnmwGesJdpj6Ee4USysSU_DhIzzRoA1bSpGt7atqn54-5Gpol-L9Y
MYSQL_HOST=nozomi.proxy.rlwy.net
MYSQL_PORT=54537
MYSQL_USER=root
MYSQL_PASSWORD=cBlIUSygvPJCgPbNKHePJekQlClRamri
MYSQL_DATABASE=bbbot1
NODE_ENV=production
```

**Connection String (for reference):**
```
mysql://root:cBlIUSygvPJCgPbNKHePJekQlClRamri@nozomi.proxy.rlwy.net:54537/railway
```

**Note:** After deployment, create the `alerts_log` table (see Step 3)

## Step 5: Monitor Logs

Railway Dashboard → Logs tab to watch:
- ✅ Alerts fetched from Yahoo Finance
- ✅ Alerts posted to Discord
- ✅ Database inserts to `alerts_log`

## Scheduled Runs

Alerts run on this schedule (weekdays, America/New_York timezone):
- 9:30 AM ET: Top gainers/losers
- 12:00 PM ET: Market update + portfolio check
- 3:30 PM ET: Close-of-day alert

## Troubleshooting

**MySQL Connection Failed**
- Verify Railway MySQL credentials in Railway Dashboard
- Check if IP whitelist is enabled (Railway allows all by default)
- Test connection: `mysql -h $RAILWAY_MYSQL_HOST -u $RAILWAY_MYSQL_USER -p$RAILWAY_MYSQL_PASSWORD`

**Discord Not Receiving Messages**
- Verify webhook URL is correct
- Check webhook hasn't expired
- Review Railway logs for HTTP errors

**Screener Endpoints Failing**
- Yahoo Finance may rate-limit or change endpoints
- Check latest endpoint: https://finance.yahoo.com/screeners/
- Consider switching to Alpha Vantage or Finnhub

## Local Development vs Production

**Local (localhost MySQL)**
```bash
npm install
node index.js
```

**Production (Railway MySQL)**
- Railway auto-deploys on git push
- Uses `RAILWAY_MYSQL_*` variables
- Node.js picks these up automatically via `.env` fallback

## Next Steps

1. Link GitHub repo to Railway
2. Add MySQL plugin to Railway project
3. Set environment variables
4. Deploy and monitor logs
5. Verify alerts in Discord and MySQL
