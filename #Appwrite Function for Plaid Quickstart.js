#Appwrite Function for Plaid Quickstart
#endpoint for Plaid backends

import axios from 'axios';

export default async ({ req, res, log, error }) => {
  const {
    PLAID_CLIENT_ID,
    PLAID_SECRET,
    PLAID_BASE_URL = 'https://sandbox.plaid.com'
  } = process.env;

  try {
    const path = req.path || '';
    const body = req.body ? JSON.parse(req.body) : {};

    // 1. Create Link Token
    if (path.endsWith('/create_link_token')) {
      const resp = await axios.post(`${PLAID_BASE_URL}/link/token/create`, {
        client_id: PLAID_CLIENT_ID,
        secret: PLAID_SECRET,
        user: { client_user_id: body.client_user_id || 'test-user' },
        client_name: 'BentleyBudgetBot',
        products: ['transactions'],
        country_codes: ['US'],
        language: 'en'
      });
      return res.json(resp.data);
    }

    // 2. Exchange Public Token for Access Token
    if (path.endsWith('/set_access_token')) {
      const resp = await axios.post(`${PLAID_BASE_URL}/item/public_token/exchange`, {
        client_id: PLAID_CLIENT_ID,
        secret: PLAID_SECRET,
        public_token: body.public_token
      });
      return res.json(resp.data);
    }

    // 3. Get Transactions
    if (path.endsWith('/transactions')) {
      const resp = await axios.post(`${PLAID_BASE_URL}/transactions/get`, {
        client_id: PLAID_CLIENT_ID,
        secret: PLAID_SECRET,
        access_token: body.access_token,
        start_date: body.start_date || '2024-01-01',
        end_date: body.end_date || '2024-12-31'
      });
      return res.json(resp.data);
    }

    return res.json({ error: 'Unknown endpoint' }, 404);
  } catch (err) {
    error(err.message);
    return res.json({ error: err.message }, 500);
  }
};