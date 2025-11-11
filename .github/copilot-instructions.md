# Bentley Budget Bot - AI Coding Instructions

## Project Architecture

**Bentley Bot** is a multi-platform financial portfolio dashboard with these core components:

- **Streamlit App** (`streamlit_app.py`) - Main web interface with Yahoo Finance integration
- **Vercel API** (`api/index.py`) - Serverless endpoints for status/health monitoring  
- **Frontend Modules** (`frontend/`) - Reusable UI components and utilities
- **Deployment** - Dual deployment model (Docker containers + Vercel serverless)

## Key Development Patterns

### Yahoo Finance Integration
The app uses a sophisticated batching system in `get_yfinance_data()` for reliable data fetching:
```python
# Downloads tickers in batches of 8 to avoid API limits
batch_size = 8
if isinstance(tickers, (list, tuple)) and len(tickers) > batch_size:
    for chunk in _chunks(list(tickers), batch_size):
        part = yf.download(chunk, start=start_date, end=end_date)
```

### Portfolio Data Sources
Two primary data input methods:
1. **Yahoo Finance scraping** - Uses `frontend/utils/yahoo.py` with robust HTML/JSON parsing
2. **CSV uploads** - Direct portfolio file uploads with validation in session state

### Error Handling Strategy
- Graceful degradation when `yfinance` is unavailable (check `YFINANCE_AVAILABLE` flag)
- Defensive column handling for MultiIndex DataFrames from Yahoo Finance
- Session state management for uploaded portfolio data persistence

## Development Workflows

### Local Development
```bash
# Standard Streamlit development
streamlit run streamlit_app.py

# Docker development (recommended for production testing)
docker-compose up
```

### Testing Changes
- Use Python CI workflow (`.github/workflows/python-app.yml`) - runs flake8 and pytest
- Test both data source paths: Yahoo Finance scraping AND CSV uploads
- Validate responsive design with different portfolio sizes

### Deployment Paths
1. **Vercel** - Primary deployment using `vercel.json` routing to `api/index.py`
2. **Docker** - Alternative deployment using `docker-compose.yml`

## Project-Specific Conventions

### UI Components
Use the modular approach from `frontend/utils/styling.py`:
```python
create_metric_card("Portfolio Value", "$125,430", "+12%")
create_custom_card("Status", "System operational")
```

### Color Scheme
All colors defined in `frontend/styles/colors.py` - use `COLOR_SCHEME` dict consistently:
```python
from frontend.styles.colors import COLOR_SCHEME
st.markdown(f"<div style='color: {COLOR_SCHEME['primary']}'>", unsafe_allow_html=True)
```

### Data Caching
Critical: Use `@st.cache_data` for expensive operations:
- Yahoo Finance API calls (`get_yfinance_data`)  
- Portfolio scraping (`_cached_fetch`, `_cached_fetch_holdings`)

## External Integration Points

### Yahoo Finance Dependencies
- **Primary**: `yfinance` package for real-time stock data
- **Fallback**: BeautifulSoup parsing in `yahoo.py` for portfolio extraction
- **Rate limiting**: Built-in batching and error handling for API limits

### Google Sheets (Optional)
- `gsheetsconnection.py` shows integration pattern with `streamlit-gsheets`
- Currently not integrated in main app but available for future extension

### Deployment Services
- **Vercel**: Routes all traffic to `api/index.py` via `vercel.json` rewrites
- **Docker**: Multi-stage build with health checks on port 8501

## Critical Files for AI Understanding

- `streamlit_app.py` - Main application logic and data flow
- `frontend/utils/yahoo.py` - Complex scraping logic for portfolio data
- `api/index.py` - Serverless function handling multiple endpoints
- `docker-compose.yml` + `Dockerfile` - Container deployment configuration
- `requirements.txt` - Core dependencies (note: yfinance is optional with fallbacks)

## Common Debugging Areas

1. **Yahoo Finance failures** - Check `YFINANCE_AVAILABLE` flag and error handling
2. **Portfolio scraping issues** - Yahoo changed HTML structure, update parsing in `yahoo.py`  
3. **MultiIndex DataFrame errors** - Yahoo returns different column structures per query size
4. **Session state persistence** - Portfolio CSV data stored in `st.session_state.portfolio_data`
5. **Vercel deployment** - Ensure all imports work in serverless environment (check `api/index.py`)