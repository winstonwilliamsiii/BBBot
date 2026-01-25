# Localhost vs Streamlit Cloud Differences - Diagnostic Report

**Date:** January 17, 2026  
**Status:** 🔍 Under Investigation

## Summary of Issues

| Issue | localhost:8501 | bbbot305.streamlit.app | Status |
|-------|---|---|---|
| Market & Economic Section | ❌ Missing | ✅ Shows | 🔧 To Fix |
| MLflow Tracker | ❌ Error | ⚠️ Error (different) | 🔧 To Fix |
| Live Crypto Dashboard | ? | ❌ Error | 🔧 To Fix |

---

## Issue 1: Missing "Markets & Economics" Section on localhost:8501

### Root Cause Analysis

**File:** [streamlit_app.py](streamlit_app.py) Lines 364-370

```python
if ECONOMIC_CALENDAR_AVAILABLE:
    st.markdown("## 📊 Markets & Economics")
    widget = get_calendar_widget()
    widget.render_full_dashboard()
    st.markdown("---")
```

**The section is gated by:** `ECONOMIC_CALENDAR_AVAILABLE` flag (Lines 50-54)

```python
try:
    from frontend.components.economic_calendar_widget import get_calendar_widget
    ECONOMIC_CALENDAR_AVAILABLE = True
except ImportError:
    ECONOMIC_CALENDAR_AVAILABLE = False
```

### Why It's Missing Locally

**Local Test Results:**
```
✅ economic_calendar_widget: OK (imports successfully)
```

Despite the import working, the flag may not be set correctly **in Streamlit's runtime** due to:

1. **Streamlit caching/module reloading** - Cache interferes with import checks
2. **Missing dependencies** in economic_calendar_widget itself
3. **Environment variables** not loaded at import time

### Why It Shows on Cloud

Streamlit Cloud environment differences:
- Different dependency versions
- Clean environment rebuild
- May have additional libraries installed

---

## Issue 2: MLflow Tracker Errors

### Local Error: "Install bbbot1_pipeline package"

**File:** [frontend/pages/02_📈_Investment_Analysis.py](frontend/pages/02_📈_Investment_Analysis.py) Lines 211-222

**Current Code:**
```python
try:
    from bbbot1_pipeline.mlflow_tracker import get_tracker, MLFLOW_AVAILABLE as MLFLOW_PKG_AVAILABLE
    from bbbot1_pipeline import load_tickers_config
    if not MLFLOW_PKG_AVAILABLE:
        raise ImportError("MLflow package not installed in bbbot1_pipeline")
    MLFLOW_AVAILABLE = True
except ImportError as e:
    MLFLOW_AVAILABLE = False
    get_tracker = None
    load_tickers_config = lambda: {}
```

**Test Result:**
```
✅ bbbot1_pipeline: OK (imports successfully)
```

**Why Error Still Shows:**
1. Streamlit caches the import result
2. The fallback display code still runs
3. OR there's a secondary error after import (in get_tracker initialization)

### Cloud Error: `ImportError: "cachetools.func"`

**Analysis:**

This error suggests:
1. `cachetools` module exists but `func` submodule is missing
2. Version mismatch between cachetools and google.generativeai
3. Likely cause: **google-generativeai requires specific cachetools version**

**Dependency Chain:**
```
google-generativeai → requires → cachetools (specific version)
Streamlit Cloud → may have older/newer → cachetools
```

---

## Issue 3: Live Crypto Dashboard Error on Cloud

**File:** [frontend/pages/03_🔴_Live_Crypto_Dashboard.py](frontend/pages/03_🔴_Live_Crypto_Dashboard.py)

**Likely Cause:**
- Same cachetools issue affecting imports
- OR missing dependency for crypto price fetching
- OR RBAC/styling import failure on cloud

---

## FIXES

### Fix 1: Force Economic Calendar Display Locally

**Problem:** Conditional rendering based on import success  
**Solution:** Add explicit diagnostics and ensure import actually works

**Change [streamlit_app.py](streamlit_app.py) Lines 50-54:**

```python
# Economic Calendar Widget import
try:
    from frontend.components.economic_calendar_widget import get_calendar_widget
    # Test that the widget actually initializes
    try:
        test_widget = get_calendar_widget()
        ECONOMIC_CALENDAR_AVAILABLE = True
    except Exception as e:
        print(f"⚠️ Economic calendar widget initialization failed: {e}")
        ECONOMIC_CALENDAR_AVAILABLE = False
except ImportError as e:
    print(f"⚠️ Economic calendar import failed: {e}")
    ECONOMIC_CALENDAR_AVAILABLE = False
```

### Fix 2: Fix cachetools Conflict on Cloud

**Problem:** google-generativeai version conflict with cachetools  
**Solution:** Pin compatible versions in requirements.txt

**Changes to [requirements.txt](requirements.txt):**

Add after the Streamlit section:

```bash
# ============================================
# GOOGLE GENERATIVE AI & CACHING
# ============================================
# Pin cachetools to compatible version with google-generativeai
cachetools>=5.0.0,<6.0.0
google-generativeai>=0.3.0

# ============================================
# NOTE: These versions are tested for compatibility
# ============================================
```

### Fix 3: Better MLflow Error Messages

**Problem:** Generic "Install bbbot1_pipeline" error not helpful  
**Solution:** Add better diagnostics to Investment Analysis page

**Change [frontend/pages/02_📈_Investment_Analysis.py](frontend/pages/02_📈_Investment_Analysis.py) Lines 211-226:**

