# Trading Scripts

This directory contains scripts related to trading operations, order management, and broker interactions.

## Scripts Overview

### Order Management
- **`place_turb_supx_orders.py`** - Script for placing TURB and SUPX orders
- **`cancel_duplicate_turb.py`** - Remove duplicate TURB orders
- **`cancel_spy_order.py`** - Cancel SPY orders
- **`fix_supx_protection.py`** - Fix protection settings for SUPX orders

## Usage

These scripts are designed to be run directly from the command line:

```bash
# From repository root
python scripts/trading/place_turb_supx_orders.py

# Or from scripts/trading directory
cd scripts/trading
python place_turb_supx_orders.py
```

## Prerequisites

- Ensure all required environment variables are set (`.env` file configured)
- Install dependencies: `pip install -r requirements.txt`
- Configure broker API credentials in your environment

## Safety Notes

⚠️ **IMPORTANT**:
- These scripts interact with live trading accounts
- Always test in paper trading mode first
- Verify orders before execution
- Monitor positions after running scripts
- Keep logs of all trading activities

## Related Documentation

- See `/docs/BRACKET_ORDER_DEPLOYMENT.md` for bracket order deployment
- See `/docs/TURB_SUPX_ORDER_SUMMARY.md` for TURB/SUPX order details
- See `/config/env-templates/.env.brokers.example` for broker configuration
