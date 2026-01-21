"""
Plaid Quickstart Integration Test Page
=======================================
Test your Plaid Docker backend connection before integrating into production.

Features:
- Backend health check
- Link token generation
- Bank connection flow
- Transaction fetching
- Debug information

Run this standalone for testing:
    streamlit run test_plaid_quickstart.py

Or access via BBBot multi-page app:
    http://localhost:8501/
"""

import os
from dotenv import load_dotenv

# Load environment variables with override enabled for cache-busting
load_dotenv(override=True)

import streamlit as st
import sys
from pathlib import Path

# Add frontend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from frontend.components.plaid_quickstart_connector import PlaidQuickstartClient, render_quickstart_plaid_link
from frontend.utils.styling import apply_custom_styling, add_footer
from frontend.styles.colors import COLOR_SCHEME
from frontend.utils.rbac import RBACManager, Permission, show_login_form, show_user_info

# Page config
st.set_page_config(
    page_title="Plaid Quickstart Test | BBBot",
    page_icon="🏦",
    layout="wide"
)

# Apply custom styling
apply_custom_styling()
RBACManager.init_session_state()
show_user_info()
if not RBACManager.is_authenticated() or not RBACManager.has_permission(Permission.VIEW_TRADING_BOT):
    st.error("🚫 ADMIN access required")
    show_login_form()
    st.stop()

st.title("🏦 Plaid Quickstart Integration Test")

st.markdown("""
This page tests your connection to the **Plaid quickstart Docker backend**.

### Prerequisites:
1. ✅ Plaid quickstart repo cloned
2. ✅ Docker container running
3. ✅ Backend accessible at `http://localhost:XXXX`
""")

# Configuration
st.markdown("---")
st.markdown("## ⚙️ Configuration")

col1, col2 = st.columns(2)

with col1:
    # Check if running on Streamlit Cloud vs local
    # Check multiple indicators for cloud deployment
    is_cloud = (
        os.getenv('STREAMLIT_SHARING_MODE') is not None or 
        os.getenv('STREAMLIT_RUNTIME_ENV') == 'cloud' or
        'streamlit.app' in str(st.get_option('browser.serverAddress')) or
        'streamlit.app' in str(os.getenv('STREAMLIT_SERVER_HEADLESS', ''))
    )
    
    # Force Appwrite endpoint for production, localhost for local dev
    default_url = "https://fra.cloud.appwrite.io/v1/functions/plaid_quickstart/executions" if is_cloud else "http://localhost:5001"
    
    backend_url = st.text_input(
        "Backend URL",
        value=default_url,
        help="🌐 Production: Appwrite Function | 💻 Local: Docker on port 5001"
    )
    
    # Show cloud status for debugging
    if is_cloud:
        st.info(f"🌐 Running on Streamlit Cloud - Using Appwrite Function")
    else:
        st.info(f"💻 Running locally - Using Docker backend")
    
    if 'localhost' in backend_url and is_cloud:
        st.error("⚠️ Cannot use localhost on Streamlit Cloud! Use the Appwrite Function URL.")

with col2:
    user_id = st.text_input(
        "Test User ID",
        value="winston_test_123",
        help="Any unique identifier for testing"
    )

# Test connection
st.markdown("---")
st.markdown("## 🔍 Backend Health Check")

client = PlaidQuickstartClient(backend_url)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔌 Test Connection", use_container_width=True):
        with st.spinner("Checking backend..."):
            if client.health_check():
                st.success("✅ Backend is running!")
            else:
                st.error("❌ Backend not responding")
                st.info(f"""
**Troubleshooting:**
1. Check Docker: `docker ps`
2. Check logs: `docker-compose logs`
3. Try different port: {backend_url.replace('8000', '8080')}
""")

with col2:
    st.metric("Backend", backend_url.split('//')[1])

with col3:
    st.metric("User ID", user_id[:15] + "..." if len(user_id) > 15 else user_id)

# Main integration test
st.markdown("---")
st.markdown("## 🧪 Integration Test")

render_quickstart_plaid_link(user_id, backend_url)

# Instructions
st.markdown("---")
st.markdown("## 📖 How to Use")

tab1, tab2, tab3 = st.tabs(["Quick Start", "Docker Setup", "Troubleshooting"])

with tab1:
    st.markdown("""
### Quick Start Guide

1. **Start the backend:**
   ```bash
   cd plaid-quickstart
   docker-compose up
   ```

2. **Click "Open Plaid Link"** above

3. **Select bank:** Chase or Bank of America

4. **Login with:**
   - Username: `user_good`
   - Password: `pass_good`

5. **Success!** Backend will exchange token automatically

6. **Fetch transactions** using date range
""")

with tab2:
    st.markdown("""
### Docker Backend Setup

#### If you have the Plaid quickstart:
```bash
# Clone if you haven't
git clone https://github.com/plaid/quickstart.git plaid-quickstart
cd plaid-quickstart

# Configure environment
cp .env.example .env

# Edit .env with your credentials:
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ENV=sandbox

# Start Docker container
docker-compose up
```

#### Check if running:
```bash
# See Docker containers
docker ps

# Check logs
docker-compose logs -f

# Test endpoint
curl http://localhost:8000/
```

#### Common Ports:
- Python backend: `8000`
- Node.js backend: `8080`
- React frontend: `3000`
""")

with tab3:
    st.markdown("""
### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Backend Offline" | Run `docker ps` to check container status |
| "Connection refused" | Try port 8080 or 3000 instead of 8000 |
| "Invalid credentials" | Update .env in plaid-quickstart folder |
| "CORS error" | Backend needs CORS enabled for Streamlit |
| Link button doesn't work | Check browser console (F12) for errors |

#### Enable CORS (if needed):
If the backend blocks Streamlit, add to the backend code:

**Python (Flask/FastAPI):**
```python
from flask_cors import CORS
CORS(app, origins=["http://localhost:8501"])
```

**Node.js (Express):**
```javascript
app.use(cors({ origin: 'http://localhost:8501' }));
```

#### Get Detailed Logs:
```bash
# Backend logs
docker-compose logs backend -f

# All logs
docker-compose logs -f
```

#### Restart Backend:
```bash
docker-compose down
docker-compose up --build
```
""")

# Debug info
with st.expander("🐛 Debug Information"):
    st.json({
        "backend_url": backend_url,
        "user_id": user_id,
        "streamlit_url": "http://localhost:8501",
        "session_state": dict(st.session_state)
    })

# Footer
st.markdown("---")
st.caption("💡 Once this works, we'll migrate the logic to your Appwrite Functions!")

# Add BBBot footer
add_footer()
