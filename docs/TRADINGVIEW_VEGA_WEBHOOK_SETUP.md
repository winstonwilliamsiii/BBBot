# TradingView -> Vega_Bot Webhook Setup

This setup enables TradingView screener and strategy alerts to trigger Vega_Bot
automation for the Mansa_Retail fund via Vercel.

## Flow

`TradingView Alert` -> `Webhook URL` -> `Bentley API /api/tradingview-alert` -> bot universe guard -> `VEGA_BOT_WEBHOOK_URL` (Vega only, optional) + `Discord` (optional)

## 1) Configure Vercel Environment Variables

Set these in your Vercel project:

- `TRADINGVIEW_WEBHOOK_SECRET` = strong shared secret used by TradingView payload/query
- `VEGA_BOT_WEBHOOK_URL` = Vega_Bot execution endpoint for Mansa_Retail (optional but recommended for automation)
- `DISCORD_WEBHOOK` = Discord webhook URL (optional)
- `API_GATEWAY_KEY` = existing API key (fallback auth if no TradingView secret is set)
- `VEGA_PAPER_ONLY` = `true` (default, blocks live mode) or `false`
- `VEGA_LIVE_MODE_KEY` = required key for live mode payloads (optional but strongly recommended)
- `VEGA_BLOCKED_LIVE_ALERT_COOLDOWN_SECONDS` = cooldown for blocked-live tiny Discord alerts (default `300`)

## 2) TradingView Webhook URL

Use this webhook URL in TradingView alerts:

`https://<your-vercel-domain>/api/tradingview-alert?secret=<TRADINGVIEW_WEBHOOK_SECRET>`

Legacy Vega-only alias remains available:

`https://<your-vercel-domain>/api/vega/tradingview-alert?secret=<TRADINGVIEW_WEBHOOK_SECRET>`

You can also pass secret inside JSON as `"secret"` or `"passphrase"`.

## 3) TradingView Alert Message (JSON)

Use valid JSON in TradingView alert message.

### Base breakout signal payload

```json
{
  "secret": "YOUR_TRADINGVIEW_WEBHOOK_SECRET",
  "bot": "Vega_Bot",
  "fund": "Mansa Retail",
  "strategy": "Breakout Strategy",
  "alert_name": "Retail Breakout Entry",
  "ticker": "{{ticker}}",
  "exchange": "{{exchange}}",
  "interval": "{{interval}}",
  "time": "{{time}}",
  "price": "{{close}}",
  "action": "BUY",
  "mode": "paper",
  "FVFI": 1.42,
  "ROVL": 2.18,
  "risk": {
    "stop_loss_pct": 1.2,
    "take_profit_pct": 2.8,
    "position_size_pct": 0.5
  }
}
```

### Live mode payload (only when gate is enabled for live)

```json
{
  "secret": "YOUR_TRADINGVIEW_WEBHOOK_SECRET",
  "bot": "Vega_Bot",
  "fund": "Mansa Retail",
  "strategy": "Breakout Strategy",
  "ticker": "{{ticker}}",
  "interval": "{{interval}}",
  "price": "{{close}}",
  "action": "BUY",
  "FVFI": 1.42,
  "ROVL": 2.18,
  "mode": "live",
  "live_key": "YOUR_VEGA_LIVE_MODE_KEY"
}
```

### Payload with Discord forwarding enabled

```json
{
  "secret": "YOUR_TRADINGVIEW_WEBHOOK_SECRET",
  "bot": "Vega_Bot",
  "fund": "Mansa Retail",
  "strategy": "Breakout Strategy",
  "ticker": "{{ticker}}",
  "interval": "{{interval}}",
  "price": "{{close}}",
  "action": "SELL",
  "FVFI": 1.42,
  "ROVL": 2.18,
  "send_discord": true
}
```

## 4) Optional Windows Vega Scheduler

The repository now includes a scheduled task setup that matches the Admin
Control Center check for `Bentley-Vega`.

Create the task:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup_vega_task.ps1 -Action Create
```

List the task:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup_vega_task.ps1 -Action List
```

Test the task:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup_vega_task.ps1 -Action Test
```

Execution path:

- `setup_vega_task.ps1` registers the scheduled task.
- `run_vega.ps1` performs the 9:30 launch sequence.
- `start_bot_mode.ps1 -Bot Vega -Mode ON -Broker IBKR` checks IBKR connectivity.
- `scripts/vega_bot.py` runs the dedicated Vega_Bot fundamentals runtime.

## 5) Endpoint Behavior

`POST /api/tradingview-alert`

- Validates `TRADINGVIEW_WEBHOOK_SECRET` (query/body) if configured
- Validates the incoming symbol against the bot's configured screener universe before forwarding or Discord delivery
- Enforces execution mode gate (`paper` default; `live` only when allowed)
- Parses JSON payload from TradingView
- Normalizes key fields (`bot`, `fund`, `symbol`, `side`, `timeframe`, `strategy`, `price`, `FVFI`, `ROVL`)
- Forwards normalized payload to `VEGA_BOT_WEBHOOK_URL` when set
- Requires `FVFI` and `ROVL` when payload includes `"send_discord": true`
- Sends Discord alert when payload includes `"send_discord": true`
- Returns JSON status (`received`, `execution_mode`, `forward`, `discord`)

## 6) Quick Test (PowerShell)

```powershell
$body = @{
  secret = "YOUR_TRADINGVIEW_WEBHOOK_SECRET"
  bot = "Vega_Bot"
  fund = "Mansa Retail"
  strategy = "Breakout Strategy"
  ticker = "SPY"
  interval = "15"
  action = "BUY"
  price = "612.40"
  FVFI = 1.42
  ROVL = 2.18
  send_discord = $true
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "https://<your-vercel-domain>/api/tradingview-alert" `
  -ContentType "application/json" `
  -Body $body
```

## Notes

- If `TRADINGVIEW_WEBHOOK_SECRET` is not set, endpoint falls back to `x-api-key` validation when `API_GATEWAY_KEY` exists.
- The route enforces bot-universe membership using the screener CSV configured under `bentley-bot/config/bots/<bot>.yml`.
- If the configured screener CSV is empty, the route fails closed and rejects the alert.
- If `VEGA_PAPER_ONLY=true`, all `"mode": "live"` requests are rejected.
- When a live request is rejected (paper-only mode or invalid live key), a tiny Discord alert is sent (if `DISCORD_WEBHOOK` is configured).
- Repeated blocked-live alerts are rate-limited by `VEGA_BLOCKED_LIVE_ALERT_COOLDOWN_SECONDS` per symbol/timeframe.
- If `VEGA_LIVE_MODE_KEY` is set, live requests must include `live_key` (payload, query, or `x-live-key` header).
- For TradingView reliability, keep payload compact and always send valid JSON.
- `FVFI` and `ROVL` are required for Discord-delivered signal notifications.
- Start with `send_discord: true` during testing, then disable for high-frequency production alerts unless needed.
- For the 9:30 task, TWS or IB Gateway must be running with API socket access enabled on the configured port.
