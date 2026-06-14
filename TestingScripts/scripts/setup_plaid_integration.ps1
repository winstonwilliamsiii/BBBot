# Plaid Budget Integration Setup Script
# ======================================
# Run this script to set up the Plaid integration for personal budget analysis

Write-Host "=================================" -ForegroundColor Cyan
Write-Host "Plaid Budget Integration Setup" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Virtual environment not detected. Activating..." -ForegroundColor Yellow
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & .\.venv\Scripts\Activate.ps1
        Write-Host "✅ Virtual environment activated" -ForegroundColor Green
    } else {
        Write-Host "❌ Virtual environment not found at .venv\" -ForegroundColor Red
        Write-Host "   Run: python -m venv .venv" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Step 1: Installing Python Dependencies" -ForegroundColor Cyan
Write-Host "---------------------------------------" -ForegroundColor Cyan

# Check if plaid-python is installed
$plaidInstalled = pip list | Select-String "plaid-python"
if (-not $plaidInstalled) {
    Write-Host "📦 Installing plaid-python..." -ForegroundColor Yellow
    pip install plaid-python
} else {
    Write-Host "✅ plaid-python already installed" -ForegroundColor Green
}

# Check if cryptography is installed
$cryptoInstalled = pip list | Select-String "cryptography"
if (-not $cryptoInstalled) {
    Write-Host "📦 Installing cryptography..." -ForegroundColor Yellow
    pip install cryptography
} else {
    Write-Host "✅ cryptography already installed" -ForegroundColor Green
}

# Check if python-dateutil is installed
$dateutilInstalled = pip list | Select-String "python-dateutil"
if (-not $dateutilInstalled) {
    Write-Host "📦 Installing python-dateutil..." -ForegroundColor Yellow
    pip install python-dateutil
} else {
    Write-Host "✅ python-dateutil already installed" -ForegroundColor Green
}

# Check if plotly is installed
$plotlyInstalled = pip list | Select-String "plotly"
if (-not $plotlyInstalled) {
    Write-Host "📦 Installing plotly..." -ForegroundColor Yellow
    pip install plotly
} else {
    Write-Host "✅ plotly already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 2: Database Setup" -ForegroundColor Cyan
Write-Host "----------------------" -ForegroundColor Cyan

$mysqlHost = "127.0.0.1"
$mysqlPort = "3306"
$mysqlUser = "root"
$mysqlDb = "mydb"

Write-Host "📊 Database Configuration:" -ForegroundColor Yellow
Write-Host "   Host: $mysqlHost" -ForegroundColor Gray
Write-Host "   Port: $mysqlPort" -ForegroundColor Gray
Write-Host "   User: $mysqlUser" -ForegroundColor Gray
Write-Host "   Database: $mysqlDb" -ForegroundColor Gray
Write-Host ""

$runDbSetup = Read-Host "Do you want to run the database schema setup? (y/n)"

if ($runDbSetup -eq "y" -or $runDbSetup -eq "Y") {
    $mysqlPassword = Read-Host "Enter MySQL root password" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($mysqlPassword)
    $plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    
    Write-Host "🔄 Running database schema setup..." -ForegroundColor Yellow
    
    # Run the SQL script
    $sqlScript = "scripts\setup\budget_schema.sql"
    
    if (Test-Path $sqlScript) {
        # Use mysql command to execute the script
        $mysqlCmd = "mysql -h $mysqlHost -P $mysqlPort -u $mysqlUser -p$plainPassword $mysqlDb"
        Get-Content $sqlScript | & mysql -h $mysqlHost -P $mysqlPort -u $mysqlUser -p$plainPassword $mysqlDb
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Database schema created successfully!" -ForegroundColor Green
        } else {
            Write-Host "❌ Error creating database schema" -ForegroundColor Red
            Write-Host "   Run manually: mysql -u root -p mydb < $sqlScript" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ SQL script not found at: $sqlScript" -ForegroundColor Red
    }
    
    # Clear password from memory
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
} else {
    Write-Host "⏭️  Skipping database setup" -ForegroundColor Yellow
    Write-Host "   Run manually: mysql -u root -p mydb < scripts\setup\budget_schema.sql" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Step 3: Environment Configuration" -ForegroundColor Cyan
Write-Host "---------------------------------" -ForegroundColor Cyan

# Check if .env exists
if (Test-Path ".env") {
    Write-Host "✅ .env file exists" -ForegroundColor Green
    
    # Check for required Plaid variables
    $envContent = Get-Content ".env" -Raw
    
    $requiredVars = @(
        "PLAID_CLIENT_ID",
        "PLAID_SECRET",
        "PLAID_ENV",
        "MYSQL_HOST",
        "MYSQL_PORT",
        "MYSQL_USER",
        "MYSQL_PASSWORD",
        "MYSQL_DATABASE"
    )
    
    $missingVars = @()
    foreach ($var in $requiredVars) {
        if ($envContent -notmatch "$var=") {
            $missingVars += $var
        }
    }
    
    if ($missingVars.Count -gt 0) {
        Write-Host "⚠️  Missing environment variables:" -ForegroundColor Yellow
        foreach ($var in $missingVars) {
            Write-Host "   - $var" -ForegroundColor Red
        }
        Write-Host ""
        Write-Host "💡 Add these to your .env file:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "# Plaid Configuration" -ForegroundColor Gray
        Write-Host "PLAID_CLIENT_ID=your_client_id_here" -ForegroundColor Gray
        Write-Host "PLAID_SECRET=your_sandbox_secret_here" -ForegroundColor Gray
        Write-Host "PLAID_ENV=sandbox" -ForegroundColor Gray
        Write-Host "" -ForegroundColor Gray
        Write-Host "# MySQL Configuration" -ForegroundColor Gray
        Write-Host "MYSQL_HOST=127.0.0.1" -ForegroundColor Gray
        Write-Host "MYSQL_PORT=3306" -ForegroundColor Gray
        Write-Host "MYSQL_USER=root" -ForegroundColor Gray
        Write-Host "MYSQL_PASSWORD=your_password" -ForegroundColor Gray
        Write-Host "MYSQL_DATABASE=mydb" -ForegroundColor Gray
    } else {
        Write-Host "✅ All required environment variables present" -ForegroundColor Green
    }
} else {
    Write-Host "❌ .env file not found" -ForegroundColor Red
    Write-Host "   Copy .env.example to .env and configure it" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Step 4: Plaid Account Setup" -ForegroundColor Cyan
Write-Host "---------------------------" -ForegroundColor Cyan

Write-Host "📝 To complete Plaid setup:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Sign up for Plaid:" -ForegroundColor White
Write-Host "   https://dashboard.plaid.com/signup" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Get your credentials:" -ForegroundColor White
Write-Host "   - Client ID (for sandbox environment)" -ForegroundColor Gray
Write-Host "   - Sandbox Secret" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Update .env with your credentials" -ForegroundColor White
Write-Host ""
Write-Host "4. Test the integration:" -ForegroundColor White
Write-Host "   python -c `"from frontend.utils.plaid_integration import test_connection; test_connection()`"" -ForegroundColor Cyan
Write-Host ""

Write-Host ""
Write-Host "Step 5: Permission Setup" -ForegroundColor Cyan
Write-Host "------------------------" -ForegroundColor Cyan

Write-Host "🔐 Budget permissions are configured in RBAC." -ForegroundColor Yellow
Write-Host ""
Write-Host "Default permissions:" -ForegroundColor White
Write-Host "   - GUEST: No budget access" -ForegroundColor Gray
Write-Host "   - CLIENT: Can view budget (VIEW_BUDGET, CONNECT_BANK)" -ForegroundColor Gray
Write-Host "   - INVESTOR: Full budget access (VIEW_BUDGET, MANAGE_BUDGET, CONNECT_BANK)" -ForegroundColor Gray
Write-Host "   - ADMIN: Full budget access" -ForegroundColor Gray
Write-Host ""

Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "Setup Complete! 🎉" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Start Streamlit:" -ForegroundColor White
Write-Host "   streamlit run streamlit_app.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Login to your account" -ForegroundColor White
Write-Host ""
Write-Host "3. Navigate to Personal Budget page or scroll down on home page" -ForegroundColor White
Write-Host ""
Write-Host "4. Connect your bank account via Plaid" -ForegroundColor White
Write-Host ""
Write-Host "5. Start tracking your budget! 💰" -ForegroundColor White
Write-Host ""

Write-Host "📚 Documentation:" -ForegroundColor Yellow
Write-Host "   - Integration Roadmap: docs\PLAID_INTEGRATION_ROADMAP.md" -ForegroundColor Cyan
Write-Host "   - Database Schema: scripts\setup\budget_schema.sql" -ForegroundColor Cyan
Write-Host "   - Budget Analyzer: frontend\utils\budget_analysis.py" -ForegroundColor Cyan
Write-Host "   - Budget Dashboard: frontend\components\budget_dashboard.py" -ForegroundColor Cyan
Write-Host ""

Write-Host "Need help? Check the documentation or contact support." -ForegroundColor Gray
Write-Host ""
