/**
 * UNIFIED BROKER TRADE API
 * 
 * Production-ready endpoint for executing trades across multiple brokers.
 * Integrates with BentleyBot's existing broker infrastructure.
 * 
 * Features:
 * - Environment-based broker routing (MVP vs PRODUCTION)
 * - Full Alpaca API integration with all order types
 * - Normalized response format across all brokers
 * - Comprehensive error handling and validation
 * - Ready for IBKR, Schwab, MT5, Binance integration
 * 
 * Environment Variables Required:
 * - APP_ENV: 'MVP' or 'PRODUCTION' (defaults to 'MVP')
 * - ALPACA_KEY_ID: Alpaca API key
 * - ALPACA_SECRET_KEY: Alpaca secret key
 * - ALPACA_BASE_URL: Alpaca API endpoint (paper or live)
 * 
 * Usage:
 * POST /api/trade
 * {
 *   "class": "equities",
 *   "symbol": "AAPL",
 *   "qty": 10,
 *   "side": "buy",
 *   "params": {
 *     "type": "limit",
 *     "limit_price": 150.00,
 *     "time_in_force": "day",
 *     "extended_hours": false
 *   }
 * }
 */

import type { NextApiRequest, NextApiResponse } from 'next'

// ============================================
// TYPE DEFINITIONS
// ============================================

type EnvMode = 'MVP' | 'PRODUCTION'
type AssetClass = 'equities' | 'futures' | 'options' | 'forex' | 'crypto'
type OrderType = 'market' | 'limit' | 'stop' | 'stop_limit' | 'trailing_stop'
type TimeInForce = 'day' | 'gtc' | 'opg' | 'cls' | 'ioc' | 'fok'
type OrderSide = 'buy' | 'sell'

interface Asset {
  class: AssetClass
  symbol: string
  qty: number
  side: OrderSide
  params?: {
    type?: OrderType
    time_in_force?: TimeInForce
    limit_price?: number
    stop_price?: number
    trail_price?: number
    trail_percent?: number
    extended_hours?: boolean
    client_order_id?: string
    // IBKR specific
    conid?: number // Contract ID
    // Options specific
    strike?: number
    expiry?: string
    option_type?: 'call' | 'put'
    // Any additional broker-specific params
    [key: string]: any
  }
}

interface NormalizedOrder {
  broker: string
  orderId: string | null
  status: string
  filledQty: number | null
  timestamp: string
  symbol: string
  side: OrderSide
  qty: number
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
  const validMode = mode === 'PRODUCTION' ? 'PRODUCTION' : 'MVP'
  
  console.log(`[TradeAPI] Environment mode: ${validMode}`)
  return validMode
}

/**
 * Select broker based on asset class and environment
 * 
 * Broker-to-Asset Mapping:
 * - Equities/ETFs: Alpaca (MVP), IBKR (Production), Schwab (Production)
 * - Futures: NinjaTrader + TradeStation
 * - Options: IBKR
 * - Forex: MT5 + IBKR
 * - Crypto: Binance
 */
function selectBroker(asset: Asset, env: EnvMode): string {
  const preferences: Record<AssetClass, Record<EnvMode, string[]>> = {
    equities: { 
      MVP: ['alpaca'], 
      PRODUCTION: ['ibkr', 'schwab'] 
    },
    futures: { 
      MVP: ['ninjatrader', 'tradestation'], 
      PRODUCTION: ['ninjatrader', 'tradestation'] 
    },
    options: { 
      MVP: ['ibkr'], 
      PRODUCTION: ['ibkr'] 
    },
    forex: { 
      MVP: ['mt5', 'ibkr'], 
      PRODUCTION: ['mt5', 'ibkr'] 
    },
    crypto: { 
      MVP: ['binance'], 
      PRODUCTION: ['binance'] 
    },
  }
  
  const preferred = preferences[asset.class]?.[env]
  const selected = preferred?.[0] ?? 'unsupported'
  
  console.log(`[TradeAPI] Broker selected: ${selected} for ${asset.class} in ${env} mode`)
  return selected
}

// ============================================
// ALPACA ADAPTER
// ============================================

function ensureAlpacaEnv() {
  // Support both naming conventions used in BentleyBot
  const keyId = process.env.ALPACA_KEY_ID || process.env.ALPACA_API_KEY || process.env.ALPACA_KEY
  const secretKey = process.env.ALPACA_SECRET_KEY || process.env.ALPACA_SECRET
  const baseUrl = process.env.ALPACA_BASE_URL || process.env.ALPACA_API_URL || 'https://paper-api.alpaca.markets'
  
  if (!keyId || !secretKey) {
    throw new Error('Missing Alpaca credentials. Set ALPACA_KEY_ID and ALPACA_SECRET_KEY in environment')
  }
  
  console.log(`[Alpaca] Using endpoint: ${baseUrl}`)
  return { keyId, secretKey, baseUrl }
}

