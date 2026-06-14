#Appwrite_CashPro_Function
#Pulls credentials from env vars Obtains an OAuth token (client credentials style) 
#Calls a CashPro API endpoint
#Returns a safe response

// Runtime: Node 18+ in Appwrite
import axios from 'axios';

export default async ({ req, res, log, error }) => {
  try {
    // 1. Environment variables (configure in Appwrite dashboard)
    const {
      CASHPRO_CLIENT_ID,
      CASHPRO_CLIENT_SECRET,
      CASHPRO_TOKEN_URL,
      CASHPRO_API_BASE_URL,
      CASHPRO_CERT_PATH,      // if using mTLS and file mount
      CASHPRO_CERT_KEY_PATH,  // if using mTLS
    } = process.env;

    // 2. Get OAuth access token (client credentials grant)
    const tokenResp = await axios({
      method: 'post',
      url: CASHPRO_TOKEN_URL, // e.g. https://auth.bankofamerica.com/... (check your docs)
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      data: new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: CASHPRO_CLIENT_ID,
        client_secret: CASHPRO_CLIENT_SECRET,
        // scope: 'your-scope-here' // if required
      }).toString(),
      // If CashPro requires mTLS for token:
      // httpsAgent: new https.Agent({
      //   cert: fs.readFileSync(CASHPRO_CERT_PATH),
      //   key: fs.readFileSync(CASHPRO_CERT_KEY_PATH),
      // })
    });

    const accessToken = tokenResp.data.access_token;

    // 3. Read request payload from caller (e.g. payment instruction)
    const body = req.body ? JSON.parse(req.body) : {};

    // 4. Call CashPro API (example: create payment)
    const paymentResp = await axios({
      method: 'post',
      url: `${CASHPRO_API_BASE_URL}/payments`, // adjust path from docs
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      data: body,
      // httpsAgent: ... // if mTLS also required for API calls
    });

    // 5. Return normalized response to your frontend / orchestrator
    return res.json({
      status: 'success',
      cashproResponse: paymentResp.data,
    });
  } catch (err) {
    error('CashPro function error', err?.message || err);

    const status = err?.response?.status || 500;
    const data = err?.response?.data || { message: 'Unknown error' };

    return res.json(
      {
        status: 'error',
        error: data,
      },
      status
    );
  }
};