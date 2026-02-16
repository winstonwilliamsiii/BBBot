#UNIFED BROKER TRADES api-routes
// pages/api/trade.ts
import type { NextApiRequest, NextApiResponse } from 'next'

type EnvMode = 'MVP' | 'PRODUCTION'

interface Asset {
  class: 'equities' | 'futures' | 'options' | 'forex' | 'crypto'
  symbol: string
  qty: number
  side: 'buy' | 'sell'
  params?: Record<string, any> // e.g., { type, time_in_force, limit_price, stop_price, extended_hours }
}

interface NormalizedOrder {
  broker: string
  orderId: string | null
  status: string
  filledQty: number | null
  timestamp: string
  raw: any
}

function getEnvMode(): EnvMode {
  const mode = (process.env.APP_ENV || 'MVP').toUpperCase()
  return mode === 'PRODUCTION' ? 'PRODUCTION' : 'MVP'
}

function selectBroker(asset: Asset, env: EnvMode): string {
  const preferences: Record<Asset['class'], Record<EnvMode, string[]>> = {
    equities: { MVP: ['alpaca'], PRODUCTION: ['ibkr', 'schwab', 'alpaca'] },
    futures: { MVP: ['ninjatrader'], PRODUCTION: ['tradestation', 'ninjatrader'] },
    options: { MVP: ['ibkr'], PRODUCTION: ['ibkr'] },
    forex: { MVP: ['mt5', 'ibkr'], PRODUCTION: ['ibkr', 'mt5'] },
    crypto: { MVP: ['binance'], PRODUCTION: ['binance'] },
  }
  const preferred = preferences[asset.class][env]
  return preferred[0] ?? 'unsupported'
}

/* ---------------------------
   Alpaca helpers and adapter
---------------------------- */

function ensureAlpacaEnv() {
  const keyId = process.env.ALPACA_KEY_ID
  const secretKey = process.env.ALPACA_SECRET_KEY
  const baseUrl = process.env.ALPACA_BASE_URL
  if (!keyId || !secretKey || !baseUrl) {
    throw new Error('Missing Alpaca env: ALPACA_KEY_ID, ALPACA_SECRET_KEY, ALPACA_BASE_URL')
  }
  return { keyId, secretKey, baseUrl }
}

function mapToAlpacaOrder(asset: Asset) {
  // Defaults for equities; override via asset.params
  const type = asset.params?.type ?? 'market' // 'market' | 'limit' | 'stop' | 'stop_limit'
  const time_in_force = asset.params?.time_in_force ?? 'day' // 'day' | 'gtc' | 'opg' | 'ioc' | 'fok'
  const limit_price = asset.params?.limit_price
  const stop_price = asset.params?.stop_price
  const extended_hours = asset.params?.extended_hours ?? false

  const payload: Record<string, any> = {
    symbol: asset.symbol,
    qty: asset.qty,
    side: asset.side, // 'buy' | 'sell'
    type,
    time_in_force,
    extended_hours,
  }

  if (limit_price !== undefined) payload.limit_price = limit_price
  if (stop_price !== undefined) payload.stop_price = stop_price

  return payload
}

function normalizeAlpacaResponse(raw: any): NormalizedOrder {
  // Alpaca returns fields like: id, status, filled_qty, etc.
  return {
    broker: 'alpaca',
    orderId: raw?.id ?? null,
    status: raw?.status ?? 'unknown',
    filledQty: raw?.filled_qty ? Number(raw.filled_qty) : null,
    timestamp: new Date().toISOString(),
    raw,
  }
}

async function alpacaTrade(asset: Asset): Promise<NormalizedOrder> {
  const { keyId, secretKey, baseUrl } = ensureAlpacaEnv()
  const payload = mapToAlpacaOrder(asset)

  const resp = await fetch(`${baseUrl}/v2/orders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'APCA-API-KEY-ID': keyId,
      'APCA-API-SECRET-KEY': secretKey,
    },
    body: JSON.stringify(payload),
  })

  if (!resp.ok) {
    const errText = await resp.text()
    throw new Error(`Alpaca order failed: ${resp.status} ${resp.statusText} - ${errText}`)
  }

  const json = await resp.json()
  return normalizeAlpacaResponse(json)
}

/* ---------------------------
   IBKR stub (ready to wire)
---------------------------- */

async function ibkrTrade(asset: Asset): Promise<NormalizedOrder> {
  // Placeholder: call your gateway client here (ensure session, POST order, normalize)
  // Example shape:
  return {
    broker: 'ibkr',
    orderId: null,
    status: 'stubbed',
    filledQty: null,
    timestamp: new Date().toISOString(),
    raw: { message: 'IBKR trade adapter not yet implemented' },
  }
}

/* ---------------------------
   Main API handler
---------------------------- */

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed. Use POST.' })
    return
  }

  try {
    const asset: Asset = req.body
    if (!asset || !asset.class || !asset.symbol || !asset.qty || !asset.side) {
      res.status(400).json({ error: 'Invalid asset payload: class, symbol, qty, side are required.' })
      return
    }

    const env = getEnvMode()
    const broker = selectBroker(asset, env)

    let result: NormalizedOrder
    switch (broker) {
      case 'alpaca':
        result = await alpacaTrade(asset)
        break
      case 'ibkr':
        result = await ibkrTrade(asset)
        break
      default:
        res.status(400).json({ error: `Unsupported or unavailable broker for ${asset.class}: ${broker}` })
        return
    }

    res.status(200).json(result)
  } catch (err: any) {
    const message = typeof err?.message === 'string' ? err.message : 'Unknown error'
    res.status(500).json({ error: message })
  }
}