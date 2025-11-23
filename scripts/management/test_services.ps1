# Bentley Budget Bot - Service Connection Testing Script
# Tests MLflow and Airbyte connections and provides diagnostic information

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "🧪 Bentley Bot Service Testing" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Test MLflow Connection
Write-Host "1️⃣  Testing MLflow (Port 5000)..." -ForegroundColor Yellow
try {
    $mlflowResponse = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 5 -UseBasicParsing
    Write-Host "   ✅ MLflow is ACCESSIBLE!" -ForegroundColor Green
    Write-Host "   📊 Status Code: $($mlflowResponse.StatusCode)" -ForegroundColor White
    Write-Host "   🌐 URL: http://localhost:5000" -ForegroundColor Cyan
} catch {
    Write-Host "   ❌ MLflow is NOT accessible" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   💡 Tip: Check if container is still installing packages" -ForegroundColor Yellow
    Write-Host "   Run: docker logs bentley-mlflow-standalone --tail 50" -ForegroundColor Gray
}

Write-Host ""

# Test Airbyte Web UI
Write-Host "2️⃣  Testing Airbyte Web UI (Port 8000)..." -ForegroundColor Yellow
try {
    $airbyteWebResponse = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 5 -UseBasicParsing
    Write-Host "   ✅ Airbyte Web UI is ACCESSIBLE!" -ForegroundColor Green
    Write-Host "   📊 Status Code: $($airbyteWebResponse.StatusCode)" -ForegroundColor White
    Write-Host "   🌐 URL: http://localhost:8000" -ForegroundColor Cyan
} catch {
    Write-Host "   ❌ Airbyte Web UI is NOT accessible" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test Airbyte API
Write-Host "3️⃣  Testing Airbyte API (Port 8001)..." -ForegroundColor Yellow
try {
    $airbyteApiResponse = Invoke-WebRequest -Uri "http://localhost:8001/api/v1/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "   ✅ Airbyte API is ACCESSIBLE!" -ForegroundColor Green
    Write-Host "   📊 Status Code: $($airbyteApiResponse.StatusCode)" -ForegroundColor White
    Write-Host "   🌐 URL: http://localhost:8001" -ForegroundColor Cyan
    Write-Host "   Response: $($airbyteApiResponse.Content)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Airbyte API is NOT accessible" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   💡 Tip: Check if server and temporal containers are running" -ForegroundColor Yellow
    Write-Host "   Run: docker ps | Select-String airbyte" -ForegroundColor Gray
}

Write-Host ""

# Test Airflow
Write-Host "4️⃣  Testing Airflow Web UI (Port 8080)..." -ForegroundColor Yellow
try {
    $airflowResponse = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "   ✅ Airflow is ACCESSIBLE!" -ForegroundColor Green
    Write-Host "   📊 Status Code: $($airflowResponse.StatusCode)" -ForegroundColor White
    Write-Host "   🌐 URL: http://localhost:8080" -ForegroundColor Cyan
    Write-Host "   👤 Default credentials: admin / admin" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Airflow is NOT accessible" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "📋 Container Status" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

docker ps --format "table {{.Names}}\t{{.Status}}" | Select-String -Pattern "NAME|mlflow|airbyte|airflow"

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "💡 Troubleshooting Tips" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "If services are not accessible:" -ForegroundColor Yellow
Write-Host "  1. Check logs: docker logs <container-name>" -ForegroundColor White
Write-Host "  2. Restart service: docker restart <container-name>" -ForegroundColor White
Write-Host "  3. View all containers: docker ps -a" -ForegroundColor White
Write-Host "  4. Check Docker resources: docker stats --no-stream" -ForegroundColor White
Write-Host ""
Write-Host "Common issues:" -ForegroundColor Yellow
Write-Host "  • MLflow: May take 2-3 minutes to install packages on first run" -ForegroundColor White
Write-Host "  • Airbyte: Requires database, server, temporal, and worker all running" -ForegroundColor White
Write-Host "  • Airflow: Check DAGs folder is mounted correctly" -ForegroundColor White
Write-Host ""
