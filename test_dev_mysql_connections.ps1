# Test Dev Environment Database Connections
# Verifies all Python applications can connect to MySQL Docker container

Write-Host "`n🧪 Testing Dev Environment Database Connections" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray
Write-Host "Testing all Python services MySQL connectivity`n" -ForegroundColor Gray

$testsPassed = 0
$testsFailed = 0
$warnings = @()

# Step 1: Verify .env file loaded
Write-Host "📋 Step 1: Verifying .env configuration..." -ForegroundColor White

if (Test-Path .env) {
    Write-Host "   ✅ .env file found" -ForegroundColor Green
    
    # Check for required MySQL variables
    $envContent = Get-Content .env -Raw
    $requiredVars = @("MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE")
    
    foreach ($var in $requiredVars) {
        if ($envContent -match "$var=") {
            Write-Host "   ✅ $var is set" -ForegroundColor Green
            $testsPassed++
        } else {
            Write-Host "   ❌ $var is missing" -ForegroundColor Red
            $testsFailed++
        }
    }
} else {
    Write-Host "   ❌ .env file not found!" -ForegroundColor Red
    $testsFailed++
}

# Step 2: Test MySQL connection from Python
Write-Host "`n📋 Step 2: Testing Python MySQL connector..." -ForegroundColor White

$pythonTest = @"
import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    import mysql.connector
    
    # Test connection
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', '127.0.0.1'),
        port=int(os.getenv('MYSQL_PORT', 3307)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', 'root'),
        database=os.getenv('MYSQL_DATABASE', 'mansa_bot')
    )
    
    cursor = conn.cursor()
    cursor.execute('SELECT DATABASE(), VERSION()')
    result = cursor.fetchone()
    
    print(f'CONNECTED|{result[0]}|{result[1]}')
    
    cursor.close()
    conn.close()
    sys.exit(0)
    
except Exception as e:
    print(f'ERROR|{str(e)}')
    sys.exit(1)
"@

$pythonTest | Out-File -FilePath "temp_mysql_test.py" -Encoding UTF8

$result = & python temp_mysql_test.py 2>&1
Remove-Item "temp_mysql_test.py" -Force

if ($result -match "CONNECTED\|(.+)\|(.+)") {
    Write-Host "   ✅ Python mysql.connector works" -ForegroundColor Green
    Write-Host "   📊 Database: $($matches[1])" -ForegroundColor Cyan
    Write-Host "   📦 MySQL Version: $($matches[2])" -ForegroundColor Cyan
    $testsPassed++
} else {
    Write-Host "   ❌ Python connection failed: $result" -ForegroundColor Red
    $testsFailed++
}

# Step 3: Test services/mysql_portfolio.py
Write-Host "`n📋 Step 3: Testing services/mysql_portfolio.py..." -ForegroundColor White

$portfolioTest = @"
import sys
sys.path.insert(0, '.')

try:
    from services.mysql_portfolio import get_mysql_connection
    
    conn = get_mysql_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        print('SUCCESS|mysql_portfolio')
    else:
        print('ERROR|Connection returned None')
        sys.exit(1)
except Exception as e:
    print(f'ERROR|{str(e)}')
    sys.exit(1)
"@

$portfolioTest | Out-File -FilePath "temp_portfolio_test.py" -Encoding UTF8

$result = & python temp_portfolio_test.py 2>&1
Remove-Item "temp_portfolio_test.py" -Force

if ($result -match "SUCCESS") {
    Write-Host "   ✅ services/mysql_portfolio.py works" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "   ❌ services/mysql_portfolio.py failed: $result" -ForegroundColor Red
    $testsFailed++
}

# Step 4: Test prediction_analytics/config.py
Write-Host "`n📋 Step 4: Testing prediction_analytics/config.py..." -ForegroundColor White

$predictionTest = @"
import sys
sys.path.insert(0, '.')

try:
    from prediction_analytics.config import settings
    
    print(f'SUCCESS|{settings.db_host}:{settings.db_port}|{settings.db_name}')
except Exception as e:
    print(f'ERROR|{str(e)}')
    sys.exit(1)
"@

$predictionTest | Out-File -FilePath "temp_prediction_test.py" -Encoding UTF8

$result = & python temp_prediction_test.py 2>&1
Remove-Item "temp_prediction_test.py" -Force

