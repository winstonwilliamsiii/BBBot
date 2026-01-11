#Railway_CashPro API Integration
#The script handles env var, token handling, endpoints and internal Authorization

import express from 'express';
import axios from 'axios';
import jwt from 'jsonwebtoken'; // only needed if you use JWT client assertion
import { randomUUID } from 'crypto';

const app = express();
app.use(express.json());

// Env vars
const {
  PORT = 3000,
  INTERNAL_API_KEY,           // shared secret between Vercel and Railway
  CASHPRO_CLIENT_ID,
  CASHPRO_CLIENT_SECRET,
  CASHPRO_TOKEN_URL,
  CASHPRO_API_BASE_URL,
  CASHPRO_JWT_PRIVATE_KEY,    // optional, if using JWT client assertion
} = process.env;

// Simple in-memory token cache (you can replace with Redis later)
let cachedToken = null;
let cachedTokenExpiry = 0;

// Middleware to verify internal calls from Vercel / Appwrite
function verifyInternalAuth(req, res, next) {
  const apiKey = req.headers['x-internal-api-key'];

  if (!INTERNAL_API_KEY || apiKey !== INTERNAL_API_KEY) {
    return res.status(401).json({
      status: 'error',
      message: 'Unauthorized',
    });
  }

  next();
}

// Helper: Get CashPro access token (client credentials, with optional JWT assertion)
async function getCashProToken() {
  const now = Math.floor(Date.now() / 1000);

  // Reuse token if still valid with some buffer
  if (cachedToken && cachedTokenExpiry - 60 > now) {
    return cachedToken;
  }

  const form = new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: CASHPRO_CLIENT_ID,
  });

  // If they require client_secret directly:
  if (CASHPRO_CLIENT_SECRET) {
    form.append('client_secret', CASHPRO_CLIENT_SECRET);
  }

  // If they require JWT client assertion:
  if (CASHPRO_JWT_PRIVATE_KEY) {
    const payload = {
      iss: CASHPRO_CLIENT_ID,
      sub: CASHPRO_CLIENT_ID,
      aud: CASHPRO_TOKEN_URL,
      exp: now + 300,
      jti: randomUUID(),
    };

    const clientAssertion = jwt.sign(payload, CASHPRO_JWT_PRIVATE_KEY, {
      algorithm: 'RS256',
    });

    form.append('client_assertion', clientAssertion);
    form.append(
      'client_assertion_type',
      'urn:ietf:params:oauth:client-assertion-type:jwt-bearer'
    );
  }

  const tokenResp = await axios({
    method: 'post',
    url: CASHPRO_TOKEN_URL,
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    data: form.toString(),
  });

  const { access_token, expires_in } = tokenResp.data;
  cachedToken = access_token;
  cachedTokenExpiry = now + (expires_in || 300);

  return access_token;
}

// Example: GET /balances
app.get('/balances', verifyInternalAuth, async (req, res) => {
  try {
    const accessToken = await getCashProToken();

    // You might pass account identifiers via query params
    const { accountId } = req.query;

    const resp = await axios({
      method: 'get',
      url: `${CASHPRO_API_BASE_URL}/balances`, // adjust path for CashPro
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      params: {
        accountId,
      },
    });

    return res.json({
      status: 'success',
      data: resp.data,
    });
  } catch (err) {
    console.error('Error in /balances:', err?.response?.data || err.message);

    return res.status(err?.response?.status || 500).json({
      status: 'error',
      error: err?.response?.data || { message: 'Unknown error' },
    });
  }
});

// Example: POST /payments
app.post('/payments', verifyInternalAuth, async (req, res) => {
  try {
    const accessToken = await getCashProToken();

    // Body will contain the payment instruction in your internal format
    const paymentPayload = req.body;

    const resp = await axios({
      method: 'post',
      url: `${CASHPRO_API_BASE_URL}/payments`, // adjust path from docs
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      data: paymentPayload,
    });

    return res.json({
      status: 'success',
      data: resp.data,
    });
  } catch (err) {
    console.error('Error in /payments:', err?.response?.data || err.message);

    return res.status(err?.response?.status || 500).json({
      status: 'error',
      error: err?.response?.data || { message: 'Unknown error' },
    });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  return res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`CashPro gateway listening on port ${PORT}`);
});