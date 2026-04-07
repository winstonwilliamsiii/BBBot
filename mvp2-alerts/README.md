# MVP2 Alerts - Market & Portfolio Discord Notifier

Node.js service that posts combined alerts to Discord using top gainers, top losers, and portfolio moves greater than 5%.

## Features

- **Top Gainers/Losers**: Fetches market movers using Yahoo Finance.
- **Portfolio Alerts**: Monitors holdings for moves greater than or equal to 5%.
- **Discord Integration**: Posts formatted embeds to a Discord webhook.
- **Scheduled Runs**: Runs at 7:00 AM, 9:40 AM, 11:30 AM, and 3:00 PM ET on weekdays.
- **Bot Universe Guard**: Filters all alert symbols to the configured bot screener universe before Discord delivery.

## Setup

1. **Install dependencies**

   ```bash
   npm install
   ```

2. **Configure environment**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Discord webhook URL.

3. **Customize portfolio symbols**

   Portfolio symbols are resolved in this order:

   1. `PORTFOLIO_SYMBOLS` (comma-separated)
   2. `MANSA_TECH_SYMBOLS` (comma-separated)
   3. MySQL `portfolios` table for `PORTFOLIO_USER_ID` (default `demo_user`)
   4. Built-in Mansa Tech fallback: `IONQ,QBTS,SOUN,RGTI,AMZN,NVDA`

4. **Select the bot universe to enforce**

   - `ALERT_BOT=Titan_Bot` or `ALERT_BOT=Vega_Bot`
   - `ENFORCE_BOT_UNIVERSE=true` (default)

   The service reads `../bentley-bot/config/bots/<bot>.yml`, loads the configured screener CSV, and filters gainers, losers, and portfolio symbols to that allowed universe. If the screener CSV is empty, the service fails closed and skips sending alerts.

5. **Configure rate limits**

   - `PORTFOLIO_SHARD_COUNT=4`
   - `PORTFOLIO_MAX_SYMBOLS_PER_RUN=5`
   - Optional override: `PORTFOLIO_SHARD_INDEX=0..N-1`

## Usage

### Manual Test Run

```bash
node index.js --run-once
```

### Run As Scheduled Service

```bash
npm start
```

## Schedule Configuration

Default schedule in `index.js`:

- 7:00 AM ET: `cron.schedule('0 7 * * 1-5', ...)`
- 9:40 AM ET: `cron.schedule('40 9 * * 1-5', ...)`
- 11:30 AM ET: `cron.schedule('30 11 * * 1-5', ...)`
- 3:00 PM ET: `cron.schedule('0 15 * * 1-5', ...)`

For Windows Task Scheduler, each task should call:

```bash
node index.js --run-once
```

This sends one alert run and exits cleanly.

## Data Provider Notes

Yahoo Finance is the default free quote source. Alternatives for production include:

- **Alpha Vantage**: Free tier with API key.
- **Finnhub**: Real-time data with free tier.
- **IEX Cloud**: Market data with flexible pricing.
- **Polygon.io**: Professional-grade market data.

Replace `fetchQuote()` in `index.js` if you want to switch providers.

## Discord Webhook

Get your webhook URL:

1. Go to Discord Server Settings → Integrations → Webhooks.
2. Create a new webhook.
3. Copy the URL into `.env`.

## Troubleshooting

- **No data returned**: Check Yahoo Finance availability or switch providers.
- **Discord errors**: Verify the webhook URL is correct and not expired.
- **Timezone issues**: Adjust the cron timezone in `index.js`.
- **No alerts sent after enabling universe guard**: Populate the target bot screener CSV under `../bentley-bot/config/` with that bot's allowed symbols.

## License

ISC
