/**
 * BROKER UTILITIES
 * 
 * Shared helper functions for broker API integrations:
 * - OAuth2 token management (Schwab, TradeStation)
 * - HMAC signature generation (Binance)
 * - Session caching
 * - Common HTTP helpers
 */

import crypto from 'crypto'

// ============================================
// SESSION CACHE
// ============================================

interface CachedToken {
  token: string
  expires: number
}

const tokenCache: Map<string, CachedToken> = new Map()

export function getCachedToken(broker: string): string | null {
  const cached = tokenCache.get(broker)
  
  if (cached && cached.expires > Date.now()) {
    return cached.token
  }
  
  if (cached) {
    console.log(`[${broker}] Token expired, refresh needed`)
    tokenCache.delete(broker)
  }
  
  return null
}

export function cacheToken(broker: string, token: string, expiresInSeconds: number): void {
  tokenCache.set(broker, {
    token,
    expires: Date.now() + (expiresInSeconds * 1000)
  })
  console.log(`[${broker}] Token cached for ${expiresInSeconds}s`)
}

// ============================================
// OAUTH2 HELPERS (Schwab, TradeStation)
// ============================================

export async function refreshOAuth2Token(
  tokenUrl: string,
  clientId: string,
  clientSecret: string,
  refreshToken: string
): Promise<{ access_token: string; expires_in: number }> {
  const body = new URLSearchParams({
    grant_type: 'refresh_token',
    refresh_token: refreshToken,
    client_id: clientId,
    client_secret: clientSecret
  })

  const response = await fetch(tokenUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: body.toString()
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`OAuth2 token refresh failed: ${response.status} - ${errorText}`)
  }

  return response.json()
}

export async function getSchwabToken(): Promise<string> {
  const cached = getCachedToken('schwab')
  if (cached) return cached

  const clientId = process.env.SCHWAB_CLIENT_ID
  const clientSecret = process.env.SCHWAB_CLIENT_SECRET
  const refreshToken = process.env.SCHWAB_REFRESH_TOKEN

  if (!clientId || !clientSecret || !refreshToken) {
    throw new Error('Missing Schwab OAuth2 credentials: SCHWAB_CLIENT_ID, SCHWAB_CLIENT_SECRET, SCHWAB_REFRESH_TOKEN')
  }

  console.log('[Schwab] Refreshing OAuth2 token...')
  const tokenUrl = 'https://api.schwabapi.com/v1/oauth/token'
  const data = await refreshOAuth2Token(tokenUrl, clientId, clientSecret, refreshToken)

  cacheToken('schwab', data.access_token, data.expires_in)
  return data.access_token
}

export async function getTradeStationToken(): Promise<string> {
  const cached = getCachedToken('tradestation')
  if (cached) return cached

  const clientId = process.env.TRADESTATION_CLIENT_ID
  const clientSecret = process.env.TRADESTATION_CLIENT_SECRET
  const refreshToken = process.env.TRADESTATION_REFRESH_TOKEN

  if (!clientId || !clientSecret || !refreshToken) {
    throw new Error('Missing TradeStation OAuth2 credentials: TRADESTATION_CLIENT_ID, TRADESTATION_CLIENT_SECRET, TRADESTATION_REFRESH_TOKEN')
  }

  console.log('[TradeStation] Refreshing OAuth2 token...')
  const tokenUrl = 'https://api.tradestation.com/v3/oauth/token'
  const data = await refreshOAuth2Token(tokenUrl, clientId, clientSecret, refreshToken)

  cacheToken('tradestation', data.access_token, data.expires_in)
  return data.access_token
}

// ============================================
// BINANCE HMAC SIGNATURE
// ============================================

export function generateBinanceSignature(queryString: string, apiSecret: string): string {
  return crypto
    .createHmac('sha256', apiSecret)
    .update(queryString)
    .digest('hex')
}

export function createBinanceQueryString(params: Record<string, any>): string {
  const timestamp = Date.now()
  const allParams = { ...params, timestamp }
  
  return Object.keys(allParams)
    .sort()
    .map(key => `${key}=${encodeURIComponent(allParams[key])}`)
    .join('&')
}

export async function binanceGet(path: string, params: Record<string, any> = {}): Promise<any> {
  const apiKey = process.env.BINANCE_API_KEY
  const apiSecret = process.env.BINANCE_API_SECRET
  const baseUrl = process.env.BINANCE_API_URL || 'https://api.binance.com'

  if (!apiKey || !apiSecret) {
    throw new Error('Missing Binance credentials: BINANCE_API_KEY, BINANCE_API_SECRET')
  }

  const queryString = createBinanceQueryString(params)
  const signature = generateBinanceSignature(queryString, apiSecret)
  const url = `${baseUrl}${path}?${queryString}&signature=${signature}`

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'X-MBX-APIKEY': apiKey
    }
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Binance GET failed: ${response.status} - ${errorText}`)
  }

  return response.json()
}

// ============================================
// HTTP HELPERS
// ============================================

export async function httpGetWithAuth(
  url: string,
  token: string,
  authHeader: string = 'Authorization',
  authPrefix: string = 'Bearer'
): Promise<any> {
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      [authHeader]: `${authPrefix} ${token}`
    }
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`HTTP GET failed: ${response.status} - ${errorText}`)
  }

  return response.json()
}
