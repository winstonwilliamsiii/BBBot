# MVP2 Alerts - Market & Portfolio Discord Notifier

Node.js service that posts combined alerts to Discord for all configured bots using each bot's universe symbols.

## Features

- **All Bot Signals format**: Sends top 15 movers (by absolute % move) per bot universe.
- **Daily Market and Portfolio format**: Sends top gainers, top losers, and portfolio moves >= 5% for every bot.
- **Discord Integration**: Posts formatted embeds to a Discord webhook.
- **Scheduled Runs**:
   - All Bot Signals at 8:30 AM ET (intended for the ML completion/startup window)
   - Daily Market and Portfolio at 9:30 AM, 12:00 PM, and 3:30 PM ET
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

4. **Select bots and universe enforcement**

   - `ALERT_BOTS=Titan_Bot,Vega_Bot,...` (optional; defaults to all bot configs)
   - `ALERT_SIGNALS_PER_BOT=15` (default)
   - `ALERT_MODE=daily|signals|both` (for `--run-once`)
   - `ENFORCE_BOT_UNIVERSE=true` (default)

   The service reads `../bentley-bot/config/bots/<bot>.yml`, loads the configured screener CSV, and filters all symbols to that allowed universe. If the screener CSV is empty, the service fails closed and skips sending alerts for that bot.

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
