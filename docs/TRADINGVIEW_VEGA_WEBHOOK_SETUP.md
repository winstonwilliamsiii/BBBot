# TradingView → Vega Bot Webhook Setup

This setup enables TradingView screener/strategy alerts to trigger Vega Bot automation via Vercel.

## Flow

`TradingView Alert` → `Webhook URL` → `Bentley API /api/vega/tradingview-alert` → `VEGA_BOT_WEBHOOK_URL` (optional) + `Discord` (optional)

## 1) Configure Vercel Environment Variables

Set these in your Vercel project:

- `TRADINGVIEW_WEBHOOK_SECRET` = strong shared secret used by TradingView payload/query
- `VEGA_BOT_WEBHOOK_URL` = Vega Mansa Retail execution endpoint (optional but recommended for automation)
- `DISCORD_WEBHOOK` = Discord webhook URL (optional)
- `API_GATEWAY_KEY` = existing API key (fallback auth if no TradingView secret is set)
- `VEGA_PAPER_ONLY` = `true` (default, blocks live mode) or `false`
- `VEGA_LIVE_MODE_KEY` = required key for live mode payloads (optional but strongly recommended)

## 2) TradingView Webhook URL

Use this webhook URL in TradingView alerts:

`https://<your-vercel-domain>/api/vega/tradingview-alert?secret=<TRADINGVIEW_WEBHOOK_SECRET>`

You can also pass secret inside JSON as `"secret"` or `"passphrase"`.

## 3) TradingView Alert Message (JSON)

Use valid JSON in TradingView alert message.

### Base MTF ML signal payload

```json
{
  "secret": "YOUR_TRADINGVIEW_WEBHOOK_SECRET",
  "strategy": "Vega Mansa Retail MTF-ML",
  "alert_name": "MTF ML Entry",
  "ticker": "{{ticker}}",
  "exchange": "{{exchange}}",
  "interval": "{{interval}}",
  "time": "{{time}}",
  "price": "{{close}}",
  "action": "BUY",
  "mode": "paper",
  "ml_score": 0.84,
  "mtf": {
    "higher_tf": "240",
    "signal_tf": "60",
    "trigger_tf": "15"
  },
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
  "strategy": "Vega Mansa Retail MTF-ML",
  "ticker": "{{ticker}}",
  "interval": "{{interval}}",
  "price": "{{close}}",
  "action": "BUY",
  "mode": "live",
  "live_key": "YOUR_VEGA_LIVE_MODE_KEY"
}
```

### Payload with Discord forwarding enabled

```json
{
  "secret": "YOUR_TRADINGVIEW_WEBHOOK_SECRET",
  "strategy": "Vega Mansa Retail MTF-ML",
  "ticker": "{{ticker}}",
  "interval": "{{interval}}",
  "price": "{{close}}",
  "action": "SELL",
  "send_discord": true
}
```

## 4) Endpoint Behavior

`POST /api/vega/tradingview-alert`

- Validates `TRADINGVIEW_WEBHOOK_SECRET` (query/body) if configured
- Enforces execution mode gate (`paper` default; `live` only when allowed)
- Parses JSON payload from TradingView
- Normalizes key fields (`symbol`, `side`, `timeframe`, `strategy`, `price`)
- Forwards normalized payload to `VEGA_BOT_WEBHOOK_URL` when set
- Sends Discord alert when payload includes `"send_discord": true`
- Returns JSON status (`received`, `execution_mode`, `forward`, `discord`)

## 5) Quick Test (PowerShell)

```powershell
$body = @{
  secret = "YOUR_TRADINGVIEW_WEBHOOK_SECRET"
  strategy = "Vega Mansa Retail MTF-ML"
  ticker = "SPY"
  interval = "15"
  action = "BUY"
  price = "612.40"
  send_discord = $true
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "https://<your-vercel-domain>/api/vega/tradingview-alert" `
  -ContentType "application/json" `
  -Body $body
```

## Notes

- If `TRADINGVIEW_WEBHOOK_SECRET` is not set, endpoint falls back to `x-api-key` validation when `API_GATEWAY_KEY` exists.
- If `VEGA_PAPER_ONLY=true`, all `"mode": "live"` requests are rejected.
- When a live request is rejected by paper-only mode, a tiny Discord alert is sent (if `DISCORD_WEBHOOK` is configured).
- If `VEGA_LIVE_MODE_KEY` is set, live requests must include `live_key` (payload, query, or `x-live-key` header).
- For TradingView reliability, keep payload compact and always send valid JSON.
- Start with `send_discord: true` during testing, then disable for high-frequency production alerts unless needed.
