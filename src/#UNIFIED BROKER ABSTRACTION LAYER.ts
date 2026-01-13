/**
 * UNIFIED BROKER ABSTRACTION LAYER
 * Production-ready broker orchestration with:
 * - Environment routing (MVP vs PRODUCTION)
 * - Automatic fallback on broker failures
 * - Thin adapter pattern for each broker
 * - Comprehensive observability & audit logging
 * - Session management & retry logic
 */

import type { NextApiRequest, NextApiResponse } from 'next'

// ============================================
// TYPE DEFINITIONS
// ============================================

type BrokerName = 'alpaca' | 'ibkr' | 'schwab' | 'ninjatrader' | 'tradestation' | 'mt5' | 'binance'
type AssetClass = 'equities' | 'futures' | 'options' | 'forex' | 'crypto'
type Environment = 'MVP' | 'PRODUCTION'

interface Asset {
  class: AssetClass
  symbol: string
  qty: number
  side: 'buy' | 'sell'
  limitPrice?: number
  stopPrice?: number
  params?: Record<string, any>
}

interface BrokerResponse {
  broker: BrokerName
  status: 'success' | 'error' | 'pending'
  orderId?: string
  error?: string
  asset: Asset
  timestamp: string
  retryCount?: number
}

interface BrokerHealth {
  broker: BrokerName
  healthy: boolean
  lastCheck: string
  responseTime?: number
  error?: string
}

// ============================================
// STRUCTURED LOGGER
// ============================================

const logger = {
  info: (message: string, meta?: any) => 
    console.log(JSON.stringify({ 
      level: 'INFO', 
      message, 
      ...meta, 
      timestamp: new Date().toISOString() 
    })),
  
  warn: (message: string, meta?: any) => 
    console.warn(JSON.stringify({ 
      level: 'WARN', 
      message, 
      ...meta, 
      timestamp: new Date().toISOString() 
    })),
  
  error: (message: string, meta?: any) => 
    console.error(JSON.stringify({ 
      level: 'ERROR', 
      message, 
      ...meta, 
      timestamp: new Date().toISOString() 
    })),

  audit: (action: string, meta?: any) =>
    console.log(JSON.stringify({
      level: 'AUDIT',
      action,
      ...meta,
      timestamp: new Date().toISOString()
    }))
}

// ============================================
// ENVIRONMENT & CONFIGURATION
// ============================================

function getEnvironment(): Environment {
  const env = (process.env.APP_ENV as Environment) || 'MVP'
  
  if (env !== 'MVP' && env !== 'PRODUCTION') {
    logger.warn('Invalid APP_ENV value, defaulting to MVP', { providedEnv: env })
    return 'MVP'
  }
  
  logger.info('Environment configured', { environment: env })
  return env
}

// Broker preferences by asset class and environment
const BROKER_PREFERENCES: Record<AssetClass, Record<Environment, BrokerName[]>> = {
  equities: { 
    MVP: ['alpaca'], 
    PRODUCTION: ['ibkr', 'schwab', 'alpaca'] 
  },
  futures: { 
    MVP: ['ninjatrader'], 
    PRODUCTION: ['tradestation', 'ibkr'] 
  },
  options: { 
    MVP: ['ibkr'], 
    PRODUCTION: ['ibkr', 'schwab'] 
  },
  forex: { 
    MVP: ['mt5'], 
    PRODUCTION: ['ibkr', 'mt5'] 
  },
  crypto: { 
    MVP: ['binance'], 
    PRODUCTION: ['binance'] 
  },
}

// Session cache for broker authentication tokens
const sessionCache: Map<BrokerName, { token: string; expires: number }> = new Map()

// ============================================
// BROKER HEALTH CHECKS
// ============================================

