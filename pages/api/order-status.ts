/**
 * ORDER STATUS API - Get order status from brokers
 * 
 * GET /api/order-status?class=equities&orderId=abc-123&broker=alpaca
 * 
 * Returns normalized order status data across all brokers
 */

import type { NextApiRequest, NextApiResponse } from 'next'
import { binanceGet, getSchwabToken, getTradeStationToken, httpGetWithAuth } from './lib/broker-utils'

type EnvMode = 'MVP' | 'PRODUCTION'
type AssetClass = 'equities' | 'futures' | 'options' | 'forex' | 'crypto'

interface NormalizedOrderStatus {
  broker: string
  orderId: string
  status: string
  symbol?: string
  side?: string
  qty?: number
  filledQty: number | null
  avgFillPrice?: number | null
  submittedAt?: string
  filledAt?: string
  updatedAt?: string
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

function normalizeAlpacaOrderStatus(raw: any): NormalizedOrderStatus {
  return {
    broker: 'alpaca',
    orderId: raw?.id ?? '',
    status: raw?.status ?? 'unknown',
    symbol: raw?.symbol ?? undefined,
    side: raw?.side ?? undefined,
    qty: raw?.qty ? Number(raw.qty) : undefined,
    filledQty: raw?.filled_qty ? Number(raw.filled_qty) : null,
    avgFillPrice: raw?.filled_avg_price ? Number(raw.filled_avg_price) : null,
    submittedAt: raw?.submitted_at ?? undefined,
    filledAt: raw?.filled_at ?? undefined,
    updatedAt: raw?.updated_at ?? undefined,
    raw,
  }
}

async function getOrderStatusAlpaca(orderId: string): Promise<NormalizedOrderStatus> {
  console.log(`[Alpaca] Fetching order status for: ${orderId}`)
  const json = await alpacaGet(`/v2/orders/${orderId}`)
  const status = normalizeAlpacaOrderStatus(json)
  console.log(`[Alpaca] Order status: ${status.status}`)
  return status
}

// ============================================
// IBKR ADAPTER (Stub)
// ============================================

async function getOrderStatusIBKR(orderId: string): Promise<NormalizedOrderStatus> {
  console.warn('[IBKR] Order status adapter not yet implemented')
  
  // When ready, implement:
  // const gatewayUrl = process.env.IBKR_GATEWAY_URL || 'http://localhost:5000'
  // const accountId = process.env.IBKR_ACCOUNT_ID
  // const response = await fetch(`${gatewayUrl}/v1/api/iserver/account/${accountId}/order/${orderId}`)
  // return normalizeIBKROrderStatus(await response.json())
  
  return {
    broker: 'ibkr',
    orderId,
    status: 'unknown',
    filledQty: null,
    raw: { message: 'IBKR order status adapter not yet implemented' },
  }
}

// ============================================
// SCHWAB ADAPTER
// ============================================

async function getOrderStatusSchwab(orderId: string): Promise<NormalizedOrderStatus> {
  console.log(`[Schwab] Fetching order status for: ${orderId}`)
  
  const accountId = process.env.SCHWAB_ACCOUNT_ID
  const apiUrl = process.env.SCHWAB_API_URL || 'https://api.schwabapi.com'

  if (!accountId) {
    throw new Error('Missing SCHWAB_ACCOUNT_ID')
  }

  const token = await getSchwabToken()
  const url = `${apiUrl}/trader/v1/accounts/${accountId}/orders/${orderId}`
  const data = await httpGetWithAuth(url, token)

  return {
    broker: 'schwab',
    orderId: data.orderId ?? orderId,
    status: data.status ?? 'unknown',
    symbol: data.orderLegCollection?.[0]?.instrument?.symbol,
    side: data.orderLegCollection?.[0]?.instruction,
    qty: data.quantity ? Number(data.quantity) : undefined,
    filledQty: data.filledQuantity ? Number(data.filledQuantity) : null,
    avgFillPrice: data.price ? Number(data.price) : null,
    submittedAt: data.enteredTime,
    filledAt: data.closeTime,
    updatedAt: data.enteredTime,
    raw: data
  }
}

// ============================================
// MT5 ADAPTER (Stub)
// ============================================

async function getOrderStatusMT5(orderId: string): Promise<NormalizedOrderStatus> {
  console.warn('[MT5] Order status adapter not yet implemented')
  
  // When ready, implement:
  // const apiUrl = process.env.MT5_API_URL || 'http://localhost:8000'
  // const response = await fetch(`${apiUrl}/order/${orderId}`)
  // return normalizeMT5OrderStatus(await response.json())
  
  return {
    broker: 'mt5',
    orderId,
    status: 'unknown',
    filledQty: null,
    raw: { message: 'MT5 order status adapter not yet implemented' },
  }
}

// ============================================
// BINANCE ADAPTER
// ============================================

async function getOrderStatusBinance(orderId: string): Promise<NormalizedOrderStatus> {
  console.log(`[Binance] Fetching order status for: ${orderId}`)
  
  // Binance requires symbol for order query - would need to pass it or store mapping
  // For now, query all orders and find by orderId
  const data = await binanceGet('/api/v3/order', { orderId })

  return {
    broker: 'binance',
    orderId: String(data.orderId),
    status: data.status ?? 'unknown',
    symbol: data.symbol,
    side: data.side,
    qty: data.origQty ? Number(data.origQty) : undefined,
    filledQty: data.executedQty ? Number(data.executedQty) : null,
    avgFillPrice: data.price ? Number(data.price) : null,
    submittedAt: data.time ? new Date(data.time).toISOString() : undefined,
    filledAt: data.updateTime ? new Date(data.updateTime).toISOString() : undefined,
    updatedAt: data.updateTime ? new Date(data.updateTime).toISOString() : undefined,
    raw: data
  }
}

// ============================================
// TRADESTATION ADAPTER
// ============================================

async function getOrderStatusTradeStation(orderId: string): Promise<NormalizedOrderStatus> {
  console.log(`[TradeStation] Fetching order status for: ${orderId}`)
  
  const accountId = process.env.TRADESTATION_ACCOUNT_ID
  const apiUrl = process.env.TRADESTATION_API_URL || 'https://api.tradestation.com'

  if (!accountId) {
    throw new Error('Missing TRADESTATION_ACCOUNT_ID')
  }

  const token = await getTradeStationToken()
  const url = `${apiUrl}/v3/orderexecution/orders/${orderId}`
  const data = await httpGetWithAuth(url, token)

  return {
    broker: 'tradestation',
    orderId: data.OrderID ?? orderId,
    status: data.Status ?? 'unknown',
    symbol: data.Symbol,
    side: data.BuyOrSell,
    qty: data.Quantity ? Number(data.Quantity) : undefined,
    filledQty: data.FilledQuantity ? Number(data.FilledQuantity) : null,
    avgFillPrice: data.AveragePrice ? Number(data.AveragePrice) : null,
    submittedAt: data.OpenedDateTime,
    filledAt: data.ClosedDateTime,
    updatedAt: data.StatusDateTime,
    raw: data
  }
}

// ============================================
// MAIN HANDLER
// ============================================

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<{ broker: string; status: NormalizedOrderStatus } | ErrorResponse>
) {
  const requestId = `order_status_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  
  console.log(`[OrderStatusAPI] ${requestId} - Request received`)

  if (req.method !== 'GET') {
    return res.status(405).json({
      error: 'Method not allowed. Use GET.',
      timestamp: new Date().toISOString()
    })
  }

  try {
    // Get parameters
    const assetClass = (req.query.class as AssetClass) || 'equities'
    const orderId = req.query.orderId as string
    const brokerOverride = req.query.broker as string | undefined
    
    // Validate orderId
    if (!orderId) {
      return res.status(400).json({
        error: 'Missing orderId query parameter',
        details: 'Provide orderId as query parameter: ?orderId=abc-123',
        timestamp: new Date().toISOString()
      })
    }

    // Select broker
    const env = getEnvMode()
    const broker = brokerOverride || selectBroker(assetClass, env)

    console.log(`[OrderStatusAPI] ${requestId} - Broker: ${broker}, OrderId: ${orderId}, Env: ${env}`)

    if (broker === 'unsupported') {
      return res.status(400).json({
        error: `Unsupported asset class: ${assetClass}`,
        timestamp: new Date().toISOString()
      })
    }

    // Fetch order status from selected broker
    let status: NormalizedOrderStatus

    switch (broker) {
      case 'alpaca':
        status = await getOrderStatusAlpaca(orderId)
        break
      
      case 'ibkr':
        status = await getOrderStatusIBKR(orderId)
        break
      
      case 'schwab':
        status = await getOrderStatusSchwab(orderId)
        break
      
      case 'mt5':
        status = await getOrderStatusMT5(orderId)
        break
      
      case 'binance':
        status = await getOrderStatusBinance(orderId)
        break
      
      case 'tradestation':
        status = await getOrderStatusTradeStation(orderId)
        break
      
      default:
        return res.status(400).json({
          error: `Unknown broker: ${broker}`,
          timestamp: new Date().toISOString()
        })
    }

    console.log(`[OrderStatusAPI] ${requestId} - Order status retrieved: ${status.status}`)

    return res.status(200).json({
      broker,
      status
    })

  } catch (err: any) {
    const message = err?.message || 'Unknown error occurred'
    
    console.error(`[OrderStatusAPI] ${requestId} - Error:`, message)

    return res.status(500).json({
      error: message,
      details: process.env.NODE_ENV === 'development' ? err?.stack : undefined,
      timestamp: new Date().toISOString()
    })
  }
}
