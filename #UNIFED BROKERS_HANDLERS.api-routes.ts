// pages/api/broker.ts (or split into positions.ts, balance.ts, order-status.ts)

import type { NextApiRequest, NextApiResponse } from 'next'

type EnvMode = 'MVP' | 'PRODUCTION'

interface AssetQuery {
  class: 'equities' | 'futures' | 'options' | 'forex' | 'crypto'
  brokerOverride?: string
}

interface NormalizedPosition {
  broker: string
  symbol: string
  qty: number
  avgPrice?: number
  marketValue?: number
  unrealizedPnL?: number
  raw: any
}

interface NormalizedBalance {
  broker: string
  cash: number | null
  buyingPower: number | null
  equity: number | null
  currency?: string
  raw: any
}

interface NormalizedOrderStatus {
  broker: string
  orderId: string
  status: string
  filledQty: number | null
  submittedAt?: string
  updatedAt?: string
  raw: any
}

/* ---------------------------
   Env + broker selection
---------------------------- */

function getEnvMode(): EnvMode {
  const mode = (process.env.APP_ENV || 'MVP').toUpperCase()
  return mode === 'PRODUCTION' ? 'PRODUCTION' : 'MVP'
}

function selectBroker(assetClass: AssetQuery['class'], env: EnvMode): string {
  const preferences: Record<AssetQuery['class'], Record<EnvMode, string[]>> = {
    equities: { MVP: ['alpaca'], PRODUCTION: ['ibkr', 'schwab', 'alpaca'] },
    futures: { MVP: ['ninjatrader'], PRODUCTION: ['tradestation', 'ninjatrader'] },
    options: { MVP: ['ibkr'], PRODUCTION: ['ibkr'] },
    forex: { MVP: ['mt5', 'ibkr'], PRODUCTION: ['ibkr', 'mt5'] },
    crypto: { MVP: ['binance'], PRODUCTION: ['binance'] },
  }
  const preferred = preferences[assetClass][env]
  return preferred[0] ?? 'unsupported'
}

/* ---------------------------
   Alpaca helpers
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

async function alpacaGet(path: string) {
  const { keyId, secretKey, baseUrl } = ensureAlpacaEnv()
  const resp = await fetch(`${baseUrl}${path}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'APCA-API-KEY-ID': keyId,
      'APCA-API-SECRET-KEY': secretKey,
    },
  })
  if (!resp.ok) {
    const errText = await resp.text()
    throw new Error(`Alpaca GET failed: ${resp.status} ${resp.statusText} - ${errText}`)
  }
  return resp.json()
}

/* ---------------------------
   Positions (Alpaca + IBKR stub)
---------------------------- */

function normalizeAlpacaPositions(raw: any[]): NormalizedPosition[] {
  return (raw || []).map((p) => ({
    broker: 'alpaca',
    symbol: p?.symbol ?? '',
    qty: p?.qty ? Number(p.qty) : 0,
    avgPrice: p?.avg_entry_price ? Number(p.avg_entry_price) : undefined,
    marketValue: p?.market_value ? Number(p.market_value) : undefined,
    unrealizedPnL: p?.unrealized_pl ? Number(p.unrealized_pl) : undefined,
    raw: p,
  }))
}

async function getPositionsAlpaca(): Promise<NormalizedPosition[]> {
  const json = await alpacaGet('/v2/positions')
  return normalizeAlpacaPositions(json)
}

async function getPositionsIBKR(): Promise<NormalizedPosition[]> {
  // Stub: replace with IBKR Gateway call to /portfolio/{accountId}/positions
  return []
}

/* ---------------------------
   Balance (Alpaca + IBKR stub)
---------------------------- */

function normalizeAlpacaAccount(raw: any): NormalizedBalance {
  return {
    broker: 'alpaca',
    cash: raw?.cash ? Number(raw.cash) : null,
    buyingPower: raw?.buying_power ? Number(raw.buying_power) : null,
    equity: raw?.equity ? Number(raw.equity) : null,
    currency: raw?.currency ?? 'USD',
    raw,
  }
}

async function getBalanceAlpaca(): Promise<NormalizedBalance> {
  const json = await alpacaGet('/v2/account')
  return normalizeAlpacaAccount(json)
}

async function getBalanceIBKR(): Promise<NormalizedBalance> {
  // Stub: replace with IBKR Gateway account summary
  return {
    broker: 'ibkr',
    cash: null,
    buyingPower: null,
    equity: null,
    raw: { message: 'IBKR balance adapter not yet implemented' },
  }
}

/* ---------------------------
   Order status (Alpaca + IBKR stub)
---------------------------- */

function normalizeAlpacaOrderStatus(raw: any): NormalizedOrderStatus {
  return {
    broker: 'alpaca',
    orderId: raw?.id ?? '',
    status: raw?.status ?? 'unknown',
    filledQty: raw?.filled_qty ? Number(raw.filled_qty) : null,
    submittedAt: raw?.submitted_at ?? undefined,
    updatedAt: raw?.updated_at ?? undefined,
    raw,
  }
}

