/**
 * Appwrite Function for Plaid Quickstart
 * Endpoint for Plaid backend operations
 * 
 * Environment Variables (from .env file):
 * ----------------------------------------
 * Required:
 *   PLAID_CLIENT_ID         - Your Plaid Client ID (from .env line 95)
 *   PLAID_SECRET            - Your Plaid Secret (from .env line 96)
 *   PLAID_ENV               - Environment: sandbox/development/production (from .env line 97)
 * 
 * Auto-provided by Appwrite:
 *   APPWRITE_FUNCTION_PROJECT_ID  - Project ID (auto-injected)
 *   APPWRITE_FUNCTION_ENDPOINT    - API endpoint (auto-injected)
 * 
 * Optional (for database storage):
 *   APPWRITE_API_KEY              - From .env line 16
 *   APPWRITE_DATABASE_ID          - From .env line 19
 *   PLAID_ITEMS_COLLECTION_ID     - Collection ID for plaid_items table
 * 
 * Endpoints:
 * ----------
 * - GET  /api/info              - Health check
 * - POST /api/create_link_token - Create Plaid Link token
 * - POST /api/set_access_token  - Exchange public token for access token
 * - POST /api/transactions      - Get transactions
 * - POST /api/accounts          - Get account balances
 */

import { Client, Databases, Query } from 'node-appwrite';

import axios from 'axios';

