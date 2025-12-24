# StreamLit Dashboard Deployment Guide

Your StreamLit dashboard (`streamlit_dashboard.py`) is now configured to connect to your Appwrite serverless functions!

## 📁 Created Files

```
services/
├── __init__.py                  # Package initialization
├── transactions.py              # Transaction service (calls Appwrite Functions)
└── watchlist.py                 # Watchlist service (calls Appwrite Functions)

streamlit_dashboard.py           # Main dashboard UI
.env.example                     # Environment variable template
```

## 🚀 Setup Instructions

### Step 1: Deploy Appwrite Functions

First, deploy your serverless functions to Appwrite Cloud (from `appwrite-functions/` directory):

1. Go to https://cloud.appwrite.io → Your Project → Functions
2. Create and deploy these functions:
   - `get_transactions_streamlit`
   - `add_to_watchlist_streamlit`
   - `get_watchlist_streamlit`

3. **Note the Function IDs** for each deployed function (you'll need them next)

### Step 2: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your Appwrite details in `.env`:
   ```env
   APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
   APPWRITE_PROJECT_ID=your_actual_project_id
   
   # Function IDs from Step 1
   APPWRITE_FUNCTION_ID_GET_TRANSACTIONS=6abc123def...
   APPWRITE_FUNCTION_ID_ADD_WATCHLIST=6abc456ghi...
   APPWRITE_FUNCTION_ID_GET_WATCHLIST=6abc789jkl...
   ```

### Step 3: Install Dependencies

```bash
pip install streamlit python-dotenv requests
```

Or add to your `requirements.txt`:
```
streamlit>=1.28.0
python-dotenv>=1.0.0
requests>=2.31.0
```

### Step 4: Run StreamLit Dashboard

```bash
streamlit run streamlit_dashboard.py
```

## 🔧 How It Works

### Architecture Flow

```
StreamLit Dashboard (streamlit_dashboard.py)
    ↓
Service Layer (services/transactions.py, services/watchlist.py)
    ↓
HTTP Requests to Appwrite Functions
    ↓
Appwrite Serverless Functions (get_transactions_streamlit, etc.)
    ↓
Appwrite Database Collections
```

### Service Functions

**transactions.py**:
- `create_transaction(user_id, amount, date)` - Create new transaction
- `get_transactions(user_id, limit)` - Retrieve user transactions

**watchlist.py**:
- `add_to_watchlist(user_id, symbol)` - Add symbol to watchlist
- `get_watchlist(user_id)` - Get user's watchlist

Each service function:
1. Reads Appwrite configuration from environment variables
2. Makes HTTP POST request to Appwrite Function endpoint
3. Parses the response from `responseBody`
4. Returns data to StreamLit UI

## 🎯 Usage Example

```python
# In your StreamLit app
from services.transactions import get_transactions

user_id = "user123"
transactions = get_transactions(user_id, limit=50)

if transactions.get("success"):
    st.dataframe(transactions["transactions"])
else:
    st.error(transactions.get("error"))
```

## 🔐 Security Notes

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Function Permissions** - Set appropriate permissions in Appwrite Console
3. **Rate Limiting** - Configure rate limits for your functions
4. **User Authentication** - Consider adding Appwrite Auth for user sessions

## 🐛 Troubleshooting

### "Missing Appwrite configuration" Error
- Ensure `.env` file exists and contains all required variables
- Check that environment variables are correctly loaded

### Function Execution Fails
- Verify Function IDs are correct in `.env`
- Check Appwrite Function logs in the Console
- Ensure functions are deployed and active

### No Data Returned
- Verify `user_id` exists in your database
- Check Appwrite Console → Databases → Collections for data
- Review function execution logs

## 📊 Next Steps

1. ✅ Deploy Appwrite Functions to Cloud
2. ✅ Configure `.env` with Function IDs
3. ✅ Run StreamLit dashboard
4. 🔄 Add user authentication (optional)
5. 🎨 Customize dashboard UI
6. 📈 Add more features (payments, audit logs, etc.)

## 🆘 Support

- **Appwrite Docs**: https://appwrite.io/docs
- **StreamLit Docs**: https://docs.streamlit.io
- **Project README**: ../appwrite-functions/README.md
