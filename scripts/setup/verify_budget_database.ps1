# Verify and Setup Budget Database for Plaid Integration
# This script checks if the mydb database exists and creates it if needed

Write-Host "🔍 Verifying Budget Database Setup..." -ForegroundColor Cyan
Write-Host ""

# Check if MySQL is running
Write-Host "1️⃣ Checking MySQL service status..." -ForegroundColor Yellow
$mysqlService = Get-Service -Name "MySQL*" -ErrorAction SilentlyContinue

if ($mysqlService) {
    Write-Host "   ✅ MySQL service found: $($mysqlService.Name)" -ForegroundColor Green
    Write-Host "   Status: $($mysqlService.Status)" -ForegroundColor $(if ($mysqlService.Status -eq 'Running') { 'Green' } else { 'Red' })
} else {
    Write-Host "   ⚠️  MySQL service not found or not running" -ForegroundColor Red
    Write-Host "   Please start MySQL before continuing" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check if port 3306 is listening
Write-Host "2️⃣ Checking if MySQL is listening on port 3306..." -ForegroundColor Yellow
$port3306 = netstat -an | Select-String "3306" | Select-String "LISTENING"

if ($port3306) {
    Write-Host "   ✅ MySQL is listening on port 3306" -ForegroundColor Green
} else {
    Write-Host "   ❌ Port 3306 is not listening" -ForegroundColor Red
    Write-Host "   Check your MySQL configuration" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Test database connection
Write-Host "3️⃣ Testing database connection..." -ForegroundColor Yellow

# Load .env file
$envPath = Join-Path $PSScriptRoot "..\..\..\.env"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match '^BUDGET_MYSQL_(\w+)=(.*)$') {
            $varName = "BUDGET_MYSQL_$($matches[1])"
            $varValue = $matches[2]
            Set-Variable -Name $varName -Value $varValue -Scope Script
        }
    }
    Write-Host "   ✅ Loaded budget database configuration from .env" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  .env file not found, using defaults" -ForegroundColor Yellow
    $BUDGET_MYSQL_HOST = "127.0.0.1"
    $BUDGET_MYSQL_PORT = "3306"
    $BUDGET_MYSQL_USER = "root"
    $BUDGET_MYSQL_PASSWORD = "root"
    $BUDGET_MYSQL_DATABASE = "mydb"
}

Write-Host ""
Write-Host "   Configuration:" -ForegroundColor Cyan
Write-Host "   - Host: $BUDGET_MYSQL_HOST" -ForegroundColor Gray
Write-Host "   - Port: $BUDGET_MYSQL_PORT" -ForegroundColor Gray
Write-Host "   - User: $BUDGET_MYSQL_USER" -ForegroundColor Gray
Write-Host "   - Database: $BUDGET_MYSQL_DATABASE" -ForegroundColor Gray

Write-Host ""

# Create SQL commands to verify/create database
$sqlCommands = @"
-- Check if database exists
SHOW DATABASES LIKE '$BUDGET_MYSQL_DATABASE';

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS $BUDGET_MYSQL_DATABASE
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Select database
USE $BUDGET_MYSQL_DATABASE;

-- Show tables
SHOW TABLES;
"@

# Save to temp file
$tempSqlFile = [System.IO.Path]::GetTempFileName() + ".sql"
$sqlCommands | Out-File -FilePath $tempSqlFile -Encoding UTF8

Write-Host "4️⃣ Running database verification commands..." -ForegroundColor Yellow
Write-Host ""

try {
    # Run MySQL commands
    if ($BUDGET_MYSQL_PASSWORD) {
        $mysqlCmd = "mysql -h $BUDGET_MYSQL_HOST -P $BUDGET_MYSQL_PORT -u $BUDGET_MYSQL_USER -p$BUDGET_MYSQL_PASSWORD < `"$tempSqlFile`""
    } else {
        $mysqlCmd = "mysql -h $BUDGET_MYSQL_HOST -P $BUDGET_MYSQL_PORT -u $BUDGET_MYSQL_USER < `"$tempSqlFile`""
    }
    
    $result = Invoke-Expression $mysqlCmd 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Database '$BUDGET_MYSQL_DATABASE' is ready!" -ForegroundColor Green
        Write-Host ""
        Write-Host "   Output:" -ForegroundColor Gray
        $result | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
    } else {
        Write-Host "   ❌ Error connecting to database" -ForegroundColor Red
        Write-Host "   $result" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
} finally {
    # Clean up temp file
    Remove-Item $tempSqlFile -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "5️⃣ Checking if budget schema exists..." -ForegroundColor Yellow

$schemaFile = Join-Path $PSScriptRoot "budget_schema.sql"
if (Test-Path $schemaFile) {
    Write-Host "   ✅ Found budget_schema.sql" -ForegroundColor Green
    Write-Host ""
    $runSchema = Read-Host "   Do you want to run the budget schema? (y/N)"
    
    if ($runSchema -eq 'y' -or $runSchema -eq 'Y') {
        Write-Host "   Running schema..." -ForegroundColor Yellow
        if ($BUDGET_MYSQL_PASSWORD) {
            mysql -h $BUDGET_MYSQL_HOST -P $BUDGET_MYSQL_PORT -u $BUDGET_MYSQL_USER -p$BUDGET_MYSQL_PASSWORD $BUDGET_MYSQL_DATABASE < $schemaFile
        } else {
            mysql -h $BUDGET_MYSQL_HOST -P $BUDGET_MYSQL_PORT -u $BUDGET_MYSQL_USER $BUDGET_MYSQL_DATABASE < $schemaFile
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Schema applied successfully!" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Error applying schema" -ForegroundColor Red
        }
    }
} else {
    Write-Host "   ⚠️  budget_schema.sql not found at: $schemaFile" -ForegroundColor Yellow
    Write-Host "   You may need to create the schema manually" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✨ Verification complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "   - MySQL Service: $(if ($mysqlService.Status -eq 'Running') { '✅ Running' } else { '❌ Not Running' })" -ForegroundColor $(if ($mysqlService.Status -eq 'Running') { 'Green' } else { 'Red' })
Write-Host "   - Port 3306: $(if ($port3306) { '✅ Listening' } else { '❌ Not Listening' })" -ForegroundColor $(if ($port3306) { 'Green' } else { 'Red' })
Write-Host "   - Database: Check output above" -ForegroundColor Gray
Write-Host ""
Write-Host "🚀 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Restart Streamlit app: streamlit run streamlit_app.py" -ForegroundColor Gray
Write-Host "   2. Navigate to Personal Budget page" -ForegroundColor Gray
Write-Host "   3. Test database connection" -ForegroundColor Gray
Write-Host ""