if ($result -match "SUCCESS\|(.+):(.+)\|(.+)") {
    Write-Host "   ✅ prediction_analytics/config.py loads" -ForegroundColor Green
    Write-Host "   🔧 Config: $($matches[1]):$($matches[2]) → $($matches[3])" -ForegroundColor Cyan
    
    if ($matches[2] -eq "3307") {
        Write-Host "   ✅ Using correct Docker port (3307)" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "   ⚠️  Warning: Using port $($matches[2]) instead of 3307" -ForegroundColor Yellow
        $warnings += "prediction_analytics config using wrong port"
        $testsPassed++
    }
} else {
    Write-Host "   ❌ prediction_analytics/config.py failed: $result" -ForegroundColor Red
    $testsFailed++
}

# Step 5: Test demo_db.py connection
Write-Host "`n📋 Step 5: Testing prediction_analytics/services/demo_db.py..." -ForegroundColor White

$demoTest = @"
import sys
sys.path.insert(0, '.')

try:
    from prediction_analytics.services.demo_db import get_connection
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DATABASE(), VERSION()')
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    print(f'SUCCESS|{result[0]}|{result[1]}')
except Exception as e:
    print(f'ERROR|{str(e)}')
    sys.exit(1)
"@

$demoTest | Out-File -FilePath "temp_demo_test.py" -Encoding UTF8

$result = & python temp_demo_test.py 2>&1
Remove-Item "temp_demo_test.py" -Force

if ($result -match "SUCCESS\|(.+)\|(.+)") {
    Write-Host "   ✅ demo_db.py connects successfully" -ForegroundColor Green
    Write-Host "   📊 Database: $($matches[1])" -ForegroundColor Cyan
    $testsPassed++
} else {
    Write-Host "   ❌ demo_db.py failed: $result" -ForegroundColor Red
    $testsFailed++
}

# Step 6: Test all database access
Write-Host "`n📋 Step 6: Testing access to all databases..." -ForegroundColor White

$databases = @("mansa_bot", "bbbot1", "mlflow_db", "mansa_quant", "Bentley_Budget")

foreach ($db in $databases) {
    $dbTest = @"
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', '127.0.0.1'),
        port=int(os.getenv('MYSQL_PORT', 3307)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', 'root'),
        database='$db'
    )
    
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s', ('$db',))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    print(f'SUCCESS|$db|{count}')
except Exception as e:
    print(f'ERROR|{str(e)}')
"@

    $dbTest | Out-File -FilePath "temp_db_test.py" -Encoding UTF8
    $result = & python temp_db_test.py 2>&1
    Remove-Item "temp_db_test.py" -Force

    if ($result -match "SUCCESS\|$db\|(.+)") {
        Write-Host "   ✅ $db - $($matches[1]) tables" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "   ❌ $db - Cannot access" -ForegroundColor Red
        $testsFailed++
    }
}

# Summary
Write-Host "`n" -NoNewline
Write-Host "=" * 70 -ForegroundColor Gray
Write-Host "🧪 Dev Environment Test Results" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray

$total = $testsPassed + $testsFailed
$successRate = [math]::Round(($testsPassed / $total) * 100, 1)

Write-Host "`n📊 Tests Passed: $testsPassed / $total ($successRate%)" -ForegroundColor $(if ($testsPassed -eq $total) { "Green" } else { "Yellow" })

if ($testsFailed -gt 0) {
    Write-Host "❌ Tests Failed: $testsFailed" -ForegroundColor Red
}

if ($warnings.Count -gt 0) {
    Write-Host "`n⚠️  Warnings:" -ForegroundColor Yellow
    foreach ($warning in $warnings) {
        Write-Host "   • $warning" -ForegroundColor Yellow
    }
}

Write-Host "`n📝 Configuration Summary:" -ForegroundColor Cyan
Write-Host "   Host: 127.0.0.1" -ForegroundColor White
Write-Host "   Port: 3307 (Docker)" -ForegroundColor White
Write-Host "   User: root" -ForegroundColor White
Write-Host "   Container: bentley-mysql" -ForegroundColor White

Write-Host "`n✨ Updated Files:" -ForegroundColor Cyan
Write-Host "   • .env - Added MySQL environment variables" -ForegroundColor Green
Write-Host "   • prediction_analytics/config.py - Port 3307" -ForegroundColor Green
Write-Host "   • prediction_analytics/config_dual.py - Port 3307" -ForegroundColor Green
Write-Host "   • services/mysql_portfolio.py - Port 3307" -ForegroundColor Green

if ($testsPassed -eq $total) {
    Write-Host "`n🎉 All dev environment database connections are working!" -ForegroundColor Green
    Write-Host "   Your Python services can now connect to MySQL Docker container." -ForegroundColor White
} else {
    Write-Host "`n⚠️  Some tests failed. Check error messages above." -ForegroundColor Yellow
    Write-Host "   Ensure MySQL Docker container is running: .\start_mysql_docker.ps1" -ForegroundColor Gray
}

Write-Host "`n"