async function isBrokerHealthy(broker: BrokerName): Promise<boolean> {
  const startTime = Date.now()
  
  try {
    let healthEndpoint: string
    let headers: Record<string, string> = {}

    switch (broker) {
      case 'alpaca':
        healthEndpoint = process.env.ALPACA_API_URL || 'https://paper-api.alpaca.markets'
        headers = { 'APCA-API-KEY-ID': process.env.ALPACA_KEY || '' }
        break
      
      case 'ibkr':
        healthEndpoint = (process.env.IBKR_GATEWAY_URL || 'http://localhost:5000') + '/v1/api/tickle'
        break
      
      case 'schwab':
        healthEndpoint = process.env.SCHWAB_API_URL || 'https://api.schwabapi.com'
        break
      
      case 'ninjatrader':
        healthEndpoint = process.env.NT_API_URL || 'http://localhost:9000/health'
        break
      
      case 'tradestation':
        healthEndpoint = process.env.TS_API_URL || 'https://api.tradestation.com'
        break
      
      case 'mt5':
        healthEndpoint = process.env.MT5_API_URL || 'http://localhost:8000/health'
        break
      
      case 'binance':
        healthEndpoint = process.env.BINANCE_API_URL || 'https://api.binance.com/api/v3/ping'
        break
      
      default:
        logger.warn('Unknown broker for health check', { broker })
        return false
    }

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 3000) // 3s timeout

    const response = await fetch(healthEndpoint, {
      method: 'GET',
      headers,
      signal: controller.signal
    })

    clearTimeout(timeoutId)
    const responseTime = Date.now() - startTime
    const healthy = response.ok

    logger.info('Broker health check completed', {
      broker,
      healthy,
      responseTime,
      statusCode: response.status
    })

    return healthy

  } catch (error: any) {
    const responseTime = Date.now() - startTime
    logger.warn('Broker health check failed', {
      broker,
      error: error.message,
      responseTime
    })
    return false
  }
}

// ============================================
// SESSION MANAGEMENT
// ============================================

async function refreshSession(broker: BrokerName): Promise<string | null> {
  logger.info('Refreshing broker session', { broker })

  try {
    switch (broker) {
      case 'alpaca':
        // Alpaca uses API keys (no session refresh needed)
        return process.env.ALPACA_KEY || null
      
      case 'ibkr':
        // IBKR Gateway session refresh
        const ibkrUrl = process.env.IBKR_GATEWAY_URL || 'http://localhost:5000'
        const authResp = await fetch(`${ibkrUrl}/v1/api/iserver/auth/status`, {
          method: 'POST'
        })
        
        if (authResp.ok) {
          const data = await authResp.json()
          const token = data.sessionId || 'IBKR_SESSION'
          sessionCache.set(broker, {
            token,
            expires: Date.now() + 3600000 // 1 hour
          })
          logger.info('Session refreshed successfully', { broker })
          return token
        }
        break
      
      case 'schwab':
        // OAuth2 token refresh logic
        const refreshToken = process.env.SCHWAB_REFRESH_TOKEN
        if (!refreshToken) return null
        
        const schwabResp = await fetch('https://api.schwabapi.com/v1/oauth/token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({
            grant_type: 'refresh_token',
            refresh_token: refreshToken,
            client_id: process.env.SCHWAB_CLIENT_ID || ''
          })
        })
        
        if (schwabResp.ok) {
          const data = await schwabResp.json()
          sessionCache.set(broker, {
            token: data.access_token,
            expires: Date.now() + data.expires_in * 1000
          })
          logger.info('Session refreshed successfully', { broker })
          return data.access_token
        }
        break

      default:
        // For other brokers, implement as needed
        logger.info('No session refresh logic for broker', { broker })
        return null
    }
  } catch (error: any) {
    logger.error('Session refresh failed', { broker, error: error.message })
    return null
  }

  return null
}

function getSession(broker: BrokerName): string | null {
  const cached = sessionCache.get(broker)
  
  if (cached && cached.expires > Date.now()) {
    return cached.token
  }
  
  // Session expired or not found
  if (cached) {
    logger.info('Session expired, refresh required', { broker })
  }
  
  return null
}

// ============================================
// BROKER SELECTOR WITH FALLBACK
// ============================================

