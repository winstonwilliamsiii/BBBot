# Appwrite Functions

**Last Updated:** December 25, 2025

This directory contains 16 serverless functions for the BBBot platform, ready for deployment to Appwrite Cloud.

## 📁 Directory Structure

```
appwrite-functions/
├── _shared/                       # Shared utilities (included in each deployment)
│   └── appwriteClient.js         # Appwrite SDK client factory
│
├── DEPLOYMENT_GUIDE.md            # Complete deployment instructions
├── ISSUES_AND_FIXES.md            # Troubleshooting and fixes history
├── README.md                      # This file
│
├── create_transaction/            # Transaction Functions
│   ├── index.js
│   └── package.json
├── get_transactions/
│   ├── index.js
│   └── package.json
├── get_transactions_streamlit/
│   ├── index.js
│   └── package.json
│
├── add_to_watchlist_streamlit/    # Watchlist Functions
│   ├── index.js
│   └── package.json
├── get_watchlist_streamlit/
│   ├── index.js
│   └── package.json
├── get_user_profile_streamlit/
│   ├── index.js
│   └── package.json
│
├── create_audit_log/              # Audit & Payment Functions
│   ├── index.js
│   └── package.json
├── get_audit_logs/
│   ├── index.js
│   └── package.json
├── create_payment/
│   ├── index.js
│   └── package.json
├── get_payments/
│   ├── index.js
│   └── package.json
│
├── manage_roles/                  # RBAC Functions
│   ├── index.js
│   └── package.json
├── manage_permissions/
│   ├── index.js
│   └── package.json
│
├── create_bot_metric/             # Bot Metrics Functions
│   ├── index.js
│   └── package.json
├── get_bot_metrics/
│   ├── index.js
│   └── package.json
├── get_bot_metrics_stats/
│   ├── index.js
│   └── package.json
│
└── create_all_indexes/            # Utility Functions
    ├── index.js
    └── package.json
```

## 🚀 Quick Start

### Deploy All Functions (3 Commands)

```powershell
# 1. Package functions
.\package-appwrite-functions-targz.ps1

# 2. Login to Appwrite
cd appwrite-deployments-targz
appwrite login

# 3. Deploy all functions
appwrite push function --all
```

**Done!** All 16 functions deployed to Appwrite Cloud.

## 📚 Documentation

- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Complete deployment instructions (CLI & Console)
- **[ISSUES_AND_FIXES.md](./ISSUES_AND_FIXES.md)** - Known issues, fixes, and troubleshooting

## 📋 Available Functions (16)

| Category | Function | Description |
|----------|----------|-------------|
| **Transactions** | `create_transaction` | Create transaction with RBAC |
| | `get_transactions` | Get transactions with RBAC |
| | `get_transactions_streamlit` | Simplified for Streamlit |
| **Watchlist** | `add_to_watchlist_streamlit` | Add to watchlist |
| | `get_watchlist_streamlit` | Get watchlist |
| | `get_user_profile_streamlit` | Get user profile |
| **Audit & Payment** | `create_audit_log` | Create audit log entry |
| | `get_audit_logs` | Retrieve audit logs |
| | `create_payment` | Create payment record |
| | `get_payments` | Get payment history |
| **RBAC** | `manage_roles` | Create/list roles |
| | `manage_permissions` | Create/list permissions |
| **Bot Metrics** | `create_bot_metric` | Record bot metric |
| | `get_bot_metrics` | Query bot metrics |
| | `get_bot_metrics_stats` | Get statistical analysis |
| **Utility** | `create_all_indexes` | Create all DB indexes (run once) |

## 🔧 Development

### Function Structure

Each function follows this pattern:

```javascript
const { createClient } = require('./_shared/appwriteClient');

module.exports = async function (req, res) {
    try {
        // Get environment variables
        const { endpoint, projectId, apiKey, databaseId } = {
            endpoint: process.env.APPWRITE_FUNCTION_ENDPOINT,
            projectId: process.env.APPWRITE_FUNCTION_PROJECT_ID,
            apiKey: process.env.APPWRITE_API_KEY,
            databaseId: process.env.APPWRITE_DATABASE_ID
        };

        // Create Appwrite client
        const { databases } = createClient({ endpoint, projectId, apiKey });

        // Parse request body
        const body = JSON.parse(req.body || '{}');

        // Your function logic here
        const result = await databases.listDocuments(databaseId, 'collection_id');

        // Return response
        return res.json({ success: true, data: result });
    } catch (error) {
        return res.json({ error: error.message }, 400);
    }
};
```

