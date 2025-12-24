# Appwrite Functions Deployment Guide

This directory contains serverless functions ready for deployment to Appwrite Cloud.

## 📁 Directory Structure

```
appwrite-functions/
├── _shared/
│   └── appwriteClient.js          # Shared Appwrite SDK client
├── create_transaction/
│   └── index.js                   # Create transaction with RBAC
├── get_transactions/
│   └── index.js                   # Get transactions with RBAC
├── get_transactions_streamlit/
│   └── index.js                   # Get transactions (simplified for StreamLit)
├── add_to_watchlist_streamlit/
│   └── index.js                   # Add to watchlist (simplified for StreamLit)
├── get_user_profile_streamlit/
│   └── index.js                   # Get user profile (simplified for StreamLit)
└── get_watchlist_streamlit/
    └── index.js                   # Get watchlist (simplified for StreamLit)
```

## 🚀 Deployment Steps

### Method 1: Manual Upload via Appwrite Console

1. **Login to Appwrite Cloud Console**
   - Go to https://cloud.appwrite.io
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
   appwrite deploy function
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
