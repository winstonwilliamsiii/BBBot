#!/usr/bin/env python
"""Quick test of Kalshi portfolio fetching."""
import os
from dotenv import load_dotenv

load_dotenv('.env.development')

from prediction_analytics.services.kalshi_client import KalshiClient

api_key = os.getenv('KALSHI_API_KEY_ID') or os.getenv('KALSHI_ACCESS_KEY')
private_key = os.getenv('KALSHI_PRIVATE_KEY')

print(f'API Key ID loaded: {bool(api_key)}')
if api_key:
    print(f'  Key: {api_key[:20]}...')
print(f'Private Key loaded: {bool(private_key)}')

client = KalshiClient(api_key_id=api_key, private_key=private_key)
print(f'Authenticated: {client.authenticated}')
if client.last_error:
    print(f'Error: {client.last_error}')

print('\nFetching portfolio...')
positions = client.get_user_portfolio()
print(f'Positions count: {len(positions)}')
if positions:
    print(f'First position keys: {list(positions[0].keys())}')
    for i, pos in enumerate(positions[:3]):
        print(f'\nPosition {i+1}:')
        print(f'  Contract: {pos.get("ticker", "Unknown")}')
        print(f'  Quantity: {pos.get("position", 0)}')
        print(f'  Total Traded: {pos.get("total_traded", 0)}')
        total_traded_dollars = pos.get("total_traded_dollars", 0)
        market_exposure_dollars = pos.get("market_exposure_dollars", 0)
        realized_pnl_dollars = pos.get("realized_pnl_dollars", 0)
        # Kalshi API returns values in cents, convert to dollars
        print(f'  Total Traded $: ${float(total_traded_dollars) / 100 if total_traded_dollars else 0:.2f}')
        print(f'  Market Exposure $: ${float(market_exposure_dollars) / 100 if market_exposure_dollars else 0:.2f}')
        print(f'  Realized P&L $: ${float(realized_pnl_dollars) / 100 if realized_pnl_dollars else 0:.2f}')
else:
    print('No positions returned')

print('\nFetching balance...')
balance = client.get_user_balance()
if balance:
    print(f'Balance (raw): {balance}')
    # Kalshi API returns values in cents, convert to dollars
    balance_dollars = balance.get('balance', 0) / 100
    portfolio_value_dollars = balance.get('portfolio_value', 0) / 100
    print(f'Balance: ${balance_dollars:.2f} cash, ${portfolio_value_dollars:.2f} portfolio value')
else:
    print('No balance data')
