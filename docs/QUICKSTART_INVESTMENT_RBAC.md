# Quick Start: Investment Analysis RBAC System

## 🚀 Get Started in 5 Minutes

### Step 1: Setup Database (Optional)

If you want to use database-backed fund storage:

```bash
# Run the SQL setup script
mysql -u your_user -p bentley_budget < mysql_setup.sql/investment_analysis_schema.sql
```

Or let the script create the table automatically:

```bash
python "#Fetch and Display Webull Funds.py" --setup-db --demo
```

### Step 2: Install Dependencies

All dependencies are already in `requirements.txt`. Ensure you have:
- streamlit
- pandas
- plotly
- requests (for Webull API)
- mysql-connector-python (optional, for database)

### Step 3: Launch the App

```bash
streamlit run streamlit_app.py
```

Or directly open the Investment Analysis page:

```bash
streamlit run "pages/01_📈_Investment_Analysis.py"
```

### Step 4: Login

Navigate to the **Investment Analysis** page and use demo credentials:

**For Full Access (Broker Connections):**
```
Username: client
Password: client123
```

**Or:**
```
Username: investor
Password: investor123
```

### Step 5: Access Broker Connections

Once logged in, you'll see the **🔗 Broker Connections** tab. Click it to view:

1. **🏦 Accounts** - Connected broker accounts
2. **💼 WeFolio Funds** - Webull fund positions
3. **📊 Positions** - Cross-broker analysis
4. **🔍 Health Monitor** - Connection status

## 📊 Using Demo Data

The system includes demo data by default:

- **5 broker connections** (WeBull, IBKR, Binance, NinjaTrader, Meta5)
- **4 WeFolio funds** with realistic values
- **Performance metrics** and charts

## 🔌 Using Real Webull API

### In the UI:

1. Go to **Broker Connections** → **💼 WeFolio Funds**
2. Check "Use Real Webull API"
3. Enter your Webull API token
4. Click "Fetch Funds"

### Via Command Line:

```bash
# Fetch and save to database
python "#Fetch and Display Webull Funds.py" --token YOUR_WEBULL_TOKEN

# Or use environment variable
export WEBULL_API_TOKEN=your_token_here
python "#Fetch and Display Webull Funds.py"

# Use demo data
python "#Fetch and Display Webull Funds.py" --demo
```

## 🎭 User Roles & Permissions

| Role     | Portfolio | Analysis | Connections | Funds | Trading |
|----------|-----------|----------|-------------|-------|---------|
| Guest    | ✅        | ❌       | ❌          | ❌    | ❌      |
| Client   | ✅        | ✅       | ✅*         | ✅*   | ❌      |
| Investor | ✅        | ✅       | ✅*         | ✅*   | ✅      |
| Admin    | ✅        | ✅       | ✅*         | ✅*   | ✅      |

*Requires KYC + Investment Agreement

## 📋 Compliance Requirements

To access **Broker Connections**, users need:

1. ✅ **KYC Completed** - Know Your Customer verification
2. ✅ **Investment Agreement Signed** - Asset management contract

Demo users `client`, `investor`, and `admin` have these completed.

## 🔒 Security Notes

### Current Setup (Development)
- Demo users with hardcoded credentials
- SHA-256 password hashing
- Session-based authentication
- No database required for auth

### For Production
- Use database for user storage
- Implement bcrypt/argon2 hashing
- Add rate limiting
- Enable audit logging
- Use environment variables for secrets

## 🛠️ Customization

### Adding New Users (Code)

Edit `frontend/utils/rbac.py`:

```python
DEMO_USERS = {
    'newuser': {
        'password_hash': hashlib.sha256('password123'.encode()).hexdigest(),
        'role': UserRole.CLIENT,
        'kyc_completed': True,
        'investment_agreement_signed': True,
        'email': 'newuser@example.com',
    },
}
```

### Adding New Broker

Edit `frontend/utils/broker_connections.py`:

```python
def get_demo_connections():
    return [
        # ... existing connections (WeBull, IBKR, Binance, NinjaTrader, Meta5)
        BrokerConnection(
            broker_name="New Broker",
            account_number="****1234",
            status="Connected",
            last_sync=datetime.now(),
            balance=50000.00,
            positions_count=5,
        ),
    ]
```

## 📁 File Structure

```
BentleyBudgetBot/
├── pages/
│   └── 01_📈_Investment_Analysis.py   # Main page with RBAC
├── frontend/
│   └── utils/
│       ├── rbac.py                     # Authentication system
│       └── broker_connections.py       # Connection displays
├── docs/
│   └── INVESTMENT_ANALYSIS_RBAC.md     # Full documentation
├── mysql_setup.sql/
│   └── investment_analysis_schema.sql  # Database schema
└── #Fetch and Display Webull Funds.py  # CLI tool
```

## 🧪 Testing Different Roles

### Test Guest Access (Limited)
```
Username: guest
Password: guest123
Expected: Only Portfolio Overview visible
```

### Test Client Access (Full)
```
Username: client
Password: client123
Expected: All tabs including Broker Connections
```

### Test Non-Compliant User
1. Edit `DEMO_USERS` in `rbac.py`
2. Set `kyc_completed: False` for a user
3. Login - connections tab will show requirements

## 🔧 Troubleshooting

### "RBAC system not available"
- Check `frontend/utils/rbac.py` exists
- Verify Python path includes project root
- Restart Streamlit server

### Connections Tab Not Showing
- Verify you're logged in as client/investor/admin
- Check KYC and agreement status
- Clear browser cache

### Database Connection Errors
- Check MySQL is running
- Verify credentials in `.env` or `st.secrets`
- Test connection: `mysql -u user -p`

### Import Errors
```bash
# Ensure working directory is project root
cd /path/to/BentleyBudgetBot

# Run from project root
streamlit run streamlit_app.py
```

## 🎯 Next Steps

1. ✅ **Test the demo** - Login and explore features
2. 🔧 **Configure database** - Setup MySQL for persistence
3. 🔑 **Add real API tokens** - Connect to actual Webull API
4. 👥 **Create real users** - Replace demo users with database
5. 🔒 **Enhance security** - Implement production-grade auth
6. 📊 **Add more brokers** - Extend to TD Ameritrade, E*TRADE, etc.

## 📚 Additional Resources

- **Full Documentation**: `docs/INVESTMENT_ANALYSIS_RBAC.md`
- **Database Schema**: `mysql_setup.sql/investment_analysis_schema.sql`
- **Webull Integration**: `#Fetch and Display Webull Funds.py`
- **Project README**: `README.md`

## 💬 Support

Questions or issues?
- GitHub: https://github.com/winstonwilliamsiii/BBBot
- Email: support@bentleybot.com

---

**Happy Investing! 📈💼**
