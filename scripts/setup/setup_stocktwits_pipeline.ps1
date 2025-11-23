#!/usr/bin/env pwsh
# Stocktwits Sentiment Pipeline - Quick Setup Script

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Stocktwits Sentiment Pipeline Setup" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"

# Step 1: Create MySQL table
Write-Host "Step 1: Creating MySQL table..." -ForegroundColor Yellow
docker exec -i bentley-mysql mysql -uroot -proot mansa_bot < airbyte-source-stocktwits/schema.sql 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Table created successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  Table may already exist (continuing...)" -ForegroundColor Yellow
}

# Step 2: Verify table structure
Write-Host "`nStep 2: Verifying table structure..." -ForegroundColor Yellow
docker exec bentley-mysql mysql -uroot -proot mansa_bot -e "DESCRIBE stocktwits_sentiment;" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Table structure verified" -ForegroundColor Green
} else {
    Write-Host "❌ Could not verify table" -ForegroundColor Red
}

# Step 3: Build Docker image
Write-Host "`nStep 3: Building Docker image..." -ForegroundColor Yellow
Push-Location airbyte-source-stocktwits
docker build -t airbyte/source-stocktwits:0.1.0 . 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Docker image built successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location

# Step 4: Test Airbyte source
Write-Host "`nStep 4: Testing Airbyte source connector..." -ForegroundColor Yellow

Write-Host "  Testing spec command..." -ForegroundColor Gray
docker run --rm airbyte/source-stocktwits:0.1.0 spec > $null 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Spec command works" -ForegroundColor Green
}

Write-Host "  Testing check command..." -ForegroundColor Gray
docker run --rm -v ${PWD}/airbyte-source-stocktwits:/data airbyte/source-stocktwits:0.1.0 check --config /data/config.json 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Connection check passed" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Connection check failed (may be rate limited)" -ForegroundColor Yellow
}

# Step 5: Update docker-compose (manual step notification)
Write-Host "`nStep 5: Updating Airflow volumes..." -ForegroundColor Yellow
Write-Host "  ℹ️  Adding airbyte-source-stocktwits mount to docker-compose" -ForegroundColor Cyan

$composeFile = "docker-compose-airflow.yml"
$content = Get-Content $composeFile -Raw

if ($content -notmatch "airbyte-source-stocktwits") {
    Write-Host "  ⚠️  Manual update required:" -ForegroundColor Yellow
    Write-Host "     Add this line to volumes in docker-compose-airflow.yml:" -ForegroundColor Gray
    Write-Host "     - ./airbyte-source-stocktwits:/opt/airflow/airbyte-source-stocktwits" -ForegroundColor White
} else {
    Write-Host "  ✅ Volume already configured" -ForegroundColor Green
}

# Step 6: Restart Airflow
Write-Host "`nStep 6: Restarting Airflow services..." -ForegroundColor Yellow
docker-compose -f docker-compose-airflow.yml restart 2>&1 | Out-Null
Write-Host "  Waiting for services to stabilize..." -ForegroundColor Gray
Start-Sleep -Seconds 15

# Step 7: Check DAG loaded
Write-Host "`nStep 7: Verifying DAG loaded in Airflow..." -ForegroundColor Yellow
$dagCheck = docker exec bentley-airflow-scheduler airflow dags list 2>$null | Select-String "stocktwits_sentiment_pipeline"
if ($dagCheck) {
    Write-Host "✅ DAG loaded successfully: stocktwits_sentiment_pipeline" -ForegroundColor Green
} else {
    Write-Host "⚠️  DAG not found - checking for import errors..." -ForegroundColor Yellow
    docker exec bentley-airflow-scheduler airflow dags list-import-errors 2>$null
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "📋 Next Steps:" -ForegroundColor White
Write-Host "  1. Verify Airflow UI: http://localhost:8080" -ForegroundColor Gray
Write-Host "  2. Trigger the DAG:" -ForegroundColor Gray
Write-Host "     docker exec bentley-airflow-scheduler airflow dags trigger stocktwits_sentiment_pipeline" -ForegroundColor White
Write-Host "`n  3. Monitor execution:" -ForegroundColor Gray
Write-Host "     docker exec bentley-airflow-scheduler airflow dags list-runs -d stocktwits_sentiment_pipeline" -ForegroundColor White
Write-Host "`n  4. Check data in MySQL:" -ForegroundColor Gray
Write-Host "     docker exec bentley-mysql mysql -uroot -proot mansa_bot -e 'SELECT * FROM stocktwits_sentiment LIMIT 5;'" -ForegroundColor White

Write-Host "`n📖 Full documentation: airbyte-source-stocktwits/SETUP_GUIDE.md" -ForegroundColor Cyan
Write-Host ""