async function getOrderStatusAlpaca(orderId: string): Promise<NormalizedOrderStatus> {
  const json = await alpacaGet(`/v2/orders/${orderId}`)
  return normalizeAlpacaOrderStatus(json)
}

async function getOrderStatusIBKR(orderId: string): Promise<NormalizedOrderStatus> {
  // Stub: replace with IBKR order status endpoint
  return {
    broker: 'ibkr',
    orderId,
    status: 'unknown',
    filledQty: null,
    raw: { message: 'IBKR order status adapter not yet implemented' },
  }
}

/* ---------------------------
   MT5 scaffold (trade adapter)
---------------------------- */

interface MT5TradeResult {
  broker: 'mt5'
  orderId: string | null
  status: 'submitted' | 'filled' | 'rejected' | 'unknown'
  filledQty: number | null
  timestamp: string
  raw: any
}

/**
 * Placeholder for MT5 integration.
 * Options:
 * 1) MQL5 Expert Advisor that listens for orders (e.g., via file, socket, or REST bridge) and executes trades.
 * 2) Python bridge using MetaTrader5 package to place orders from your backend.
 * Return a normalized shape consistent with other brokers.
 */
async function mt5Trade(asset: { symbol: string; qty: number; side: 'buy' | 'sell'; params?: any }): Promise<MT5TradeResult> {
  // TODO: Implement bridge call (HTTP to local service or socket to EA)
  return {
    broker: 'mt5',
    orderId: null,
    status: 'submitted',
    filledQty: null,
    timestamp: new Date().toISOString(),
    raw: { message: 'MT5 trade adapter not yet implemented' },
  }
}

/* ---------------------------
   API handlers (copy into separate files or multiplex)
---------------------------- */

// /api/positions
export async function positionsHandler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed. Use GET.' })
    return
  }
  try {
    const assetClass = (req.query.class as AssetQuery['class']) || 'equities'
    const brokerOverride = req.query.broker as string | undefined
    const env = getEnvMode()
    const broker = brokerOverride || selectBroker(assetClass, env)

    let positions: NormalizedPosition[] = []
    switch (broker) {
      case 'alpaca':
        positions = await getPositionsAlpaca()
        break
      case 'ibkr':
        positions = await getPositionsIBKR()
        break
      default:
        res.status(400).json({ error: `Unsupported or unavailable broker for ${assetClass}: ${broker}` })
        return
    }

    res.status(200).json({ broker, positions })
  } catch (err: any) {
    res.status(500).json({ error: err?.message || 'Unknown error' })
  }
}

// /api/balance
export async function balanceHandler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed. Use GET.' })
    return
  }
  try {
    const assetClass = (req.query.class as AssetQuery['class']) || 'equities'
    const brokerOverride = req.query.broker as string | undefined
    const env = getEnvMode()
    const broker = brokerOverride || selectBroker(assetClass, env)

    let balance: NormalizedBalance
    switch (broker) {
      case 'alpaca':
        balance = await getBalanceAlpaca()
        break
      case 'ibkr':
        balance = await getBalanceIBKR()
        break
      default:
        res.status(400).json({ error: `Unsupported or unavailable broker for ${assetClass}: ${broker}` })
        return
    }

    res.status(200).json({ broker, balance })
  } catch (err: any) {
    res.status(500).json({ error: err?.message || 'Unknown error' })
  }
}

// /api/order-status
export async function orderStatusHandler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed. Use GET.' })
    return
  }
  try {
    const assetClass = (req.query.class as AssetQuery['class']) || 'equities'
    const orderId = req.query.orderId as string
    const brokerOverride = req.query.broker as string | undefined
    if (!orderId) {
      res.status(400).json({ error: 'Missing orderId query parameter.' })
      return
    }

    const env = getEnvMode()
    const broker = brokerOverride || selectBroker(assetClass, env)

    let status: NormalizedOrderStatus
    switch (broker) {
      case 'alpaca':
        status = await getOrderStatusAlpaca(orderId)
        break
      case 'ibkr':
        status = await getOrderStatusIBKR(orderId)
        break
      default:
        res.status(400).json({ error: `Unsupported or unavailable broker for ${assetClass}: ${broker}` })
        return
    }

    res.status(200).json({ broker, status })
  } catch (err: any) {
    res.status(500).json({ error: err?.message || 'Unknown error' })
  }
}

/* ---------------------------
   Optional multiplexer default export
   Use /api/broker?action=positions|balance|order-status
---------------------------- */

export default async function brokerMultiplexer(req: NextApiRequest, res: NextApiResponse) {
  const action = (req.query.action as string) || ''
  if (action === 'positions') return positionsHandler(req, res)
  if (action === 'balance') return balanceHandler(req, res)
  if (action === 'order-status') return orderStatusHandler(req, res)
  res.status(400).json({ error: 'Invalid action. Use ?action=positions|balance|order-status' })
}