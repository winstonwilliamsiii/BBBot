# Bank of America CashPro Integration Guide

## Overview

**Status:** ✅ Complete - Alternative to Plaid for business bank accounts

This integration provides seamless connection to Bank of America business accounts via the CashPro API. It serves as a fallback option when Plaid encounters issues or when working with BofA business accounts.

## Features

✅ **OAuth 2.0 Authentication** - Secure client credentials flow  
✅ **Current Day Transactions** - Real-time transaction inquiry  
✅ **Account Balance Retrieval** - Check current account balances  
✅ **Transaction Sync** - Automatic sync to transactions table  
✅ **Sandbox & Production** - Full environment support  
✅ **Streamlit Integration** - User-friendly connection form  

## API Endpoints Implemented

### 1. OAuth Token Endpoint
```http
POST https://api.bankofamerica.com/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id={CLIENT_ID}
&client_secret={CLIENT_SECRET}
&scope=cashpro.reporting
```

### 2. Current Day Transaction Inquiry
```http
POST https://api.bankofamerica.com/cashpro/reporting/v1/transaction-inquiries/current-day
Authorization: Bearer {ACCESS_TOKEN}
X-API-Key: {API_KEY}

{
  "accountNumber": "123456789",
  "transactionDate": "2024-01-15",
  "pageSize": 100,
  "pageNumber": 1
}
```

### 3. Account Balance (Optional)
```http
POST https://api.bankofamerica.com/cashpro/reporting/v1/account-balances
Authorization: Bearer {ACCESS_TOKEN}
X-API-Key: {API_KEY}

{
  "accountNumber": "123456789"
}
```

## Setup Instructions

### Step 1: Get CashPro API Credentials

1. **Contact BofA** - Reach out to your Bank of America relationship manager
2. **Request API Access** - Ask for CashPro API developer credentials
3. **Receive Credentials:**
   - `BOFA_CLIENT_ID` - OAuth client ID
   - `BOFA_CLIENT_SECRET` - OAuth client secret
   - `BOFA_API_KEY` - API key for requests

### Step 2: Configure Environment

**For Local Development (.env file):**
```bash
# Bank of America CashPro API
BOFA_CLIENT_ID=your_client_id_here
BOFA_CLIENT_SECRET=your_client_secret_here
BOFA_API_KEY=your_api_key_here
BOFA_ENV=sandbox  # or production
```

**For Streamlit Cloud (Secrets):**
```toml
# .streamlit/secrets.toml
BOFA_CLIENT_ID = "your_client_id_here"
BOFA_CLIENT_SECRET = "your_client_secret_here"
BOFA_API_KEY = "your_api_key_here"
BOFA_ENV = "sandbox"
```

### Step 3: Test Connection

1. Go to **Personal Budget** page
2. Select **"💼 Bank of America CashPro"** radio button
3. Enter your **BofA account number**
4. Enter an **account nickname** (e.g., "Business Checking")
5. Select **days of history to sync** (1-90 days)
6. Click **"🔗 Connect BofA Account"**

## Sandbox Testing

**Environment:** `sandbox`

The sandbox environment returns sample transaction data for testing:

```python
BOFA_ENV = "sandbox"
```

- Use any account number (e.g., "123456789")
- Returns mock transaction data
- No real bank connection required
- Perfect for development and testing

## Production Use

**Environment:** `production`

For live business accounts:

```python
BOFA_ENV = "production"
```

- Requires active CashPro account
- Uses real account numbers
- Returns actual transaction data
- Subject to API rate limits

## Database Integration

### Tables Used

**plaid_items** - Reused for BofA connections:
```sql
INSERT INTO plaid_items (item_id, user_id, access_token, institution_name)
VALUES (
  'bofa_{account_number}',  -- Prefixed with 'bofa_'
  {user_id},
  '{account_number}',       -- Account number stored as access token
  'Bank of America CashPro'
);
```

**transactions** - Standard transaction storage:
```sql
INSERT INTO transactions (
  user_id, account_id, amount, date, name, 
  merchant_name, category, pending, transaction_id
)
VALUES (
  {user_id},
  '{account_number}',
  {amount},
  '{transaction_date}',
  '{description}',
  '{merchant_name}',
  '{category}',
  FALSE,  -- BofA transactions are settled
  'bofa_{reference_number}'
);
```

## Code Architecture

### Main Components

1. **BofACashProClient** (`frontend/utils/bofa_cashpro.py`)
   - OAuth 2.0 authentication
   - Transaction retrieval
   - Account balance checking
   - Token management

2. **render_bofa_connection_form()** (`frontend/utils/bofa_cashpro.py`)
   - Streamlit UI form
   - User input handling
   - Connection testing
   - Transaction sync trigger

