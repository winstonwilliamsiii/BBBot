/**
 * BALANCE API - Get account balance from brokers
 * 
 * GET /api/balance?class=equities&broker=alpaca
 * 
 * Returns normalized balance/account data across all brokers
 */

import type { NextApiRequest, NextApiResponse } from 'next'

type EnvMode = 'MVP' | 'PRODUCTION'
type AssetClass = 'equities' | 'futures' | 'options' | 'forex' | 'crypto'

interface NormalizedBalance {
  broker: string
  cash: number | null
  buyingPower: number | null
  equity: number | null
  portfolioValue?: number | null
  currency?: string
  raw: any
}

interface ErrorResponse {
  error: string
  details?: string
  timestamp: string
}

// ============================================
// ENVIRONMENT & BROKER SELECTION
// ============================================

function getEnvMode(): EnvMode {
  const mode = (process.env.APP_ENV || 'MVP').toUpperCase()
  return mode === 'PRODUCTION' ? 'PRODUCTION' : 'MVP'
}

/**
 * Select broker based on asset class and environment
 * Official Mapping:
 * - Equities/ETFs: Alpaca (MVP), IBKR, Schwab (Production)
 * - Futures: NinjaTrader + TradeStation
 * - Options: IBKR
 * - Forex: MT5 + IBKR
 * - Crypto: Binance
 */
function selectBroker(assetClass: AssetClass, env: EnvMode): string {
  const preferences: Record<AssetClass, Record<EnvMode, string[]>> = {
    equities: { MVP: ['alpaca'], PRODUCTION: ['ibkr', 'schwab'] },
    futures: { MVP: ['ninjatrader', 'tradestation'], PRODUCTION: ['ninjatrader', 'tradestation'] },
    options: { MVP: ['ibkr'], PRODUCTION: ['ibkr'] },
    forex: { MVP: ['mt5', 'ibkr'], PRODUCTION: ['mt5', 'ibkr'] },
    crypto: { MVP: ['binance'], PRODUCTION: ['binance'] },
  }
  const preferred = preferences[assetClass]?.[env]
  return preferred?.[0] ?? 'unsupported'
}

// ============================================
// ALPACA ADAPTER
// ============================================