### Required Environment Variables

Each function requires these 4 variables:

```bash
APPWRITE_FUNCTION_ENDPOINT=https://fra.cloud.appwrite.io/v1
APPWRITE_FUNCTION_PROJECT_ID=68869ef500017ca73772
APPWRITE_API_KEY=<your-server-api-key>
APPWRITE_DATABASE_ID=<your-database-id>
```

### Shared Module

The `_shared/appwriteClient.js` provides a reusable Appwrite SDK client:

```javascript
const sdk = require('node-appwrite');

function createClient({ endpoint, projectId, apiKey }) {
    const client = new sdk.Client()
        .setEndpoint(endpoint)
        .setProject(projectId)
        .setKey(apiKey);

    return {
        client,
        databases: new sdk.Databases(client),
        users: new sdk.Users(client)
    };
}

module.exports = { createClient };
```

## 🧪 Testing Functions Locally

### Run Test Script
```powershell
# Test function logic locally
node appwrite-functions/get_transactions_streamlit/index.js
```

### Mock Request/Response
```javascript
// test-function.js
const handler = require('./appwrite-functions/get_transactions_streamlit/index.js');

const mockReq = {
    body: JSON.stringify({ user_id: 'test123', limit: 10 })
};

const mockRes = {
    json: (data, status = 200) => {
        console.log('Status:', status);
        console.log('Response:', JSON.stringify(data, null, 2));
    }
};

handler(mockReq, mockRes);
```

## 📦 Package Structure

After running `.\package-appwrite-functions-targz.ps1`, each tar.gz contains:

```
get_transactions_streamlit.tar.gz
├── index.js                   # Main function code
├── package.json               # Node.js dependencies
└── _shared/                   # Shared utilities
    └── appwriteClient.js      # Appwrite client factory
```

**Key Points:**
- `_shared/` is included in EACH package
- All requires use `./_shared/...` (same level)
- Entry point is always `index.js`

## 🔍 Troubleshooting

### Module Not Found Error
```
Error: Cannot find module './_shared/appwriteClient'
```

**Fix:**
1. Verify require path: `require('./_shared/appwriteClient')` not `require('../_shared/appwriteClient')`
2. Repackage: `.\package-appwrite-functions-targz.ps1`
3. Check tar.gz contains `_shared/` folder

### Environment Variables Not Set
```
Error: Cannot read property 'endpoint' of undefined
```

**Fix:**
1. Go to Appwrite Console → Function → Settings → Variables
2. Add all 4 required environment variables
3. Redeploy function

### Build Fails
```
Error: npm install failed
```

**Fix:**
1. Check `package.json` exists in function directory
2. Verify `node-appwrite: ^11.0.0` in dependencies
3. Review build logs in Appwrite Console

For more troubleshooting, see [ISSUES_AND_FIXES.md](./ISSUES_AND_FIXES.md)

## 📚 Additional Resources

