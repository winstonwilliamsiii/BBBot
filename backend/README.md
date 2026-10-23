# Backend API
Serverless functions and API endpoints for Mansa Capital platform.

## Structure
- /api - API endpoints (budget, transactions, orders, KYC)
- /services - External service connectors (brokerages, banks)
- /models - Database schemas and ORM models
- /utils - Shared utilities (auth, logging, validation)

## Runtime
- `Main.py` is the primary FastAPI application for local development.
- `backend/api/app.py` is a compatibility launcher that starts the same FastAPI app on port `5001` by default.
- `api/index.py` remains the lightweight Vercel/serverless handler for stateless production endpoints.

## Discord notifications
- The primary FastAPI app (`Main.py`) serves `POST /notify/signal` and `POST /tv-alert`.
- Set the matching `WEBHOOK_<BOT>` environment variable for each bot that should post to Discord. Create each webhook in the destination Discord channel and keep its URL private.
- EA signal requests include `bot_name`, `symbol`, `decision`, `cosmic_score`, and `mode`; `heads` is optional and carries ML insight data.
- Configure TradingView with a publicly reachable HTTPS URL ending in `/tv-alert`. Its JSON alert message must include `bot_name` and the configured `secret`; `screenshot` may contain a publicly accessible chart image URL, and `message` is optional. The secret can also be sent in the `X-TradingView-Secret` header.
- Set `TRADINGVIEW_WEBHOOK_SECRET` in the API environment and use the matching value in TradingView alert JSON. Requests fail closed if the server secret is not configured or does not match.