function mapToAlpacaOrder(asset: Asset) {
  // Default values for common equity orders
  const type = asset.params?.type ?? 'market'
  const time_in_force = asset.params?.time_in_force ?? 'day'
  const limit_price = asset.params?.limit_price
  const stop_price = asset.params?.stop_price
  const trail_price = asset.params?.trail_price
  const trail_percent = asset.params?.trail_percent
  const extended_hours = asset.params?.extended_hours ?? false
  const client_order_id = asset.params?.client_order_id

  const payload: Record<string, any> = {
    symbol: asset.symbol.toUpperCase(),
    qty: asset.qty,
    side: asset.side,
    type,
    time_in_force,
    extended_hours,
  }

  // Add price parameters based on order type
  if (limit_price !== undefined) payload.limit_price = limit_price
  if (stop_price !== undefined) payload.stop_price = stop_price
  if (trail_price !== undefined) payload.trail_price = trail_price
  if (trail_percent !== undefined) payload.trail_percent = trail_percent
  if (client_order_id) payload.client_order_id = client_order_id

  console.log(`[Alpaca] Order payload:`, JSON.stringify(payload, null, 2))
  return payload
}

function normalizeAlpacaResponse(raw: any, asset: Asset): NormalizedOrder {
  return {
    broker: 'alpaca',
    orderId: raw?.id ?? null,
    status: raw?.status ?? 'unknown',
    filledQty: raw?.filled_qty ? Number(raw.filled_qty) : null,
    symbol: raw?.symbol ?? asset.symbol,
    side: raw?.side ?? asset.side,
    qty: raw?.qty ? Number(raw.qty) : asset.qty,
    timestamp: new Date().toISOString(),
    raw,
  }
}

async function alpacaTrade(asset: Asset): Promise<NormalizedOrder> {
  console.log(`[Alpaca] Executing trade: ${asset.side} ${asset.qty} ${asset.symbol}`)
  
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
    console.error(`[Alpaca] Order failed: ${resp.status} ${resp.statusText}`, errText)
    throw new Error(`Alpaca order failed: ${resp.status} ${resp.statusText} - ${errText}`)
  }

  const json = await resp.json()
  console.log(`[Alpaca] Order placed successfully:`, json)
  
  return normalizeAlpacaResponse(json, asset)
}

// ============================================
// IBKR ADAPTER (Stub - Ready for Integration)
// ============================================

/**
 * Interactive Brokers Gateway adapter
 * 
 * To implement:
 * 1. Ensure IBKR Gateway is running (localhost:5000)
 * 2. Authenticate session via /v1/api/iserver/auth/status
 * 3. Get contract ID (conid) via /v1/api/iserver/secdef/search
 * 4. Place order via /v1/api/iserver/account/{accountId}/orders
 * 5. Normalize response to NormalizedOrder format
 * 
 * See: c:\Users\winst\BentleyBudgetBot\bbbot1_pipeline\broker_api.py
 * And: c:\Users\winst\BentleyBudgetBot\frontend\components\multi_broker_dashboard.py
 */
async function ibkrTrade(asset: Asset): Promise<NormalizedOrder> {
  console.warn('[IBKR] Adapter not yet implemented - returning stub response')
  
  // When ready, use environment variables:
  // - IBKR_GATEWAY_URL (default: http://localhost:5000)
  // - IBKR_ACCOUNT_ID
  // - IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID
  
  return {
    broker: 'ibkr',
    orderId: null,
    status: 'stubbed',
    filledQty: null,
    symbol: asset.symbol,
    side: asset.side,
    qty: asset.qty,
    timestamp: new Date().toISOString(),
    raw: { 
      message: 'IBKR trade adapter not yet implemented',
      note: 'Wire in IBKR Gateway client from broker_api.py'
    },
  }
}

// ============================================
// SCHWAB ADAPTER (Stub - Ready for Integration)
// ============================================

/**
 * Charles Schwab API adapter
 * 
 * To implement:
 * 1. OAuth2 authentication flow
 * 2. Token refresh logic
 * 3. POST /trader/v1/accounts/{accountId}/orders
 * 4. Normalize response
 * 
 * Requires:
 * - SCHWAB_CLIENT_ID
 * - SCHWAB_CLIENT_SECRET
 * - SCHWAB_REFRESH_TOKEN
 * - SCHWAB_ACCOUNT_ID
 */
async function schwabTrade(asset: Asset): Promise<NormalizedOrder> {
  console.warn('[Schwab] Adapter not yet implemented - returning stub response')
  
  return {
    broker: 'schwab',
    orderId: null,
    status: 'stubbed',
    filledQty: null,
    symbol: asset.symbol,
    side: asset.side,
    qty: asset.qty,
    timestamp: new Date().toISOString(),
    raw: { 
      message: 'Schwab trade adapter not yet implemented'
    },
  }
}

// ============================================
// MT5 ADAPTER (Stub - Ready for Integration)
// ============================================

