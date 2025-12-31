# MVP2 Alerts - Market & Portfolio Discord Notifier

Node.js service that posts combined alerts (top gainers/losers + your portfolio moves >5%) to a Discord channel via webhook.

## Features

- **Top Gainers/Losers**: Fetches market movers using Yahoo Finance
- **Portfolio Alerts**: Monitors your holdings for moves ≥5%
- **Discord Integration**: Posts formatted embeds to your Discord channel
- **Scheduled Runs**: Automated alerts at 9:30 AM, 12:00 PM, and 3:30 PM ET on weekdays

## Setup

1. **Install dependencies** (already done):
   ```bash
   npm install
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Discord webhook URL

3. **Customize portfolio**:
   Edit `index.js` line 88 to add your stock symbols:
   ```javascript
   const portfolio = ['AAPL', 'MSFT', 'TSLA']; // replace with your holdings
   ```

## Usage

**Manual test run**:
```bash
node index.js
```

**Run as scheduled service**:
```bash
npm start
```

## Schedule Configuration

Default schedule (weekdays, America/New_York timezone):
- 9:30 AM ET: `cron.schedule('30 14 * * 1-5', ...)`
- 12:00 PM ET: `cron.schedule('0 17 * * 1-5', ...)`
- 3:30 PM ET: `cron.schedule('30 20 * * 1-5', ...)`

Modify cron patterns in `index.js` to adjust timing.

## API Notes

**Yahoo Finance**: Free public API used for quotes. Consider these alternatives for production:
- **Alpha Vantage**: Free tier with API key
- **Finnhub**: Real-time data with free tier
- **IEX Cloud**: Market data with flexible pricing
- **Polygon.io**: Professional-grade market data

Replace `fetchQuote()` function to integrate alternative providers.

## Discord Webhook

Get your webhook URL:
1. Go to Discord Server Settings → Integrations → Webhooks
2. Create New Webhook
3. Copy URL and add to `.env`

## Troubleshooting

- **No data returned**: Check Yahoo Finance API availability or switch providers
- **Discord errors**: Verify webhook URL is correct and not expired
- **Timezone issues**: Adjust `timezone` parameter in cron schedules

## License

ISC