function ensureAlpacaEnv() {
  const keyId = process.env.ALPACA_KEY_ID || process.env.ALPACA_API_KEY
  const secretKey = process.env.ALPACA_SECRET_KEY || process.env.ALPACA_SECRET
  const baseUrl = process.env.ALPACA_BASE_URL || process.env.ALPACA_API_URL || 'https://paper-api.alpaca.markets'
  
  if (!keyId || !secretKey) {
    throw new Error('Missing Alpaca credentials: ALPACA_KEY_ID, ALPACA_SECRET_KEY')
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

function normalizeAlpacaAccount(raw: any): NormalizedBalance {
  return {
    broker: 'alpaca',
    cash: raw?.cash ? Number(raw.cash) : null,
    buyingPower: raw?.buying_power ? Number(raw.buying_power) : null,
    equity: raw?.equity ? Number(raw.equity) : null,
    portfolioValue: raw?.portfolio_value ? Number(raw.portfolio_value) : null,
    currency: raw?.currency ?? 'USD',
    raw,
  }
}

async function getBalanceAlpaca(): Promise<NormalizedBalance> {
  console.log('[Alpaca] Fetching account balance...')
  const json = await alpacaGet('/v2/account')
  const balance = normalizeAlpacaAccount(json)
  console.log(`[Alpaca] Balance retrieved - Equity: $${balance.equity}`)
  return balance
}

// ============================================
// IBKR ADAPTER (Stub)
// ============================================

async function getBalanceIBKR(): Promise<NormalizedBalance> {
  console.warn('[IBKR] Balance adapter not yet implemented')
  
  // When ready, implement:
  // const gatewayUrl = process.env.IBKR_GATEWAY_URL || 'http://localhost:5000'
  // const accountId = process.env.IBKR_ACCOUNT_ID
  // const response = await fetch(`${gatewayUrl}/v1/api/portfolio/${accountId}/summary`)
  // return normalizeIBKRAccount(await response.json())
  
  return {
    broker: 'ibkr',
    cash: null,
    buyingPower: null,
    equity: null,
    raw: { message: 'IBKR balance adapter not yet implemented' },
  }
}

// ============================================
// SCHWAB ADAPTER (Stub)
// ============================================

async function getBalanceSchwab(): Promise<NormalizedBalance> {
  console.warn('[Schwab] Balance adapter not yet implemented')
  
  return {
    broker: 'schwab',
    cash: null,
    buyingPower: null,
    equity: null,
    raw: { message: 'Schwab balance adapter not yet implemented' },
  }
}

// ============================================
// MT5 ADAPTER (Stub)
// ============================================

async function getBalanceMT5(): Promise<NormalizedBalance> {
  console.warn('[MT5] Balance adapter not yet implemented')
  
  // When ready, implement:
  // const apiUrl = process.env.MT5_API_URL || 'http://localhost:8000'
  // const response = await fetch(`${apiUrl}/account`)
  // return normalizeMT5Account(await response.json())
  
  return {
    broker: 'mt5',
    cash: null,
    buyingPower: null,
    equity: null,
    raw: { message: 'MT5 balance adapter not yet implemented' },
  }
}

// ============================================
// BINANCE ADAPTER (Stub)
// ============================================

async function getBalanceBinance(): Promise<NormalizedBalance> {
  console.warn('[Binance] Balance adapter not yet implemented')
  
  return {
    broker: 'binance',
    cash: null,
    buyingPower: null,
    equity: null,
    raw: { message: 'Binance balance adapter not yet implemented' },
  }
}

// ============================================
// MAIN HANDLER
// ============================================

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<{ broker: string; balance: NormalizedBalance } | ErrorResponse>
) {
  const requestId = `balance_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  
  console.log(`[BalanceAPI] ${requestId} - Request received`)

  if (req.method !== 'GET') {
    return res.status(405).json({
      error: 'Method not allowed. Use GET.',
      timestamp: new Date().toISOString()
    })
  }

  try {
    // Get parameters
    const assetClass = (req.query.class as AssetClass) || 'equities'
    const brokerOverride = req.query.broker as string | undefined
    
    // Select broker
    const env = getEnvMode()
    const broker = brokerOverride || selectBroker(assetClass, env)

    console.log(`[BalanceAPI] ${requestId} - Broker: ${broker}, Asset: ${assetClass}, Env: ${env}`)

    if (broker === 'unsupported') {
      return res.status(400).json({
        error: `Unsupported asset class: ${assetClass}`,
        timestamp: new Date().toISOString()
      })
    }

    // Fetch balance from selected broker
    let balance: NormalizedBalance

    switch (broker) {
      case 'alpaca':
        balance = await getBalanceAlpaca()
        break
      
      case 'ibkr':
        balance = await getBalanceIBKR()
        break
      
      case 'schwab':
        balance = await getBalanceSchwab()
        break
      
      case 'mt5':
        balance = await getBalanceMT5()
        break
      
      case 'binance':
        balance = await getBalanceBinance()
        break
      
      default:
        return res.status(400).json({
          error: `Unknown broker: ${broker}`,
          timestamp: new Date().toISOString()
        })
    }

    console.log(`[BalanceAPI] ${requestId} - Balance retrieved successfully`)

    return res.status(200).json({
      broker,
      balance
    })

  } catch (err: any) {
    const message = err?.message || 'Unknown error occurred'
    
    console.error(`[BalanceAPI] ${requestId} - Error:`, message)

    return res.status(500).json({
      error: message,
      details: process.env.NODE_ENV === 'development' ? err?.stack : undefined,
      timestamp: new Date().toISOString()
    })
  }
}
