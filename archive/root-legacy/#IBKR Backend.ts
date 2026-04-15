#IBKR Backend 

// lib/ibkr.ts
import fetch from 'node-fetch'

const IBKR_BASE_URL = process.env.IBKR_BASE_URL || 'https://localhost:5000/v1/api'

async function ensureSession() {
  const resp = await fetch(`${IBKR_BASE_URL}/iserver/auth/status`, { method: 'GET' })
  const json = await resp.json()
  if (!json.authenticated) {
    await fetch(`${IBKR_BASE_URL}/iserver/reauthenticate`, { method: 'POST' })
  }
}

export async function ibkrTrade(order: {
  symbol: string
  qty: number
  side: 'BUY' | 'SELL'
  type?: string
}) {
  await ensureSession()
  const payload = {
    orders: [
      {
        conid: order.symbol, // IBKR contract ID, not ticker
        orderType: order.type || 'MKT',
        side: order.side,
        quantity: order.qty,
      },
    ],
  }
  const resp = await fetch(`${IBKR_BASE_URL}/iserver/account/orders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return resp.json()
}

export async function ibkrPositions(accountId: string) {
  await ensureSession()
  const resp = await fetch(`${IBKR_BASE_URL}/portfolio/${accountId}/positions`, { method: 'GET' })
  return resp.json()
}

export async function ibkrBalance(accountId: string) {
  await ensureSession()
  const resp = await fetch(`${IBKR_BASE_URL}/portfolio/${accountId}/summary`, { method: 'GET' })
  return resp.json()
}