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
   Portfolio symbols are resolved in this order:
   1. `PORTFOLIO_SYMBOLS` (comma-separated)
   2. `MANSA_TECH_SYMBOLS` (comma-separated)
   3. MySQL `portfolios` table for `PORTFOLIO_USER_ID` (default `demo_user`)
   4. Built-in Mansa Tech fallback: `IONQ,QBTS,SOUN,RGTI,AMZN,NVDA`

4. **Rate-limit controls (recommended for AlphaVantage free tier)**:
   - `PORTFOLIO_SHARD_COUNT=4` (split portfolio across runs)
   - `PORTFOLIO_MAX_SYMBOLS_PER_RUN=5` (cap symbols evaluated per run)
   - Optional override: `PORTFOLIO_SHARD_INDEX=0..N-1`

## Usage

**Manual test run**:
```bash
node index.js --run-once
```

**Run as scheduled service**:
```bash
npm start
```

## Schedule Configuration

Default daily trade alert schedule (weekdays, America/New_York timezone):
- 7:00 AM ET: `cron.schedule('0 7 * * 1-5', ...)`
- 9:40 AM ET: `cron.schedule('40 9 * * 1-5', ...)`
- 11:30 AM ET: `cron.schedule('30 11 * * 1-5', ...)`
- 3:00 PM ET: `cron.schedule('0 15 * * 1-5', ...)`

Current implementation schedule:
- 7:00 AM ET
- 9:40 AM ET
- 11:30 AM ET
- 3:00 PM ET

For Windows Task Scheduler, each task should call:
```bash
node index.js --run-once
```
This sends one alert run and exits cleanly.

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