async function selectBroker(asset: Asset, env: Environment): Promise<BrokerName> {
  const candidates = BROKER_PREFERENCES[asset.class][env] || []
  
  logger.audit('Broker selection initiated', {
    assetClass: asset.class,
    symbol: asset.symbol,
    environment: env,
    candidates
  })

  if (candidates.length === 0) {
    throw new Error(`No broker configured for asset class: ${asset.class}`)
  }

  for (const broker of candidates) {
    logger.info('Checking broker health', { broker, assetClass: asset.class })
    
    if (await isBrokerHealthy(broker)) {
      logger.audit('Broker selected', {
        broker,
        assetClass: asset.class,
        symbol: asset.symbol,
        environment: env
      })
      return broker
    }
    
    logger.warn('Broker unhealthy, trying fallback', { broker, assetClass: asset.class })
  }

  throw new Error(`No healthy brokers available for ${asset.class}`)
}

// ============================================
// PAYLOAD MAPPERS
// ============================================

function mapToAlpacaPayload(asset: Asset) {
  return {
    symbol: asset.symbol,
    qty: asset.qty,
    side: asset.side,
    type: asset.limitPrice ? 'limit' : 'market',
    limit_price: asset.limitPrice,
    time_in_force: 'day'
  }
}

function mapToIBKRPayload(asset: Asset) {
  return {
    conid: asset.params?.conid, // Contract ID from IBKR
    orderType: asset.limitPrice ? 'LMT' : 'MKT',
    side: asset.side.toUpperCase(),
    quantity: asset.qty,
    price: asset.limitPrice
  }
}

function mapToSchwabPayload(asset: Asset) {
  return {
    orderType: asset.limitPrice ? 'LIMIT' : 'MARKET',
    session: 'NORMAL',
    duration: 'DAY',
    orderStrategyType: 'SINGLE',
    orderLegCollection: [{
      instruction: asset.side.toUpperCase(),
      quantity: asset.qty,
      instrument: {
        symbol: asset.symbol,
        assetType: 'EQUITY'
      }
    }],
    price: asset.limitPrice
  }
}

function mapToMT5Payload(asset: Asset) {
  return {
    symbol: asset.symbol,
    volume: asset.qty,
    action: asset.side === 'buy' ? 'ORDER_TYPE_BUY' : 'ORDER_TYPE_SELL',
    type: asset.limitPrice ? 'ORDER_TYPE_BUY_LIMIT' : 'ORDER_TYPE_BUY',
    price: asset.limitPrice || 0
  }
}

function mapToBinancePayload(asset: Asset) {
  return {
    symbol: asset.symbol.replace('/', ''), // BTC/USDT -> BTCUSDT
    side: asset.side.toUpperCase(),
    type: asset.limitPrice ? 'LIMIT' : 'MARKET',
    quantity: asset.qty,
    price: asset.limitPrice,
    timeInForce: 'GTC'
  }
}

// ============================================
// BROKER ADAPTERS
// ============================================

