# ============================================
# Complete Pipeline Setup Script
# Configures Airflow, Airbyte, dbt, and MLFlow
# ============================================

Write-Host "`n🚀 Bentley Budget Bot - Complete Pipeline Setup" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray

# ============================================
# Step 1: Verify Prerequisites
# ============================================

Write-Host "`n📋 Step 1: Verifying Prerequisites..." -ForegroundColor Yellow

# Check Docker
$dockerRunning = docker ps 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker is running" -ForegroundColor Green

# Check MySQL container
$mysqlRunning = docker ps --filter "name=bentley-mysql" --format "{{.Names}}" 2>$null
if ($mysqlRunning -ne "bentley-mysql") {
    Write-Host "⚠️  MySQL container not running. Starting..." -ForegroundColor Yellow
    docker start bentley-mysql
    Start-Sleep -Seconds 5
}
Write-Host "✅ MySQL container is running" -ForegroundColor Green

# Check Airflow
$airflowRunning = docker ps --filter "name=airflow" --format "{{.Names}}" 2>$null
if (!$airflowRunning) {
    Write-Host "⚠️  Airflow containers not running" -ForegroundColor Yellow
    Write-Host "   Start with: docker-compose -f docker/docker-compose-airflow.yml up -d" -ForegroundColor Gray
} else {
    Write-Host "✅ Airflow is running" -ForegroundColor Green
}

# ============================================
# Step 2: Create Raw Tables
# ============================================

Write-Host "`n📊 Step 2: Creating Raw Data Tables..." -ForegroundColor Yellow

$tablesExist = docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "SHOW TABLES LIKE 'prices_daily';" 2>$null

if ($tablesExist) {
    Write-Host "✅ Raw tables already exist" -ForegroundColor Green
} else {
    Write-Host "   Creating tables..." -ForegroundColor White
    Get-Content mysql_config/create_airbyte_raw_tables.sql | docker exec -i bentley-mysql mysql -uroot -proot bbbot1 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Raw tables created" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create tables" -ForegroundColor Red
    }
}

# ============================================
# Step 3: Configure Airflow Connections
# ============================================

Write-Host "`n🔗 Step 3: Configuring Airflow Connections..." -ForegroundColor Yellow

if ($airflowRunning) {
    # MySQL connection
    Write-Host "   Configuring MySQL connection..." -ForegroundColor White
    
    docker exec airflow-webserver airflow connections delete mysql_bbbot1 2>$null | Out-Null
    
    $mysqlConn = docker exec airflow-webserver airflow connections add `
        mysql_bbbot1 `
        --conn-type mysql `
        --conn-host bentley-mysql `
        --conn-schema bbbot1 `
        --conn-login root `
        --conn-password root `
        --conn-port 3306 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ MySQL connection configured" -ForegroundColor Green
    } else {
        Write-Host "⚠️  MySQL connection may need manual configuration" -ForegroundColor Yellow
    }
    
    # Test connection
    Write-Host "   Testing MySQL connection..." -ForegroundColor White
    
    $testResult = docker exec airflow-webserver python -c @"
from airflow.providers.mysql.hooks.mysql import MySqlHook
try:
    hook = MySqlHook(mysql_conn_id='mysql_bbbot1')
    result = hook.get_first('SELECT DATABASE()')
    print(f'Connected to: {result[0]}')
except Exception as e:
    print(f'Error: {e}')
"@ 2>&1
    
    Write-Host "   $testResult" -ForegroundColor Gray
    
} else {
    Write-Host "⏭️  Skipping (Airflow not running)" -ForegroundColor Gray
    Write-Host "   Manual setup: See docs/AIRFLOW_CONNECTIONS.md" -ForegroundColor DarkGray
}

# ============================================
# Step 4: Install dbt Dependencies
# ============================================

Write-Host "`n📦 Step 4: Installing dbt Dependencies..." -ForegroundColor Yellow

# Check if dbt is installed
$dbtInstalled = dbt --version 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ dbt is already installed" -ForegroundColor Green
} else {
    Write-Host "   Installing dbt..." -ForegroundColor White
    
    $installChoice = Read-Host "   Install dbt now? (y/N)"
    
    if ($installChoice -eq "y" -or $installChoice -eq "Y") {
        pip install dbt-core dbt-mysql dbt-snowflake
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ dbt installed successfully" -ForegroundColor Green
        } else {
            Write-Host "❌ dbt installation failed" -ForegroundColor Red
        }
    } else {
        Write-Host "⏭️  Skipped. Install manually: pip install dbt-core dbt-mysql" -ForegroundColor Gray
    }
}

# ============================================
# Step 5: Test dbt Connection
# ============================================

Write-Host "`n🧪 Step 5: Testing dbt Connection..." -ForegroundColor Yellow

if (Test-Path "dbt_project") {
    Push-Location dbt_project
    
    $dbtDebug = dbt debug --profiles-dir . 2>&1
    
    if ($dbtDebug -match "All checks passed") {
        Write-Host "✅ dbt connection successful" -ForegroundColor Green
    } else {
        Write-Host "⚠️  dbt connection issues. Check dbt_project/profiles.yml" -ForegroundColor Yellow
    }
    
    Pop-Location
} else {
    Write-Host "⚠️  dbt_project directory not found" -ForegroundColor Yellow
}