/**
 * MetaTrader 5 REST API adapter
 * 
 * To implement:
 * 1. Connect to MT5 REST server (see mt5_rest_api_server.py)
 * 2. POST /trade with order details
 * 3. Normalize response
 * 
 * See: c:\Users\winst\BentleyBudgetBot\mt5_rest_api_server.py
 * And: c:\Users\winst\BentleyBudgetBot\frontend\components\mt5_connector.py
 * 
 * Requires:
 * - MT5_API_URL (default: http://localhost:8000)
 */
async function mt5Trade(asset: Asset): Promise<NormalizedOrder> {
  console.warn('[MT5] Adapter not yet implemented - returning stub response')
  
  return {
    broker: 'mt5',
    orderId: null,
    status: 'stubbed',
    filledQty: null,
    symbol: asset.symbol,
    side: asset.side,
    qty: asset.qty,
    timestamp: new Date().toISOString(),
    raw: { 
      message: 'MT5 trade adapter not yet implemented',
      note: 'Wire in MT5 REST API from mt5_rest_api_server.py'
    },
  }
}

// ============================================
// BINANCE ADAPTER (Stub - Ready for Integration)
// ============================================

/**
 * Binance API adapter for crypto trading
 * 
 * To implement:
 * 1. HMAC signature generation
 * 2. POST /api/v3/order
 * 3. Normalize response
 * 
 * Requires:
 * - BINANCE_API_KEY
 * - BINANCE_API_SECRET
 * - BINANCE_TESTNET (true/false)
 */
async function binanceTrade(asset: Asset): Promise<NormalizedOrder> {
  console.warn('[Binance] Adapter not yet implemented - returning stub response')
  
  return {
    broker: 'binance',
    orderId: null,
    status: 'stubbed',
    filledQty: null,
    symbol: asset.symbol,
    side: asset.side,
    qty: asset.qty,
    timestamp: new Date().toISOString(),
    raw: { 
      message: 'Binance trade adapter not yet implemented'
    },
  }
}

// ============================================
// MAIN API HANDLER
// ============================================

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<NormalizedOrder | ErrorResponse>
) {
  const requestId = `trade_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  
  console.log(`[TradeAPI] ${requestId} - Request received`)
  console.log(`[TradeAPI] Method: ${req.method}`)
  console.log(`[TradeAPI] Body:`, JSON.stringify(req.body, null, 2))

  // Only accept POST requests
  if (req.method !== 'POST') {
    console.warn(`[TradeAPI] ${requestId} - Invalid method: ${req.method}`)
    return res.status(405).json({ 
      error: 'Method not allowed. Use POST.',
      timestamp: new Date().toISOString()
    })
  }

  try {
    // Validate request payload
    const asset: Asset = req.body
    
    if (!asset || !asset.class || !asset.symbol || !asset.qty || !asset.side) {
      console.error(`[TradeAPI] ${requestId} - Invalid payload`, asset)
      return res.status(400).json({ 
        error: 'Invalid asset payload',
        details: 'Required fields: class, symbol, qty, side',
        timestamp: new Date().toISOString()
      })
    }

    // Additional validation
    if (asset.qty <= 0) {
      return res.status(400).json({
        error: 'Invalid quantity',
        details: 'qty must be greater than 0',
        timestamp: new Date().toISOString()
      })
    }

    if (!['buy', 'sell'].includes(asset.side)) {
      return res.status(400).json({
        error: 'Invalid side',
        details: 'side must be "buy" or "sell"',
        timestamp: new Date().toISOString()
      })
    }

    // Get environment and select broker
    const env = getEnvMode()
    const broker = selectBroker(asset, env)

    if (broker === 'unsupported') {
      console.error(`[TradeAPI] ${requestId} - No broker for ${asset.class}`)
      return res.status(400).json({ 
        error: `Unsupported or unavailable broker for asset class: ${asset.class}`,
        details: `No broker configured for ${asset.class} in ${env} mode`,
        timestamp: new Date().toISOString()
      })
    }

    // Execute trade via selected broker adapter
    let result: NormalizedOrder

    switch (broker) {
      case 'alpaca':
        result = await alpacaTrade(asset)
        break
      
      case 'ibkr':
        result = await ibkrTrade(asset)
        break
      
      case 'schwab':
        result = await schwabTrade(asset)
        break
      
      case 'mt5':
        result = await mt5Trade(asset)
        break
      
      case 'binance':
        result = await binanceTrade(asset)
        break
      
      default:
        console.error(`[TradeAPI] ${requestId} - Unknown broker: ${broker}`)
        return res.status(400).json({ 
          error: `Unknown broker: ${broker}`,
          timestamp: new Date().toISOString()
        })
    }

    console.log(`[TradeAPI] ${requestId} - Trade completed:`, result)
    return res.status(200).json(result)

  } catch (err: any) {
    const message = typeof err?.message === 'string' ? err.message : 'Unknown error occurred'
    const stack = err?.stack || ''
    
    console.error(`[TradeAPI] ${requestId} - Error:`, message)
    console.error(`[TradeAPI] ${requestId} - Stack:`, stack)

    return res.status(500).json({ 
      error: message,
      details: process.env.NODE_ENV === 'development' ? stack : undefined,
      timestamp: new Date().toISOString()
    })
  }
}