async function alpacaTrade(asset: Asset): Promise<BrokerResponse> {
  const broker: BrokerName = 'alpaca'
  
  try {
    const apiUrl = process.env.ALPACA_API_URL || 'https://paper-api.alpaca.markets'
    const apiKey = process.env.ALPACA_KEY
    const apiSecret = process.env.ALPACA_SECRET
    
    if (!apiKey || !apiSecret) {
      throw new Error('Alpaca credentials not configured')
    }

    const response = await fetch(`${apiUrl}/v2/orders`, {
      method: 'POST',
      headers: {
        'APCA-API-KEY-ID': apiKey,
        'APCA-API-SECRET-KEY': apiSecret,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(mapToAlpacaPayload(asset))
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.message || 'Alpaca API error')
    }

    const data = await response.json()
    
    logger.audit('Trade executed', {
      broker,
      orderId: data.id,
      symbol: asset.symbol,
      qty: asset.qty,
      side: asset.side
    })

    return {
      broker,
      status: 'success',
      orderId: data.id,
      asset,
      timestamp: new Date().toISOString()
    }

  } catch (error: any) {
    logger.error('Alpaca trade failed', {
      broker,
      error: error.message,
      asset
    })

    return {
      broker,
      status: 'error',
      error: error.message,
      asset,
      timestamp: new Date().toISOString()
    }
  }
}

async function ibkrTrade(asset: Asset): Promise<BrokerResponse> {
  const broker: BrokerName = 'ibkr'
  
  try {
    const gatewayUrl = process.env.IBKR_GATEWAY_URL || 'http://localhost:5000'
    
    // Check/refresh session
    let session = getSession(broker)
    if (!session) {
      session = await refreshSession(broker)
      if (!session) {
        throw new Error('IBKR session authentication failed')
      }
    }

    const accountId = process.env.IBKR_ACCOUNT_ID
    
    const response = await fetch(`${gatewayUrl}/v1/api/iserver/account/${accountId}/orders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(mapToIBKRPayload(asset))
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || 'IBKR API error')
    }

    const data = await response.json()
    
    logger.audit('Trade executed', {
      broker,
      orderId: data.order_id,
      symbol: asset.symbol,
      qty: asset.qty,
      side: asset.side
    })

    return {
      broker,
      status: 'success',
      orderId: data.order_id,
      asset,
      timestamp: new Date().toISOString()
    }

  } catch (error: any) {
    logger.error('IBKR trade failed', {
      broker,
      error: error.message,
      asset
    })

    return {
      broker,
      status: 'error',
      error: error.message,
      asset,
      timestamp: new Date().toISOString()
    }
  }
}

async function schwabTrade(asset: Asset): Promise<BrokerResponse> {
  const broker: BrokerName = 'schwab'
  
  try {
    // Check/refresh session
    let token = getSession(broker)
    if (!token) {
      token = await refreshSession(broker)
      if (!token) {
        throw new Error('Schwab authentication failed')
      }
    }

    const accountId = process.env.SCHWAB_ACCOUNT_ID
    const apiUrl = process.env.SCHWAB_API_URL || 'https://api.schwabapi.com'

    const response = await fetch(`${apiUrl}/trader/v1/accounts/${accountId}/orders`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(mapToSchwabPayload(asset))
    })

    if (!response.ok) {
      throw new Error('Schwab API error')
    }

    const orderId = response.headers.get('Location')?.split('/').pop() || 'UNKNOWN'

    logger.audit('Trade executed', {
      broker,
      orderId,
      symbol: asset.symbol,
      qty: asset.qty,
      side: asset.side
    })

    return {
      broker,
      status: 'success',
      orderId,
      asset,
      timestamp: new Date().toISOString()
    }

  } catch (error: any) {
    logger.error('Schwab trade failed', {
      broker,
      error: error.message,
      asset
    })

    return {
      broker,
      status: 'error',
      error: error.message,
      asset,
      timestamp: new Date().toISOString()
    }
  }
}

async function mt5Trade(asset: Asset): Promise<BrokerResponse> {
  const broker: BrokerName = 'mt5'
  
  try {
    const apiUrl = process.env.MT5_API_URL || 'http://localhost:8000'
    
    const response = await fetch(`${apiUrl}/trade`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(mapToMT5Payload(asset))
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || 'MT5 API error')
    }

    const data = await response.json()

    logger.audit('Trade executed', {
      broker,
      orderId: data.order,
      symbol: asset.symbol,
      qty: asset.qty,
      side: asset.side
    })

    return {
      broker,
      status: 'success',
      orderId: String(data.order),
      asset,
      timestamp: new Date().toISOString()
    }

  } catch (error: any) {
    logger.error('MT5 trade failed', {
      broker,
      error: error.message,
      asset
    })

    return {
      broker,
      status: 'error',
      error: error.message,
      asset,
      timestamp: new Date().toISOString()
    }
  }
}

async function binanceTrade(asset: Asset): Promise<BrokerResponse> {
  const broker: BrokerName = 'binance'
  
  try {
    const apiKey = process.env.BINANCE_API_KEY
    const apiSecret = process.env.BINANCE_API_SECRET
    
    if (!apiKey || !apiSecret) {
      throw new Error('Binance credentials not configured')
    }

    const apiUrl = process.env.BINANCE_API_URL || 'https://api.binance.com'
    const payload = mapToBinancePayload(asset)
    
    // Add timestamp and signature (simplified - use proper HMAC signing in production)
    const timestamp = Date.now()
    const queryString = new URLSearchParams({ ...payload, timestamp: String(timestamp) }).toString()

    const response = await fetch(`${apiUrl}/api/v3/order?${queryString}`, {
      method: 'POST',
      headers: {
        'X-MBX-APIKEY': apiKey
      }
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.msg || 'Binance API error')
    }

    const data = await response.json()

    logger.audit('Trade executed', {
      broker,
      orderId: String(data.orderId),
      symbol: asset.symbol,
      qty: asset.qty,
      side: asset.side
    })

    return {
      broker,
      status: 'success',
      orderId: String(data.orderId),
      asset,
      timestamp: new Date().toISOString()
    }

  } catch (error: any) {
    logger.error('Binance trade failed', {
      broker,
      error: error.message,
      asset
    })

    return {
      broker,
      status: 'error',
      error: error.message,
      asset,
      timestamp: new Date().toISOString()
    }
  }
}

// Stub adapters for other brokers
async function ninjatraderTrade(asset: Asset): Promise<BrokerResponse> {
  const broker: BrokerName = 'ninjatrader'
  logger.warn('NinjaTrader adapter not fully implemented', { asset })
  
  return {
    broker,
    status: 'error',
    error: 'Not implemented',
    asset,
    timestamp: new Date().toISOString()
  }
}

async function tradestationTrade(asset: Asset): Promise<BrokerResponse> {
  const broker: BrokerName = 'tradestation'
  logger.warn('TradeStation adapter not fully implemented', { asset })
  
  return {
    broker,
    status: 'error',
    error: 'Not implemented',
    asset,
    timestamp: new Date().toISOString()
  }
}

// ============================================
// RETRY LOGIC WITH EXPONENTIAL BACKOFF
// ============================================

async function executeTradeWithRetry(
  broker: BrokerName,
  asset: Asset,
  maxRetries: number = 3
): Promise<BrokerResponse> {
  let lastError: BrokerResponse | null = null
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    logger.info('Executing trade attempt', {
      broker,
      attempt: attempt + 1,
      maxRetries,
      symbol: asset.symbol
    })

    let result: BrokerResponse

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
      case 'ninjatrader':
        result = await ninjatraderTrade(asset)
        break
      case 'tradestation':
        result = await tradestationTrade(asset)
        break
      default:
        return {
          broker,
          status: 'error',
          error: 'Unsupported broker',
          asset,
          timestamp: new Date().toISOString()
        }
    }

    if (result.status === 'success') {
      result.retryCount = attempt
      return result
    }

    lastError = result

    if (attempt < maxRetries - 1) {
      const backoffMs = Math.pow(2, attempt) * 1000 // Exponential backoff: 1s, 2s, 4s
      logger.info('Trade failed, retrying with backoff', {
        broker,
        attempt: attempt + 1,
        backoffMs,
        error: result.error
      })
      await new Promise(resolve => setTimeout(resolve, backoffMs))
    }
  }

  logger.error('Trade failed after max retries', {
    broker,
    maxRetries,
    asset,
    lastError: lastError?.error
  })

  return lastError!
}

// ============================================
// MAIN TRADE EXECUTOR
// ============================================

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  
  logger.audit('Trade request received', {
    requestId,
    method: req.method,
    body: req.body
  })

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const asset: Asset = req.body

    // Validate asset payload
    if (!asset.class || !asset.symbol || !asset.qty || !asset.side) {
      logger.error('Invalid asset payload', { requestId, asset })
      return res.status(400).json({ 
        error: 'Invalid asset payload. Required: class, symbol, qty, side' 
      })
    }

    // Get environment and select broker
    const env = getEnvironment()
    const broker = await selectBroker(asset, env)

    logger.info('Broker selected, executing trade', {
      requestId,
      broker,
      environment: env,
      asset: {
        class: asset.class,
        symbol: asset.symbol,
        qty: asset.qty,
        side: asset.side
      }
    })

    // Execute trade with retry logic
    const result = await executeTradeWithRetry(broker, asset)

    logger.audit('Trade request completed', {
      requestId,
      broker,
      status: result.status,
      orderId: result.orderId
    })

    const statusCode = result.status === 'success' ? 200 : 500
    return res.status(statusCode).json({ ...result, requestId })

  } catch (error: any) {
    logger.error('Trade request failed with exception', {
      requestId,
      error: error.message,
      stack: error.stack
    })

    return res.status(500).json({
      error: error.message,
      requestId,
      timestamp: new Date().toISOString()
    })
  }
}