3. **Budget Dashboard Integration** (`frontend/components/budget_dashboard.py`)
   - Radio button selector (Plaid vs BofA)
   - Conditional rendering
   - Error handling

### Key Functions

```python
# Authentication
client = BofACashProClient()
if client.authenticate():
    print("Authenticated successfully!")

# Get current day transactions
result = client.get_current_day_transactions(
    account_number="123456789",
    transaction_date="2024-01-15"
)

# Sync transactions to database
count = sync_bofa_transactions(
    user_id=1,
    account_number="123456789",
    days_back=30
)
print(f"Synced {count} transactions")

# Save connection
save_bofa_connection(
    user_id=1,
    account_number="123456789",
    account_name="Business Checking"
)
```

## API Rate Limits

Bank of America CashPro API rate limits (typical):

- **Sandbox:** 100 requests/minute
- **Production:** 60 requests/minute
- **Daily limit:** 10,000 requests/day

**Our implementation includes:**
- Token caching (reduces auth requests)
- Error handling with retries
- Batch transaction processing

## Error Handling

### Common Errors

**1. Authentication Failed (401)**
```
Error: Authentication failed: 401
Solution: Check BOFA_CLIENT_ID and BOFA_CLIENT_SECRET
```

**2. Invalid API Key (403)**
```
Error: API Error 403
Solution: Verify BOFA_API_KEY is correct
```

**3. Invalid Account Number (404)**
```
Error: API Error 404
Solution: Ensure account number format is correct
```

**4. Rate Limit Exceeded (429)**
```
Error: API Error 429
Solution: Wait 60 seconds and retry
```

## Security Considerations

✅ **Credentials stored securely** - Streamlit secrets or .env (gitignored)  
✅ **OAuth 2.0 flow** - Industry standard authentication  
✅ **Token expiration** - Automatic token refresh  
✅ **HTTPS only** - All API calls encrypted  
✅ **No password storage** - Uses API keys only  

## Comparison: Plaid vs BofA CashPro

| Feature | Plaid | BofA CashPro |
|---------|-------|--------------|
| **Bank Support** | 12,000+ banks | BofA only |
| **Account Type** | Consumer + Business | Business only |
| **Setup Time** | 5 minutes | 1-2 weeks |
| **Cost** | Free (sandbox) | Enterprise pricing |
| **Transaction History** | Up to 2 years | Up to 90 days |
| **Real-time Data** | Yes | Yes |
| **OAuth Flow** | User consent | API keys |
| **Best For** | Consumer accounts | BofA business accounts |

## When to Use Each

### Use Plaid When:
- Connecting consumer bank accounts
- Need multi-bank support
- Want quick setup without approval process
- Testing with sandbox data

### Use BofA CashPro When:
- Already have BofA business account
- Plaid connection issues
- Need BofA-specific features
- Enterprise compliance requirements

## Troubleshooting

### Issue: "Authentication failed"
**Check:**
1. Credentials are in Streamlit secrets or .env
2. BOFA_ENV is set correctly (sandbox/production)
3. API key is active

### Issue: "No transactions synced"
**Check:**
1. Account number is correct
2. Transaction date range is valid
3. Transactions exist in that date range
4. Database connection is working

### Issue: "Connection form not showing"
**Check:**
1. Radio button selected properly
2. No Python import errors
3. Check browser console for errors

## API Documentation

**Official Docs:** https://developer.bankofamerica.com/cashpro/apis

**Key Resources:**
- API Reference Guide
- OAuth 2.0 Implementation
- Transaction Inquiry Specs
- Rate Limit Guidelines

## Support

**Technical Issues:**
- Check Streamlit logs for errors
- Review `bofa_cashpro.py` error messages
- Test authentication separately

**BofA API Issues:**
- Contact BofA API support team
- Reference your Client ID in support requests
- Check API status page for outages

## Future Enhancements

Potential additions:

- [ ] Multi-account support (multiple BofA accounts)
- [ ] Historical transaction retrieval (previous days endpoint)
- [ ] Payment initiation (send money via API)
- [ ] Account management (update settings)
- [ ] Wire transfer tracking
- [ ] ACH transaction monitoring

## Files Modified

- ✅ `frontend/utils/bofa_cashpro.py` - **NEW** - Complete BofA API client
- ✅ `frontend/components/budget_dashboard.py` - Added radio button selector
- ✅ `docs/BOFA_CASHPRO_INTEGRATION.md` - **NEW** - This documentation

## Deployment

**Status:** ✅ Deployed to production

**URL:** https://bbbot305.streamlit.app/Personal_Budget

**Test It:**
1. Log in as Admin
2. Go to Personal Budget
3. Select "💼 Bank of America CashPro"
4. Enter account details
5. Click Connect

---

**Last Updated:** January 2025  
**Author:** Winston Williams III  
**Version:** 1.0.0
