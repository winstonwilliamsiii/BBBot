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
