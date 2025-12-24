# Tests and Scripts Directory

This directory contains diagnostic tests and utility scripts for BBBot.

## Test Scripts

### Database Tests
- **test_budget_database.py** - Tests MySQL connection to mydb database (port 3306)
- **test_env_loading.py** - Verifies .env file loads correctly with all variables

### Plaid Integration Tests
- **test_plaid_credentials.py** - Verifies Plaid API credentials load properly
- **create_plaid_table.py** - Creates user_plaid_tokens table if missing

### Comprehensive Tests
- **test_budget_fixes.py** - Complete test suite (env, MySQL, Plaid)
- **full_diagnostic.py** - Full system diagnostic report

## Restart Scripts

### PowerShell Scripts
- **quick_restart.ps1** - Fast restart (no tests)
- **restart_bbbot.ps1** - Comprehensive restart with diagnostics
- **restart_clean.ps1** - Full restart with tests
- **start_after_reboot.ps1** - Fresh start after system reboot

### Batch Scripts
- **restart_clean.bat** - Windows batch version of restart script

## Usage

### Run Tests
```powershell
# Test database connection
python tests_and_scripts/test_budget_database.py

# Test Plaid credentials
python tests_and_scripts/test_plaid_credentials.py

# Full diagnostic
python tests_and_scripts/full_diagnostic.py
```

### Restart Streamlit
```powershell
# Quick restart (recommended)
.\tests_and_scripts\quick_restart.ps1

# Full restart with tests
.\tests_and_scripts\restart_bbbot.ps1
```

## Maintenance

All scripts are maintained and updated as needed. For issues, check:
1. `.env` file configuration
2. MySQL service status (port 3306)
3. Virtual environment activation