export default async ({ req, res, log, error }) => {
  const {
    PLAID_CLIENT_ID,
    PLAID_SECRET,
    PLAID_ENV = 'sandbox',
    APPWRITE_FUNCTION_PROJECT_ID,
    APPWRITE_API_KEY,
    APPWRITE_DATABASE_ID,
    PLAID_ITEMS_COLLECTION_ID
  } = process.env;

  const PLAID_BASE_URL = PLAID_ENV === 'production' 
    ? 'https://production.plaid.com'
    : PLAID_ENV === 'development'
    ? 'https://development.plaid.com'
    : 'https://sandbox.plaid.com';

  // Parse request body - handle both JSON and form-encoded
  let body = {};
  const contentType = req.headers['content-type'] || '';
  
  if (contentType.includes('application/json')) {
    try {
      body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
    } catch (e) {
      body = req.body || {};
    }
  } else if (contentType.includes('application/x-www-form-urlencoded')) {
    // Parse form-encoded data (for token exchange from frontend)
    const params = new URLSearchParams(req.body || '');
    body = Object.fromEntries(params.entries());
  }

  const path = req.path || req.url || '';
  log(`Request: ${req.method} ${path}`);

  try {
    // 0. Health Check / Info
    if (path.endsWith('/api/info') || path === '/') {
      return res.json({
        status: 'ok',
        service: 'plaid-quickstart',
        version: '1.0.0',
        plaid_env: PLAID_ENV,
        timestamp: new Date().toISOString()
      });
    }

    // 1. Create Link Token
    if (path.endsWith('/api/create_link_token') || path.endsWith('/create_link_token')) {
      log(`Creating link token for user: ${body.user_id || body.client_user_id || 'test-user'}`);
      
      const resp = await axios.post(`${PLAID_BASE_URL}/link/token/create`, {
        client_id: PLAID_CLIENT_ID,
        secret: PLAID_SECRET,
        user: { 
          client_user_id: body.user_id || body.client_user_id || 'test-user' 
        },
        client_name: 'BentleyBudgetBot',
        products: body.products || ['transactions'],
        country_codes: body.country_codes || ['US'],
        language: body.language || 'en',
        webhook: body.webhook || undefined
      });
      
      log(`Link token created: ${resp.data.link_token}`);
      return res.json(resp.data);
    }

    // 2. Exchange Public Token for Access Token
    if (path.endsWith('/api/set_access_token') || path.endsWith('/set_access_token')) {
      const publicToken = body.public_token;
      
      if (!publicToken) {
        error('Missing public_token in request');
        return res.json({ error: 'Missing public_token' }, 400);
      }
      
      log(`Exchanging public token: ${publicToken.substring(0, 20)}...`);
      
      const resp = await axios.post(`${PLAID_BASE_URL}/item/public_token/exchange`, {
        client_id: PLAID_CLIENT_ID,
        secret: PLAID_SECRET,
        public_token: publicToken
      });
      
      const { access_token, item_id } = resp.data;
      log(`Access token obtained for item: ${item_id}`);
      
      // Store in Appwrite Database (optional - if configured)
      if (APPWRITE_API_KEY && APPWRITE_DATABASE_ID && PLAID_ITEMS_COLLECTION_ID) {
        try {
          const client = new Client()
            .setEndpoint(process.env.APPWRITE_FUNCTION_ENDPOINT || 'https://fra.cloud.appwrite.io/v1')
            .setProject(APPWRITE_FUNCTION_PROJECT_ID)
            .setKey(APPWRITE_API_KEY);
          
          const databases = new Databases(client);
          
          // Check if item already exists
          const existing = await databases.listDocuments(
            APPWRITE_DATABASE_ID,
            PLAID_ITEMS_COLLECTION_ID,
            [Query.equal('item_id', item_id)]
          );
          
          if (existing.documents.length === 0) {
            await databases.createDocument(
              APPWRITE_DATABASE_ID,
              PLAID_ITEMS_COLLECTION_ID,
              'unique()',
              {
                user_id: body.user_id || 'test-user',
                tenant_id: body.tenant_id || null,
                item_id: item_id,
                access_token: access_token,
                institution_id: body.institution_id || null,
                status: 'active',
                created_at: new Date().toISOString()
              }
            );
            log(`Stored access token in database for item: ${item_id}`);
          }
        } catch (dbError) {
          error(`Database storage failed: ${dbError.message}`);
          // Continue even if DB storage fails
        }
      }
      
      return res.json({
        access_token,
        item_id,
        success: true
      });
    }

    // 3. Get Accounts
    if (path.endsWith('/api/accounts') || path.endsWith('/accounts')) {
      const accessToken = body.access_token || body.accessToken;
      
      if (!accessToken) {
        return res.json({ error: 'Missing access_token' }, 400);
      }
      
      log('Fetching account balances');
      
      const resp = await axios.post(`${PLAID_BASE_URL}/accounts/balance/get`, {
        client_id: PLAID_CLIENT_ID,
        secret: PLAID_SECRET,
        access_token: accessToken
      });
      
      return res.json({
        accounts: resp.data.accounts,
        item: resp.data.item
      });
    }

    // 4. Get Transactions
    if (path.endsWith('/api/transactions') || path.endsWith('/transactions')) {
      const accessToken = body.access_token || body.accessToken;
      const startDate = body.start_date || '2024-01-01';
      const endDate = body.end_date || new Date().toISOString().split('T')[0];
      
      if (!accessToken) {
        return res.json({ error: 'Missing access_token' }, 400);
      }
      
      log(`Fetching transactions from ${startDate} to ${endDate}`);
      
      const resp = await axios.post(`${PLAID_BASE_URL}/transactions/get`, {
        client_id: PLAID_CLIENT_ID,
        secret: PLAID_SECRET,
        access_token: accessToken,
        start_date: startDate,
        end_date: endDate
      });
      
      return res.json({
        transactions: resp.data.transactions,
        accounts: resp.data.accounts,
        total_transactions: resp.data.total_transactions
      });
    }

    // Unknown endpoint
    error(`Unknown endpoint: ${path}`);
    return res.json({ error: `Unknown endpoint: ${path}` }, 404);
    
  } catch (err) {
    const errorMsg = err.response?.data || err.message;
    error(`Error: ${JSON.stringify(errorMsg)}`);
    return res.json({ 
      error: errorMsg,
      status: err.response?.status || 500
    }, err.response?.status || 500);
  }
};