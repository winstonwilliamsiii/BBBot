/**
 * POSITIONS API - Get current positions from brokers
 * 
 * GET /api/positions?class=equities&broker=alpaca
 * 
 * Returns normalized position data across all brokers
 */

import type { NextApiRequest, NextApiResponse } from 'next'
import { getSchwabToken, getTradeStationToken, binanceGet, httpGetWithAuth } from './lib/broker-utils'

type EnvMode = 'MVP' | 'PRODUCTION'
type AssetClass = 'equities' | 'futures' | 'options' | 'forex' | 'crypto'

interface NormalizedPosition {
  broker: string
  symbol: string
  qty: number
  avgPrice?: number
  marketValue?: number
  unrealizedPnL?: number
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
  console.log('[Alpaca] Fetching positions...')
  const json = await alpacaGet('/v2/positions')
  const positions = normalizeAlpacaPositions(json)
  console.log(`[Alpaca] Found ${positions.length} positions`)
  return positions
}

// ============================================
// IBKR ADAPTER (Stub)
// ============================================

async function getPositionsIBKR(): Promise<NormalizedPosition[]> {
  console.warn('[IBKR] Positions adapter not yet implemented')
  
  // When ready, implement:
  // const gatewayUrl = process.env.IBKR_GATEWAY_URL || 'http://localhost:5000'
  // const accountId = process.env.IBKR_ACCOUNT_ID
  // const response = await fetch(`${gatewayUrl}/v1/api/portfolio/${accountId}/positions`)
  // return normalizeIBKRPositions(await response.json())
  
  return []
}

// ============================================
// SCHWAB ADAPTER
// ============================================

import { getSchwabToken, httpGetWithAuth } from './lib/broker-utils'

async function getPositionsSchwab(): Promise<NormalizedPosition[]> {
  console.log('[Schwab] Fetching positions...')
  
  const accountId = process.env.SCHWAB_ACCOUNT_ID
  const apiUrl = process.env.SCHWAB_API_URL || 'https://api.schwabapi.com'

  if (!accountId) {
    throw new Error('Missing SCHWAB_ACCOUNT_ID')
  }

  const token = await getSchwabToken()
  const url = `${apiUrl}/trader/v1/accounts/${accountId}/positions`
  const data = await httpGetWithAuth(url, token)

  const positions: NormalizedPosition[] = (data.securitiesAccount?.positions || []).map((p: any) => ({
    broker: 'schwab',
    symbol: p?.instrument?.symbol ?? '',
    qty: p?.longQuantity ? Number(p.longQuantity) : (p?.shortQuantity ? -Number(p.shortQuantity) : 0),
    avgPrice: p?.averagePrice ? Number(p.averagePrice) : undefined,
    marketValue: p?.marketValue ? Number(p.marketValue) : undefined,
    unrealizedPnL: p?.currentDayProfitLoss ? Number(p.currentDayProfitLoss) : undefined,
    raw: p
  }))

  console.log(`[Schwab] Found ${positions.length} positions`)
  return positions
}

// ============================================
// MT5 ADAPTER (Stub)
// ============================================

async function getPositionsMT5(): Promise<NormalizedPosition[]> {
  console.warn('[MT5] Positions adapter not yet implemented')
  
  // When ready, implement:
  // const apiUrl = process.env.MT5_API_URL || 'http://localhost:8000'
  // const response = await fetch(`${apiUrl}/positions`)
  // return normalizeMT5Positions(await response.json())
  
  return []
}

// ============================================
// BINANCE ADAPTER
// ============================================

import { binanceGet } from './lib/broker-utils'

async function getPositionsBinance(): Promise<NormalizedPosition[]> {
  console.log('[Binance] Fetching positions...')
  
  // Binance uses /api/v3/account for positions
  const accountData = await binanceGet('/api/v3/account', {})

  const positions: NormalizedPosition[] = (accountData.balances || [])
    .filter((b: any) => Number(b.free) > 0 || Number(b.locked) > 0)
    .map((b: any) => {
      const qty = Number(b.free) + Number(b.locked)
      return {
        broker: 'binance',
        symbol: b.asset,
        qty,
        avgPrice: undefined, // Binance doesn't provide avg price in account endpoint
        marketValue: undefined, // Would need to fetch current price
        unrealizedPnL: undefined,
        raw: b
      }
    })

  console.log(`[Binance] Found ${positions.length} positions`)
  return positions
}

// ============================================
// TRADESTATION ADAPTER
// ============================================

async function getPositionsTradeStation(): Promise<NormalizedPosition[]> {
  console.log('[TradeStation] Fetching positions...')
  
  const accountId = process.env.TRADESTATION_ACCOUNT_ID
  const apiUrl = process.env.TRADESTATION_API_URL || 'https://api.tradestation.com'

  if (!accountId) {
    throw new Error('Missing TRADESTATION_ACCOUNT_ID')
  }

  const token = await getTradeStationToken()
  const url = `${apiUrl}/v3/accounts/${accountId}/positions`
  const data = await httpGetWithAuth(url, token)

  const positions: NormalizedPosition[] = (data.Positions || []).map((p: any) => ({
    broker: 'tradestation',
    symbol: p?.Symbol ?? '',
    qty: p?.Quantity ? Number(p.Quantity) : 0,
    avgPrice: p?.AveragePrice ? Number(p.AveragePrice) : undefined,
    marketValue: p?.MarketValue ? Number(p.MarketValue) : undefined,
    unrealizedPnL: p?.UnrealizedProfitLoss ? Number(p.UnrealizedProfitLoss) : undefined,
    raw: p
  }))

  console.log(`[TradeStation] Found ${positions.length} positions`)
  return positions
}

// ============================================
// MAIN HANDLER
// ============================================

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<{ broker: string; positions: NormalizedPosition[] } | ErrorResponse>
) {
  const requestId = `positions_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  
  console.log(`[PositionsAPI] ${requestId} - Request received`)

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

    console.log(`[PositionsAPI] ${requestId} - Broker: ${broker}, Asset: ${assetClass}, Env: ${env}`)

    if (broker === 'unsupported') {
      return res.status(400).json({
        error: `Unsupported asset class: ${assetClass}`,
        timestamp: new Date().toISOString()
      })
    }

    // Fetch positions from selected broker
    let positions: NormalizedPosition[] = []

    switch (broker) {
      case 'alpaca':
        positions = await getPositionsAlpaca()
        break
      
      case 'ibkr':
        positions = await getPositionsIBKR()
        break
      
      case 'schwab':
        positions = await getPositionsSchwab()
        break
      
      case 'mt5':
        positions = await getPositionsMT5()
        break
      
      case 'binance':
        positions = await getPositionsBinance()
        break
      
      case 'tradestation':
        positions = await getPositionsTradeStation()
        break
      
      default:
        return res.status(400).json({
          error: `Unknown broker: ${broker}`,
          timestamp: new Date().toISOString()
        })
    }

    console.log(`[PositionsAPI] ${requestId} - Retrieved ${positions.length} positions`)

    return res.status(200).json({
      broker,
      positions
    })

  } catch (err: any) {
    const message = err?.message || 'Unknown error occurred'
    
    console.error(`[PositionsAPI] ${requestId} - Error:`, message)

    return res.status(500).json({
      error: message,
      details: process.env.NODE_ENV === 'development' ? err?.stack : undefined,
      timestamp: new Date().toISOString()
    })
  }
}
