# ============================================
# Setup Airbyte Raw Tables
# Creates tables in MySQL and optionally Snowflake
# ============================================

Write-Host "`n🗄️  Bentley Budget Bot - Airbyte Raw Tables Setup" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# ============================================
# MySQL Setup
# ============================================

Write-Host "`n📊 Creating MySQL Tables..." -ForegroundColor Yellow

$mysqlHost = "127.0.0.1"
$mysqlPort = 3307
$mysqlUser = "root"
$mysqlPassword = "root"
$mysqlDatabase = "bbbot1"
$mysqlScript = "mysql_config/create_airbyte_raw_tables.sql"

# Check if MySQL script exists
if (-not (Test-Path $mysqlScript)) {
    Write-Host "❌ MySQL script not found: $mysqlScript" -ForegroundColor Red
    exit 1
}

Write-Host "   Host: $mysqlHost`:$mysqlPort" -ForegroundColor Gray
Write-Host "   Database: $mysqlDatabase" -ForegroundColor Gray
Write-Host "   Script: $mysqlScript" -ForegroundColor Gray

# Execute MySQL script
try {
    Write-Host "`n   Executing MySQL script..." -ForegroundColor White
    
    # Using mysql CLI (ensure mysql is in PATH or use full path)
    $mysqlCommand = "mysql -h $mysqlHost -P $mysqlPort -u $mysqlUser -p$mysqlPassword $mysqlDatabase < $mysqlScript"
    
    # Alternative: Use Docker exec if MySQL is in container
    $containerCommand = "docker exec -i bentley-mysql mysql -u $mysqlUser -p$mysqlPassword $mysqlDatabase < $mysqlScript"
    
    Write-Host "`n   Option 1 - Direct MySQL:" -ForegroundColor Cyan
    Write-Host "   $mysqlCommand" -ForegroundColor Gray
    
    Write-Host "`n   Option 2 - Docker Exec:" -ForegroundColor Cyan
    Write-Host "   $containerCommand" -ForegroundColor Gray
    
    # Check if Docker container is running
    $containerRunning = docker ps --filter "name=bentley-mysql" --format "{{.Names}}" 2>$null
    
    if ($containerRunning -eq "bentley-mysql") {
        Write-Host "`n✅ MySQL container 'bentley-mysql' is running" -ForegroundColor Green
        Write-Host "   Executing via Docker..." -ForegroundColor White
        
        Get-Content $mysqlScript | docker exec -i bentley-mysql mysql -u $mysqlUser -p$mysqlPassword $mysqlDatabase
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ MySQL tables created successfully!" -ForegroundColor Green
        } else {
            Write-Host "❌ MySQL table creation failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
        }
    } else {
        Write-Host "⚠️  MySQL container not running" -ForegroundColor Yellow
        Write-Host "   Start container with: docker-compose up -d mysql" -ForegroundColor Gray
        Write-Host "   Then run this script again" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "❌ Error executing MySQL script: $_" -ForegroundColor Red
}

# ============================================
# Verify MySQL Tables
# ============================================

Write-Host "`n📋 Verifying MySQL Tables..." -ForegroundColor Yellow

try {
    $verifyQuery = @"
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    CREATE_TIME,
    TABLE_COMMENT
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = '$mysqlDatabase'
  AND TABLE_NAME IN ('prices_daily', 'fundamentals_raw', 'sentiment_msgs', 'technicals_raw')
ORDER BY TABLE_NAME;
"@
    
    $result = $verifyQuery | docker exec -i bentley-mysql mysql -u $mysqlUser -p$mysqlPassword $mysqlDatabase 2>$null
    
    if ($result) {
        Write-Host $result -ForegroundColor White
        Write-Host "✅ Verification complete" -ForegroundColor Green
    }
    
} catch {
    Write-Host "⚠️  Could not verify tables: $_" -ForegroundColor Yellow
}

# ============================================
# Snowflake Setup (Optional)
# ============================================

