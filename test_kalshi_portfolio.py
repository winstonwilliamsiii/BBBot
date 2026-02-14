#!/usr/bin/env python
"""Quick test of Kalshi portfolio fetching."""
import os
from dotenv import load_dotenv

load_dotenv('.env.development')

from prediction_analytics.services.kalshi_client import KalshiClient

api_key = os.getenv('KALSHI_ACCESS_KEY')
private_key = os.getenv('KALSHI_PRIVATE_KEY')

print(f'API Key loaded: {bool(api_key)}')
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
        print(f'  Contract: {pos.get("contract_ticker", pos.get("ticker", "Unknown"))}')
        print(f'  Quantity: {pos.get("quantity", pos.get("position", 0))}')
        print(f'  Entry Price: {pos.get("purchase_price", pos.get("cost_basis", "N/A"))}')
else:
    print('No positions returned')

print('\nFetching balance...')
balance = client.get_user_balance()
if balance:
    print(f'Balance: {balance}')
else:
    print('No balance data')