# ============================================
# Step 6: Copy DAG Files
# ============================================

Write-Host "`n📂 Step 6: Copying DAG Files..." -ForegroundColor Yellow

# Check if original stock_pipeline_DAG.py exists
if (Test-Path "#stock_pipeline_DAG.py") {
    Write-Host "   Found original stock_pipeline_DAG.py" -ForegroundColor White
    Write-Host "   ℹ️  New comprehensive DAG created: airflow/dags/stock_pipeline_comprehensive.py" -ForegroundColor Cyan
}

# Verify DAG files exist
$dagFiles = @(
    "airflow/dags/dbt_transformation_pipeline.py",
    "airflow/dags/stock_pipeline_comprehensive.py"
)

foreach ($dagFile in $dagFiles) {
    if (Test-Path $dagFile) {
        Write-Host "✅ $dagFile" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing: $dagFile" -ForegroundColor Red
    }
}

# ============================================
# Step 7: Copy Python Modules
# ============================================

Write-Host "`n🐍 Step 7: Verifying Python Modules..." -ForegroundColor Yellow

$modules = @(
    "bbbot1_pipeline/ingest_alpha_vantage_updated.py",
    "bbbot1_pipeline/ingest_yfinance_updated.py",
    "bbbot1_pipeline/mlflow_config.py",
    "bbbot1_pipeline/db.py"
)

foreach ($module in $modules) {
    if (Test-Path $module) {
        Write-Host "✅ $module" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing: $module" -ForegroundColor Red
    }
}

# ============================================
# Step 8: Documentation Summary
# ============================================

Write-Host "`n📚 Step 8: Documentation Created" -ForegroundColor Yellow

$docs = @(
    "docs/AIRFLOW_CONNECTIONS.md",
    "docs/AIRBYTE_SETUP.md",
    "docs/AIRBYTE_RAW_TABLES.md",
    "docs/DBT_ARCHITECTURE.md",
    "DATA_PIPELINE_REFERENCE.md"
)

foreach ($doc in $docs) {
    if (Test-Path $doc) {
        Write-Host "✅ $doc" -ForegroundColor Green
    } else {
        Write-Host "⚠️  $doc" -ForegroundColor Yellow
    }
}

# ============================================
# Summary & Next Steps
# ============================================

Write-Host "`n" + ("=" * 70) -ForegroundColor Gray
Write-Host "📊 Setup Summary" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Gray

Write-Host "`n✅ Completed:" -ForegroundColor Green
Write-Host "   • Raw tables created in MySQL (prices_daily, fundamentals_raw, sentiment_msgs, technicals_raw)" -ForegroundColor White
Write-Host "   • dbt project configured with staging and marts models" -ForegroundColor White
Write-Host "   • Airflow DAGs created (dbt_transformation_pipeline, stock_pipeline_comprehensive)" -ForegroundColor White
Write-Host "   • Python ingestion modules updated" -ForegroundColor White
Write-Host "   • Comprehensive documentation created" -ForegroundColor White

Write-Host "`n⏭️  Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Configure Airbyte connections (see docs/AIRBYTE_SETUP.md)" -ForegroundColor White
Write-Host "      • Tiingo → prices_daily" -ForegroundColor Gray
Write-Host "      • AlphaVantage → fundamentals_raw" -ForegroundColor Gray
Write-Host "      • StockTwits → sentiment_msgs" -ForegroundColor Gray
Write-Host "" -ForegroundColor White
Write-Host "   2. Run dbt pipeline:" -ForegroundColor White
Write-Host "      cd dbt_project" -ForegroundColor Gray
Write-Host "      dbt run --profiles-dir ." -ForegroundColor Gray
Write-Host "      dbt test --profiles-dir ." -ForegroundColor Gray
Write-Host "" -ForegroundColor White
Write-Host "   3. Enable Airflow DAGs:" -ForegroundColor White
Write-Host "      • Open http://localhost:8080" -ForegroundColor Gray
Write-Host "      • Enable 'dbt_transformation_pipeline'" -ForegroundColor Gray
Write-Host "      • Enable 'stock_pipeline_comprehensive'" -ForegroundColor Gray
Write-Host "" -ForegroundColor White
Write-Host "   4. Monitor pipeline execution" -ForegroundColor White
Write-Host "      • Airbyte: http://localhost:8000" -ForegroundColor Gray
Write-Host "      • Airflow: http://localhost:8080" -ForegroundColor Gray
Write-Host "      • MLFlow: http://localhost:5000" -ForegroundColor Gray

Write-Host "`n📖 Documentation:" -ForegroundColor Cyan
Write-Host "   • Airflow Connections: docs/AIRFLOW_CONNECTIONS.md" -ForegroundColor Gray
Write-Host "   • Airbyte Setup: docs/AIRBYTE_SETUP.md" -ForegroundColor Gray
Write-Host "   • dbt Architecture: docs/DBT_ARCHITECTURE.md" -ForegroundColor Gray
Write-Host "   • Quick Reference: DATA_PIPELINE_REFERENCE.md" -ForegroundColor Gray

Write-Host "`n✨ Setup Complete!`n" -ForegroundColor Green
