# Environment Templates

This directory contains template environment files for various deployment scenarios and configurations.

## Usage

1. Copy the appropriate template file to the root directory
2. Rename it to `.env` (or the appropriate name for your environment)
3. Fill in your actual credentials and configuration values
4. Never commit actual `.env` files with real credentials

## Available Templates

- **`.env.example`** - Main application environment template with all standard variables
- **`.env.template`** - Alternative main template
- **`.env.development.example`** - Development environment configuration
- **`.env.production.example`** - Production environment configuration
- **`.env.local.template`** - Local development overrides
- **`.env.brokers`** - Broker API credentials template (Alpaca, IBKR, etc.)
- **`.env.brokers.example`** - Alternative broker credentials template
- **`.env.brokers.updated`** - Updated broker configuration template
- **`.env.mt5.example`** - MetaTrader 5 integration configuration
- **`.env.railway-prediction`** - Railway deployment for prediction analytics
- **`.env.rbac.template`** - Role-Based Access Control configuration
- **`.env.backup_20260112_094253`** - Backup of environment configuration

## Security Notes

⚠️ **IMPORTANT**: 
- Never commit files with actual credentials
- All `.env` files (except templates) are ignored by git
- Keep your credentials secure and rotate them regularly
- Use different credentials for development and production