- **Deployment Guide:** [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **Issues & Fixes:** [ISSUES_AND_FIXES.md](./ISSUES_AND_FIXES.md)
- **Appwrite Functions Docs:** https://appwrite.io/docs/products/functions
- **Appwrite Node.js SDK:** https://appwrite.io/docs/sdks#server

## 🆘 Support

If you encounter issues:

1. Check [ISSUES_AND_FIXES.md](./ISSUES_AND_FIXES.md) for known problems
2. Review function logs in Appwrite Console
3. Verify environment variables are set
4. Test with simple execution payload

---

**Project:** BBBot - Bentley Budget Bot  
**Status:** All 16 functions ready for deployment ✅  
**Last Updated:** December 25, 2025

   - Navigate to your project

2. **For Each Function:**
   - Click "Functions" in the sidebar
   - Click "Create Function"
   - Choose "Node.js 18.0" or latest runtime
   - Upload the entire function folder (e.g., `get_transactions_streamlit/`)
   - Set the entrypoint as `index.js`

3. **Configure Environment Variables:**
   ```
   APPWRITE_FUNCTION_ENDPOINT=https://cloud.appwrite.io/v1
   APPWRITE_FUNCTION_PROJECT_ID=your_project_id
   APPWRITE_API_KEY=your_api_key
   APPWRITE_DATABASE_ID=your_database_id
   ```

4. **Set Function Permissions:**
   - For StreamLit functions: Set to "Any" or specific user roles
   - For RBAC functions: Set appropriate role-based permissions

5. **Deploy and Test:**
   - Click "Deploy"
   - Test using the built-in executor or your frontend

### Method 2: Appwrite CLI Deployment

1. **Install Appwrite CLI:**
   ```bash
   npm install -g appwrite-cli
   ```

2. **Login to Appwrite:**
   ```bash
   appwrite login
   ```

3. **Initialize Project:**
   ```bash
   appwrite init project
   ```

4. **Deploy Functions:**
   ```bash
   appwrite push function
   ```

## 📋 Function Details

### StreamLit Functions (Simplified - No RBAC)
These functions are designed for direct StreamLit integration:

- **get_transactions_streamlit**: Retrieve transactions for a user
  - Body: `{ "user_id": "string", "limit": 100 }`
  
- **add_to_watchlist_streamlit**: Add symbol to watchlist
  - Body: `{ "user_id": "string", "symbol": "AAPL" }`
  
- **get_user_profile_streamlit**: Get user profile
  - Body: `{ "userId": "string" }`
  
- **get_watchlist_streamlit**: Get user's watchlist
  - Body: `{ "user_id": "string" }`

### RBAC-Protected Functions
These functions include role-based access control:

- **create_transaction**: Create a new transaction
  - Body: `{ "requester_id": "string", "user_id": "string", "amount": 100.50, "description": "Purchase" }`
  
- **get_transactions**: Get transactions with authorization
  - Body: `{ "requester_id": "string", "user_id": "string", "limit": 100 }`

## 🔧 Database Indexes

The transaction-related functions include commented index creation utilities. Run these once during initial setup:

```javascript
await databases.createIndex(
    databaseId,
    'transactions',
    'idx_transactions_user_date',
    'key',
    ['user_id', 'date'],
    ['ASC', 'DESC']
);
```

## 🔗 Calling Functions from StreamLit

Example Python code for StreamLit:

```python
import requests
import json

APPWRITE_ENDPOINT = "https://cloud.appwrite.io/v1"
PROJECT_ID = "your_project_id"
FUNCTION_ID = "your_function_id"

def get_transactions(user_id, limit=100):
    url = f"{APPWRITE_ENDPOINT}/functions/{FUNCTION_ID}/executions"
    headers = {
        "Content-Type": "application/json",
        "X-Appwrite-Project": PROJECT_ID
    }
    body = json.dumps({
        "user_id": user_id,
        "limit": limit
    })
    
    response = requests.post(url, headers=headers, data=body)
    return response.json()
```

## 📝 Notes

- **Dependencies**: Each function requires `node-appwrite` package
- **Runtime**: Node.js 18.0 or higher recommended
- **Timeout**: Default 15s, adjust if needed for complex operations
- **Memory**: 512MB default, increase for data-intensive operations
- **Shared Code**: The `_shared/` folder must be uploaded with each function

## 🔐 Security Considerations

1. **API Keys**: Use server-side API keys with appropriate scopes
2. **RBAC Functions**: Validate requester permissions before data access
3. **StreamLit Functions**: Consider adding API key authentication
4. **Rate Limiting**: Configure rate limits in Appwrite Console
5. **Environment Variables**: Never commit secrets to version control

## 🐛 Troubleshooting

- **Module Not Found**: Ensure `_shared` folder is uploaded
- **Authorization Errors**: Verify environment variables are set
- **Database Errors**: Check collection names and attribute types
- **Timeout Errors**: Increase function timeout or optimize queries

## 📚 Additional Resources

- [Appwrite Functions Documentation](https://appwrite.io/docs/functions)
- [Appwrite Node.js SDK](https://appwrite.io/docs/sdks#node)
- [BentleyBot Architecture](../README.md)
