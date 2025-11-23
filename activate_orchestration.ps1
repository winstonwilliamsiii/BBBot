# Quick Start Script for Bentley Budget Bot Orchestration
# Unpauses all DAGs and prepares the pipeline for execution

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Bentley Budget Bot - DAG Activation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$dags = @(
    "airbyte_sync_dag",
    "knime_cli_workflow", 
    "mlflow_logging_dag",
    "bentley_master_orchestration"
)

Write-Host "📋 Activating orchestration DAGs..." -ForegroundColor Yellow
Write-Host ""

foreach ($dag in $dags) {
    try {
        Write-Host "  ⏸  Unpausing: $dag" -ForegroundColor Gray
        docker exec bentley-airflow-scheduler airflow dags unpause $dag 2>$null | Out-Null
        Write-Host "  ✅ Activated: $dag" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Failed to unpause: $dag" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Pipeline Architecture" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Airbyte Sync DAG      (@hourly)" -ForegroundColor White
Write-Host "     └── Produces: Dataset(mysql://mansa_bot/binance_ohlcv)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  2. KNIME CLI Workflow    (Dataset-triggered)" -ForegroundColor White
Write-Host "     ├── Consumes: Airbyte dataset" -ForegroundColor DarkGray
Write-Host "     └── Produces: Dataset(mysql://mansa_bot/knime_processed)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  3. MLflow Logging DAG    (Dataset-triggered)" -ForegroundColor White
Write-Host "     └── Consumes: Airbyte + KNIME datasets" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  4. Master Orchestration  (@daily or manual)" -ForegroundColor White
Write-Host "     └── Coordinates all pipeline stages" -ForegroundColor DarkGray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Open Airflow UI: " -NoNewline -ForegroundColor Yellow
Write-Host "http://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. View DAGs in VS Code Airflow Extension" -ForegroundColor Yellow
Write-Host "   - Click Airflow icon in sidebar" -ForegroundColor DarkGray
Write-Host "   - Or: Ctrl+Shift+P → 'Airflow: Open'" -ForegroundColor DarkGray
Write-Host ""
Write-Host "3. Trigger Master Orchestration:" -ForegroundColor Yellow
Write-Host "   docker exec bentley-airflow-scheduler airflow dags trigger bentley_master_orchestration" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Monitor execution in Airflow UI or VS Code" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ DAGs activated and ready!" -ForegroundColor Green
Write-Host ""

# Check if VS Code Airflow extension can connect
Write-Host "Testing Airflow API connection..." -ForegroundColor Yellow
try {
    $headers = @{ Authorization = "Basic " + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("admin:admin")) }
    $response = Invoke-RestMethod -Uri "http://localhost:8080/api/v1/health" -Headers $headers -Method Get
    
    if ($response.metadatabase.status -eq "healthy") {
        Write-Host "✅ Airflow API is healthy and accessible" -ForegroundColor Green
        Write-Host "✅ VS Code Airflow Extension should work!" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Could not connect to Airflow API" -ForegroundColor Yellow
    Write-Host "   Make sure Airflow webserver is running" -ForegroundColor DarkGray
}

Write-Host ""