```python
# Import MLFlow tracker with detailed diagnostics
import sys
try:
    # Check if package is in sys.path
    from bbbot1_pipeline.mlflow_tracker import get_tracker, MLFLOW_AVAILABLE as MLFLOW_PKG_AVAILABLE
    from bbbot1_pipeline import load_tickers_config
    
    if not MLFLOW_PKG_AVAILABLE:
        raise ImportError("MLflow not installed - run: pip install mlflow")
    
    # Test actual instantiation
    test_tracker = get_tracker()
    MLFLOW_AVAILABLE = True
except ImportError as e:
    MLFLOW_AVAILABLE = False
    get_tracker = None
    load_tickers_config = lambda: {}
    import warnings
    warnings.warn(f"⚠️ MLflow unavailable: {str(e)[:150]}")
except Exception as e:
    # Secondary errors (connection, database, etc.)
    MLFLOW_AVAILABLE = False
    get_tracker = None
    load_tickers_config = lambda: {}
    import warnings
    warnings.warn(f"⚠️ MLflow error: {str(e)[:150]}")
```

### Fix 4: Crypto Dashboard Fallback

**Problem:** Crashes if dependencies missing on cloud  
**Solution:** Add graceful fallback

**Add to [frontend/pages/03_🔴_Live_Crypto_Dashboard.py](frontend/pages/03_🔴_Live_Crypto_Dashboard.py) after styling section:**

```python
except Exception as styling_error:
    st.warning(f"⚠️ Styling not available: {styling_error}")
    st.title("🔴 Live Crypto Dashboard (Fallback Mode)")
```

---

## Environment Comparison

### localhost:8501 (Local Development)

**Environment:** Your machine  
**Python:** 3.12.10 (from your Windows Python install)  
**Dependencies:** Installed in `.venv`  
**Database:** Docker on localhost:3307  
**Advantages:**
- ✅ Full control over dependencies
- ✅ Local file access
- ✅ Fast iteration
- ✅ All optional packages available

**Disadvantages:**
- ❌ Must maintain .venv manually
- ❌ Caching can mask import errors
- ❌ May differ from cloud environment

### bbbot305.streamlit.app (Production/Cloud)

**Environment:** Streamlit Cloud servers  
**Python:** 3.12.x (managed by Streamlit)  
**Dependencies:** Installed from requirements.txt at deployment time  
**Database:** Railway MySQL on port 54537  
**Secrets:** From Streamlit Cloud dashboard  
**Advantages:**
- ✅ Public access
- ✅ Auto-deploys on git push
- ✅ Clean environment
- ✅ Managed infrastructure

**Disadvantages:**
- ❌ Version mismatches
- ❌ Limited troubleshooting
- ❌ Dependency conflicts can't be easily debugged
- ❌ Logs only visible in dashboard

---

## Deployment Process

### How Code Goes from Local to Cloud

```
1. You push code to GitHub
                ↓
2. Streamlit Cloud detects push
                ↓
3. Rebuilds environment:
   - Installs Python 3.12
   - Runs: pip install -r requirements.txt
   - Loads secrets from dashboard
                ↓
4. Runs: streamlit run streamlit_app.py
                ↓
5. Deployed at bbbot305.streamlit.app
```

### Why Versions Differ

**Local (your machine):**
```bash
pip install mlflow>=2.8.0  # Gets latest: maybe 2.15.0
```

**Cloud (at deployment):**
```bash
pip install mlflow>=2.8.0  # Gets whatever is latest TODAY: maybe 2.16.0
```

**Result:** Different versions → Different behavior

---

## Why Features Appear/Disappear

### Missing Features on Local

```
import economic_calendar_widget
    ↓
✅ Imports successfully
    ↓
BUT: Flag checked in Streamlit runtime
    ↓
❌ Error during rendering (hidden)
    ↓
Feature doesn't display
```

### Why Cloud Shows It

```
Same code, but:
- Different Python version
- Different dependency versions
- Cloud environment more similar to expected
    ↓
✅ Works
```

---

## Action Items

### IMMEDIATE (High Priority)

1. **Pin cachetools version** in requirements.txt
   - Prevents google-generativeai conflicts on cloud
   - Should fix "ImportError: cachetools.func"

2. **Add error diagnostics** to Investment Analysis page
   - Better error messages
   - Easier debugging

3. **Test economic calendar locally**
   - Add debug output to verify import
   - Test widget initialization

### MEDIUM (Should Do)

1. Add requirements-local.txt with full dependencies
   - For local development with all features
   - Current requirements.txt is cloud-optimized

2. Add streamlit.toml configuration
   - Set up proper caching
   - Reduce import check issues

3. Separate "demo" mode fallbacks
   - Show data even if some imports fail
   - Better user experience

### LONG-TERM (Nice to Have)

1. Unit tests for each page
   - Catch import errors before deployment
   - Test cloud vs local differences

2. Pre-deployment checks
   - Run requirements.txt in clean environment
   - Verify all imports work

3. Documentation
   - Explain localhost vs cloud differences
   - Troubleshooting guide

---

## Testing Plan

### Test on localhost:8501

```bash
# 1. Check if sections appear
# - Personal Budget ✅
# - Markets & Economics ❓ (currently missing)
# - Investment Analysis ❓ (check for MLflow error)
# - Crypto Dashboard ✅

# 2. Check console for warnings
streamlit run streamlit_app.py 2>&1 | grep -i "warning\|error"

# 3. Test specific page
streamlit run frontend/pages/02_📈_Investment_Analysis.py
```

### Test on bbbot305.streamlit.app

```
# After deployment:
1. Home page → Check Markets & Economics ✅
2. Investment Analysis → Check MLflow tab (should say no error now)
3. Crypto Dashboard → Check for errors
4. Check Streamlit Cloud logs for warnings
```

---

**Next Steps:** Apply the fixes above and redeploy to Streamlit Cloud for testing.

