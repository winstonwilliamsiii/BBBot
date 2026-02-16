# 🔄 Flask + Streamlit Architecture Update

**Date:** February 15, 2026  
**Status:** ✅ Updated for Flask + Streamlit stack

---

## What Changed

### Before (Original Plan)
- **Backend:** FastAPI (async, complex, needs `uvicorn`)
- **Admin UI:** HTML + JavaScript (separate from main app)

### After (Updated Plan)
- **Backend:** Flask (simpler, synchronous, familiar)
- **Admin UI:** Streamlit pages (integrated with existing app)

---

## Why Flask + Streamlit?

### Benefits of Flask
✅ **Simpler than FastAPI** - Standard Python web framework  
✅ **No async complexity** - Synchronous code is easier  
✅ **Lightweight** - Minimal dependencies  
✅ **Easy to learn** - Similar to existing patterns  
✅ **Flask Blueprints** - Clean module organization  

### Benefits of Streamlit Admin UI
✅ **Already using Streamlit** - No new frontend framework  
✅ **Multipage app** - Just add new page for admin  
✅ **Rapid development** - Build UI in pure Python  
✅ **Built-in widgets** - Buttons, tables, metrics, charts  
✅ **Session state** - Easy authentication  

---

## New Architecture

```
┌─────────────────────────────────────────┐
│     STREAMLIT MULTIPAGE APP             │
│     (localhost:8501)                    │
├─────────────────────────────────────────┤
│  Client Pages:                          │
│  - Home Dashboard                       │
│  - Portfolio                            │
│  - Budget Management                    │
│  - Investment Analysis                  │
│  - Crypto Dashboard                     │
│                                         │
│  Admin Page: (NEW)                      │
│  - pages/99_🔧_Admin_Control_Center.py │
│    └─> Tabs: Overview, Bots, Brokers,  │
│        Risk, Logs                       │
└────────────┬────────────────────────────┘
             │
             │ HTTP Requests (via requests library)
             ▼
┌─────────────────────────────────────────┐
│       FLASK REST API                    │
│       (localhost:5000)                  │
├─────────────────────────────────────────┤
│  Flask Blueprints:                      │
│  - /admin/bots       (bots_bp)         │
│  - /admin/brokers    (brokers_bp)      │
│  - /admin/risk       (risk_bp)         │
│  - /admin/monitoring (monitoring_bp)   │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│   EXISTING INFRASTRUCTURE               │
│   - MySQL (Railway)                     │
│   - Appwrite                            │
│   - Docker Services (Airflow, MLflow)  │
│   - Broker APIs (Alpaca, MT5, Binance) │
└─────────────────────────────────────────┘
```

---

## Quick Start (Updated)

### Step 1: Install Flask Dependencies
```bash
pip install Flask==3.0.0 flask-cors==4.0.0
```

### Step 2: Start Flask API
```bash
python backend/api/app.py
```

API will run on **http://localhost:5000**

### Step 3: Start Streamlit App
```bash
streamlit run streamlit_app.py
```

App will run on **http://localhost:8501**

### Step 4: Access Admin Dashboard
- Open Streamlit in browser
- Navigate to **"🔧 Admin Control Center"** page (in sidebar)
- Enter admin password (stored in `.streamlit/secrets.toml`)

---

## Implementation Changes

### Week 1-2 Tasks (Updated)

**Day 1-2: Flask Blueprints**
```bash
mkdir -p backend/api/admin
touch backend/api/admin/__init__.py
touch backend/api/admin/bots.py       # Flask Blueprint
touch backend/api/admin/brokers.py    # Flask Blueprint
touch backend/api/admin/risk.py       # Flask Blueprint
touch backend/api/admin/monitoring.py # Flask Blueprint
```

**Day 3-4: Streamlit Admin Page**
```bash
touch pages/99_🔧_Admin_Control_Center.py
```

**Day 5: Test Integration**
- Start Flask API
- Start Streamlit
- Navigate to admin page
- Test API calls from Streamlit

---

## Code Template Comparison

### FastAPI (Before) ❌
```python
from fastapi import APIRouter

router = APIRouter(prefix="/admin/bots")

@router.get("/list")
async def list_bots():
    return {"bots": []}
```

