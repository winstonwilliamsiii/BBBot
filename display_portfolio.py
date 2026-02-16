#!/usr/bin/env python
"""Test portfolio display in Streamlit page."""
import os
from dotenv import load_dotenv
import pandas as pd
from prediction_analytics.services.kalshi_client import KalshiClient

load_dotenv('.env.development')

# Mimic what the page does
KALSHI_API_KEY_ID = (
    os.getenv("KALSHI_API_KEY_ID", "")
    or os.getenv("KALSHI_ACCESS_KEY", "")
)
KALSHI_PRIVATE_KEY = os.getenv("KALSHI_PRIVATE_KEY", "")

if KALSHI_API_KEY_ID:
    print(f"✓ API Key ID: {KALSHI_API_KEY_ID[:20]}...")
else:
    print("✗ API Key ID: NOT SET")

if KALSHI_PRIVATE_KEY:
    print("✓ Private Key: loaded")
else:
    print("✗ Private Key: NOT SET")

client = KalshiClient(
    api_key_id=KALSHI_API_KEY_ID,
    private_key=KALSHI_PRIVATE_KEY
)
print(f"✓ Authenticated: {client.authenticated}")

positions = client.get_user_portfolio()
print(f"\n✓ Found {len(positions)} positions\n")

if positions:
    portfolio_list = []
    for pos in positions:
        contract_name = pos.get('ticker', 'Unknown')
        quantity = float(pos.get('position', 0))
        realized_pnl = float(pos.get('realized_pnl', 0))
        realized_pnl_dollars = float(pos.get('realized_pnl_dollars', 0))
        total_traded = float(pos.get('total_traded', 0))
        total_traded_dollars = float(pos.get('total_traded_dollars', 0))
        market_exposure_dollars = float(pos.get('market_exposure_dollars', 0))

        # Kalshi API returns values in cents, convert to dollars
        total_traded_dollars = total_traded_dollars / 100
        market_exposure_dollars = market_exposure_dollars / 100
        realized_pnl_dollars = realized_pnl_dollars / 100
        
        if total_traded and total_traded != 0:
            entry_price = total_traded_dollars / total_traded
        else:
            entry_price = 0

        if quantity and quantity != 0:
            current_price = market_exposure_dollars / quantity
        else:
            current_price = entry_price

        cost_basis = (
            abs(total_traded_dollars) if total_traded_dollars else 0
        )
        current_value = (
            abs(market_exposure_dollars) if market_exposure_dollars else 0
        )
        pnl = realized_pnl_dollars
        pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
        
        entry_price_str = (
            f"${entry_price:.4f}" if entry_price else "N/A"
        )
        current_price_str = (
            f"${current_price:.4f}" if current_price else "N/A"
        )

        portfolio_list.append({
            'Exchange': 'Kalshi',
            'Contract': contract_name,
            'Quantity': int(quantity),
            'Entry Price': entry_price_str,
            'Current Price': current_price_str,
            'P&L': f"${pnl:.2f}",
            'P&L %': f"{pnl_pct:+.2f}%" if pnl_pct else "0%"
        })
    
    df = pd.DataFrame(portfolio_list)
    print("Your Kalshi Portfolio:")
    print("=" * 100)
    print(df.to_string(index=False))
    print("=" * 100)
    balance = client.get_user_balance()
    if balance:
        balance_dollars = balance.get('balance', 0) / 100
        portfolio_value_dollars = balance.get('portfolio_value', 0) / 100
        print(f"\nBalance: ${balance_dollars:.2f} cash, ${portfolio_value_dollars:.2f} portfolio value")
        print(f"Raw API response: {balance}")
    else:
        print("\nNo balance data")

