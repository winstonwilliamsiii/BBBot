# Environment Variable Cache-Busting Guide

## Overview

This document explains the cache-busting mechanism implemented in Bentley Budget Bot to ensure environment variables are properly reloaded during runtime, preventing stale cached values from causing issues.

## The Problem

When using `python-dotenv`, environment variables are loaded once at module import time. This creates issues:

1. **Module-level caching**: Once loaded, variables remain cached even if the `.env` file changes
2. **Streamlit hot-reload**: When Streamlit reloads modules, it may use stale cached values
3. **Runtime updates**: Changes to `.env` file don't propagate until full application restart
4. **Testing difficulties**: Hard to test with different environment configurations

## The Solution

We've implemented a **cache-busting reload mechanism** in `config_env.py` that allows environment variables to be refreshed on-demand.

### Core Functions

#### 1. `reload_env(force: bool = False)`

Reloads environment variables from the `.env` file.

```python
from config_env import reload_env

# Use cached values (default, faster)
reload_env(force=False)

# Force reload from .env file (cache-busting)
reload_env(force=True)
```

**Parameters:**
- `force` (bool): If `True`, always reload. If `False`, only reload if not already loaded.

**Returns:**
- `bool`: `True` if `.env` file was found and loaded

**Use Cases:**
- Call with `force=False` at application startup (efficient)
- Call with `force=True` when you know `.env` has changed
- Call with `force=True` in critical functions that need fresh values

#### 2. `require_env_var(var_name: str, reload: bool = False)`

Get environment variable with optional reload and validation.

```python
from config_env import require_env_var

# Get variable (uses cached value)
api_key = require_env_var('TIINGO_API_KEY')

# Get variable with cache-busting reload
api_key_fresh = require_env_var('TIINGO_API_KEY', reload=True)
```

**Parameters:**
- `var_name` (str): Name of environment variable
- `reload` (bool): If `True`, reload `.env` file before getting variable

**Returns:**
- `str`: Value of environment variable

**Raises:**
- `ValueError`: If environment variable is not set or has placeholder value

## Implementation Examples

### Streamlit Application

```python
# streamlit_app.py
from dotenv import load_dotenv

# Initial load at module level
load_dotenv()

# Import reload function
from config_env import reload_env

def main():
    st.set_page_config(...)
    
    # Reload env vars for cache-busting
    reload_env(force=False)  # or force=True if you need fresh values
    
    # Rest of your app...
```

### Page-Level Implementation

```python
# pages/01_💰_Personal_Budget.py
import os
from dotenv import load_dotenv

# Initial load
load_dotenv()

import streamlit as st
from config_env import reload_env

def main():
    st.set_page_config(...)
    
    # Reload environment variables
    reload_env(force=False)
    
    # Your page logic...
```

### Database Connection with Fresh Credentials

```python
# Database connection that always uses fresh credentials
from config_env import reload_env
import os

# Reload env vars to ensure fresh database credentials
reload_env(force=True)

MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3307,
    'user': 'root',
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': 'bentleybot'
}
```

## Best Practices

### When to Use `force=False` (Default)

✅ **Application startup** - First load of environment variables
```python
reload_env(force=False)  # Efficient, uses cache if available
```

✅ **Most function calls** - When you don't expect `.env` to have changed
```python
def my_function():
    reload_env(force=False)
    api_key = os.getenv('API_KEY')
```

### When to Use `force=True` (Cache-Busting)

🔄 **After `.env` file modifications** - When you know the file has changed
```python
# User updated .env file
reload_env(force=True)
```

🔄 **Critical operations** - Database connections, API calls
```python
def connect_to_database():
    reload_env(force=True)  # Ensure fresh credentials
    password = os.getenv('MYSQL_PASSWORD')
```

🔄 **Testing scenarios** - When testing with different configurations
```python
def test_with_different_config():
    # Modify .env
    reload_env(force=True)
    # Test with new values
```

### When to Use `require_env_var(reload=True)`

🔒 **Sensitive operations** - When you need guaranteed fresh values
```python
# Critical API call that needs fresh token
api_token = require_env_var('API_TOKEN', reload=True)
```

🔒 **Long-running processes** - Periodic credential refresh
```python
def periodic_task():
    # Refresh credentials every hour
    db_password = require_env_var('MYSQL_PASSWORD', reload=True)
```

## Testing the Mechanism

Run the test script to verify the reload mechanism:

```bash
python test_env_reload.py
```

The test script validates:
1. ✅ Initial environment load
2. ✅ Reload without force (caching behavior)
3. ✅ Force reload (cache-busting)
4. ✅ `require_env_var()` with reload parameter
5. ✅ Missing variable error handling

## Migration Guide

### Before (Module-Level Loading)

```python
# ❌ OLD WAY - Cached at module import time
import os
from dotenv import load_dotenv

load_dotenv()

# These values are cached and never refresh
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
TIINGO_API_KEY = os.getenv('TIINGO_API_KEY')
```

### After (Function-Level Reloading)

```python
# ✅ NEW WAY - Can be refreshed on demand
import os
from config_env import reload_env

def get_database_connection():
    # Reload for fresh credentials
    reload_env(force=True)
    
    password = os.getenv('MYSQL_PASSWORD')
    # Use password...
```

## Files Modified

1. ✅ `config_env.py` - Added `reload_env()` function
2. ✅ `streamlit_app.py` - Calls `reload_env()` in `main()`
3. ✅ `pages/01_💰_Personal_Budget.py` - Calls `reload_env()` in `main()`
4. ✅ `pages/05_🤖_Trading_Bot.py` - Calls `reload_env()` before database connection
5. ✅ `test_env_reload.py` - Comprehensive test script

## Troubleshooting

### Issue: Environment variables still showing stale values

**Solution:** Use `force=True` to bypass cache:
```python
reload_env(force=True)
```

### Issue: ValueError about missing environment variable

**Solution:** Check your `.env` file and ensure the variable is set:
```python
# Will raise helpful error if not set
api_key = require_env_var('API_KEY', reload=True)
```

### Issue: Streamlit not picking up .env changes

**Solution:** Force reload in your main function:
```python
def main():
    st.set_page_config(...)
    reload_env(force=True)  # Force fresh values
```

## Performance Considerations

- **`force=False`**: Fast, uses cached values
- **`force=True`**: Slightly slower, reads `.env` file from disk
- **Recommendation**: Use `force=False` for most cases, `force=True` only when needed

## Security Notes

- Environment variables containing secrets are still masked in logs
- The reload mechanism doesn't expose sensitive values
- Test script masks passwords and API keys in output
- Same security practices apply as before

## Summary

The cache-busting mechanism provides:

✅ **Flexibility** - Reload environment variables on demand  
✅ **Reliability** - Ensure fresh values for critical operations  
✅ **Testing** - Easy to test with different configurations  
✅ **Performance** - Optional caching for efficiency  
✅ **Safety** - Validation and error handling built-in  

Use `reload_env(force=True)` when you need guaranteed fresh values, otherwise stick with the default `force=False` for optimal performance.