### Flask (After) ✅
```python
from flask import Blueprint, jsonify

bots_bp = Blueprint('bots', __name__, url_prefix='/admin/bots')

@bots_bp.route('/list', methods=['GET'])
def list_bots():
    return jsonify({"bots": []})
```

**Key Differences:**
- `APIRouter` → `Blueprint`
- `@router.get()` → `@bp.route(methods=['GET'])`
- `async def` → `def` (no async)
- `return {}` → `return jsonify({})`

---

## File Structure (Updated)

### Before
```
backend/api/
├── Main.py (FastAPI app)
└── admin/
    ├── bots.py (APIRouter)
    └── brokers.py (APIRouter)

admin_ui/
├── dashboard.html
└── bots.html
```

### After
```
backend/api/
├── app.py (Flask app) ✅
└── admin/
    ├── bots.py (Flask Blueprint) ✅
    └── brokers.py (Flask Blueprint) ✅

pages/
└── 99_🔧_Admin_Control_Center.py (Streamlit admin page) ✅
```

---

## Testing Commands (Updated)

### Test Flask API
```bash
# Health check
curl http://localhost:5000/health

# Test endpoint
curl http://localhost:5000/admin/test

# Check broker health (after implementing blueprint)
curl http://localhost:5000/admin/brokers/health

# List bots (after implementing blueprint)
curl http://localhost:5000/admin/bots/list
```

### Test Streamlit Admin
```bash
# Start Streamlit
streamlit run streamlit_app.py

# Open browser
# Navigate to: Pages → 🔧 Admin Control Center
```

---

## Authentication (Simplified)

### Flask (No changes needed)
Flask endpoints are open by default. Add auth middleware later if needed.

### Streamlit Admin Page
```python
# In pages/99_🔧_Admin_Control_Center.py

if 'admin_authenticated' not in st.session_state:
    password = st.text_input("Admin Password", type="password")
    if st.button("Login"):
        if password == st.secrets["ADMIN_PASSWORD"]:
            st.session_state.admin_authenticated = True
            st.rerun()
    st.stop()

# Rest of admin dashboard...
```

**Add to `.streamlit/secrets.toml`:**
```toml
ADMIN_PASSWORD = "your_secure_password_here"
```

---

## Advantages of This Approach

1. **Single Tech Stack** - Python everywhere (Flask + Streamlit)
2. **No Frontend Complexity** - No JavaScript/React needed
3. **Familiar Tools** - Flask is standard Python web framework
4. **Integrated UI** - Admin is just another Streamlit page
5. **Faster Development** - Build UI with Python, not HTML/JS
6. **Easy Testing** - Test API with curl, test UI in browser

---

## What Stays the Same

✅ **All functionality** - Same features, different implementation  
✅ **Database schema** - MySQL tables unchanged  
✅ **Broker integration** - broker_interface.py unchanged  
✅ **Docker services** - Airflow, MLflow, etc. unchanged  
✅ **Roadmap phases** - Same timeline and milestones  

---

## Next Steps

1. ✅ Install Flask: `pip install Flask flask-cors`
2. ✅ Created: `backend/api/app.py` (Flask starter)
3. 📋 Follow: [CONTROL_CENTER_QUICK_START.md](./CONTROL_CENTER_QUICK_START.md) (now updated for Flask)
4. 📋 Create: Flask Blueprints in `backend/api/admin/`
5. 📋 Create: Streamlit admin page in `pages/`

---

## Documentation Updated

All docs now reflect Flask + Streamlit:
- ✅ [CONTROL_CENTER_QUICK_START.md](./CONTROL_CENTER_QUICK_START.md)
- ✅ [BENTLEY_BOT_CONTROL_CENTER_ARCHITECTURE.md](./BENTLEY_BOT_CONTROL_CENTER_ARCHITECTURE.md)
- ✅ [BENTLEY_BOT_PLATFORM_OVERVIEW.md](../BENTLEY_BOT_PLATFORM_OVERVIEW.md)
- ✅ [ARCHITECTURE_COMPLETE.md](./ARCHITECTURE_COMPLETE.md)

---

**Ready to start building?** Flask API starter is at `backend/api/app.py` - test it now!

```bash
python backend/api/app.py
# Then visit: http://localhost:5000
```
