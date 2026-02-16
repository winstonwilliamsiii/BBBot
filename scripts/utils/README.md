# Utility Scripts

This directory contains general utility scripts for testing, debugging, and helper functions.

## Scripts Overview

### Quick Tests & Utilities
- **`quick_alpaca_test.py`** - Quick test script for Alpaca API connectivity
- **`display_portfolio.py`** - Display portfolio information and holdings
- **`Main.py`** - General utility/test script

## Usage

Run these scripts directly from the command line:

```bash
# From repository root
python scripts/utils/quick_alpaca_test.py

# Or from scripts/utils directory
cd scripts/utils
python quick_alpaca_test.py
```

## Purpose

These utility scripts are for:
- **Quick Testing**: Rapidly verify API connections and configurations
- **Debugging**: Troubleshoot issues with accounts and data
- **Development**: Helper scripts during feature development
- **Demonstrations**: Example code for common operations

## Prerequisites

- Environment variables configured (`.env` file)
- Required dependencies installed: `pip install -r requirements.txt`
- API credentials for services being tested

## Related Directories

- `/tests/` - Full test suite with pytest
- `/scripts/trading/` - Production trading scripts
- `/scripts/` - Other management and setup scripts