Write-Host "`n❄️  Snowflake Setup" -ForegroundColor Cyan

$snowflakeScript = "airbyte/config/snowflake_airbyte_raw_tables.sql"

if (Test-Path $snowflakeScript) {
    Write-Host "   Script: $snowflakeScript" -ForegroundColor Gray
    Write-Host "   ℹ️  Snowflake setup requires:" -ForegroundColor Yellow
    Write-Host "      1. Snowflake CLI (snowsql) installed" -ForegroundColor Gray
    Write-Host "      2. Snowflake account credentials configured" -ForegroundColor Gray
    Write-Host "      3. Database: MARKET_DATA" -ForegroundColor Gray
    Write-Host "      4. Schema: PUBLIC" -ForegroundColor Gray
    
    $setupSnowflake = Read-Host "`n   Setup Snowflake tables now? (y/N)"
    
    if ($setupSnowflake -eq "y" -or $setupSnowflake -eq "Y") {
        Write-Host "`n   Enter Snowflake details:" -ForegroundColor White
        $snowflakeAccount = Read-Host "   Account (e.g., abc12345.us-east-1)"
        $snowflakeUser = Read-Host "   Username"
        $snowflakeDatabase = Read-Host "   Database (default: MARKET_DATA)"
        
        if ([string]::IsNullOrWhiteSpace($snowflakeDatabase)) {
            $snowflakeDatabase = "MARKET_DATA"
        }
        
        Write-Host "`n   Executing Snowflake script..." -ForegroundColor White
        
        # Execute via snowsql
        $snowsqlCommand = "snowsql -a $snowflakeAccount -u $snowflakeUser -d $snowflakeDatabase -f $snowflakeScript"
        
        Write-Host "   Command: $snowsqlCommand" -ForegroundColor Gray
        
        try {
            & snowsql -a $snowflakeAccount -u $snowflakeUser -d $snowflakeDatabase -f $snowflakeScript
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Snowflake tables created successfully!" -ForegroundColor Green
            } else {
                Write-Host "❌ Snowflake table creation failed" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ Error executing Snowflake script: $_" -ForegroundColor Red
            Write-Host "   Install snowsql: https://docs.snowflake.com/en/user-guide/snowsql-install-config.html" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⏭️  Skipping Snowflake setup" -ForegroundColor Gray
        Write-Host "   Run manually later with:" -ForegroundColor Gray
        Write-Host "   snowsql -a YOUR_ACCOUNT -u YOUR_USER -d MARKET_DATA -f $snowflakeScript" -ForegroundColor DarkGray
    }
} else {
    Write-Host "   ⚠️  Snowflake script not found: $snowflakeScript" -ForegroundColor Yellow
}

# ============================================
# Update dbt Sources
# ============================================

Write-Host "`n🔧 Updating dbt sources..." -ForegroundColor Yellow

$dbtSourcesFile = "dbt_project/models/staging/sources.yml"

$sourcesContent = @"
# ============================================
# dbt Sources Configuration
# Maps raw tables for staging models
# ============================================

version: 2

sources:
  - name: raw
    description: "Raw data tables loaded by Airbyte from external APIs"
    database: bbbot1  # MySQL database
    schema: bbbot1    # Use database name as schema for MySQL
    
    tables:
      - name: prices_daily
        description: "Daily OHLC price data from Tiingo API"
        columns:
          - name: id
            description: "Primary key"
          - name: ticker
            description: "Stock ticker symbol"
          - name: date
            description: "Trading date"
          - name: close
            description: "Closing price"
          - name: volume
            description: "Trading volume"
          - name: created_at
            description: "Record creation timestamp"
        
        # Data quality tests
        tests:
          - dbt_utils.expression_is_true:
              expression: "close > 0"
        
        # Freshness check
        freshness:
          warn_after: {count: 2, period: day}
          error_after: {count: 5, period: day}
      
      - name: fundamentals_raw
        description: "Financial statement data from AlphaVantage/yfinance"
        columns:
          - name: id
            description: "Primary key"
          - name: ticker
            description: "Stock ticker symbol"
          - name: report_date
            description: "Financial report date"
          - name: net_income
            description: "Net income"
          - name: ebit
            description: "Earnings before interest and taxes"
          - name: ebitda
            description: "Earnings before interest, taxes, depreciation, and amortization"
          - name: total_assets
            description: "Total assets"
          - name: total_equity
            description: "Total shareholder equity"
          - name: total_liabilities
            description: "Total liabilities"
          - name: cash_and_equivalents
            description: "Cash and cash equivalents"
          - name: shares_outstanding
            description: "Number of shares outstanding"
        
        freshness:
          warn_after: {count: 7, period: day}
          error_after: {count: 14, period: day}
      
      - name: sentiment_msgs
        description: "Social sentiment messages from StockTwits/Twitter"
        columns:
          - name: id
            description: "Primary key"
          - name: ticker
            description: "Stock ticker symbol"
          - name: timestamp
            description: "Message timestamp"
          - name: message_id
            description: "External message ID"
          - name: message_text
            description: "Message content"
          - name: sentiment_score
            description: "Sentiment score from -1 to 1"
          - name: sentiment_label
            description: "Sentiment classification: bullish, bearish, neutral"
          - name: source
            description: "Data source: stocktwits, twitter, reddit"
        
        freshness:
          warn_after: {count: 1, period: day}
          error_after: {count: 3, period: day}
      
      - name: technicals_raw
        description: "Technical indicators calculated from price data"
        columns:
          - name: id
            description: "Primary key"
          - name: ticker
            description: "Stock ticker symbol"
          - name: date
            description: "Calculation date"
          - name: sma_20
            description: "20-day Simple Moving Average"
          - name: sma_50
            description: "50-day Simple Moving Average"
          - name: sma_200
            description: "200-day Simple Moving Average"
          - name: rsi_14
            description: "14-day Relative Strength Index"
          - name: macd
            description: "MACD line"
          - name: macd_signal
            description: "MACD signal line"
        
        freshness:
          warn_after: {count: 2, period: day}
          error_after: {count: 5, period: day}
"@

try {
    New-Item -ItemType Directory -Force -Path (Split-Path $dbtSourcesFile) | Out-Null
    $sourcesContent | Out-File -FilePath $dbtSourcesFile -Encoding UTF8
    Write-Host "✅ Created: $dbtSourcesFile" -ForegroundColor Green
} catch {
    Write-Host "❌ Error creating sources.yml: $_" -ForegroundColor Red
}

# ============================================
# Summary
# ============================================

Write-Host "`n📊 Setup Summary" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

Write-Host "`n✅ Created Tables:" -ForegroundColor Green
Write-Host "   • prices_daily (OHLC price data)" -ForegroundColor White
Write-Host "   • fundamentals_raw (financial statements)" -ForegroundColor White
Write-Host "   • sentiment_msgs (social sentiment)" -ForegroundColor White
Write-Host "   • technicals_raw (technical indicators)" -ForegroundColor White

Write-Host "`n📝 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Configure Airbyte connections to populate these tables" -ForegroundColor White
Write-Host "   2. Update dbt staging models to use new table names:" -ForegroundColor White
Write-Host "      • stg_prices.sql → source('raw', 'prices_daily')" -ForegroundColor Gray
Write-Host "      • stg_fundamentals.sql → source('raw', 'fundamentals_raw')" -ForegroundColor Gray
Write-Host "      • stg_sentiment.sql → source('raw', 'sentiment_msgs')" -ForegroundColor Gray
Write-Host "   3. Run dbt to validate: cd dbt_project && dbt run" -ForegroundColor White

Write-Host "`n🔍 Verification:" -ForegroundColor Yellow
Write-Host "   MySQL: docker exec -i bentley-mysql mysql -u root -proot bbbot1 -e 'SHOW TABLES;'" -ForegroundColor Gray

Write-Host "`n✨ Done!`n" -ForegroundColor Green
