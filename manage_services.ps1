# Bentley Budget Bot - Complete Docker Setup
# Manages Airflow, Airbyte, and Streamlit services

param(
    [string]$Service = "all",  # Options: airflow, airbyte, streamlit, all
    [string]$Action = "start"  # Options: start, stop, status, logs
)

# Set encoding
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🚀 Bentley Budget Bot - Docker Service Manager" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

function Show-ServiceStatus {
    Write-Host "📊 Current Service Status:" -ForegroundColor Cyan
    
    Write-Host "`n🔄 Airflow Services:" -ForegroundColor Yellow
    docker-compose -f docker-compose-airflow.yml ps
    
    Write-Host "`n🔄 Airbyte Services:" -ForegroundColor Yellow  
    docker-compose -f docker-compose-airbyte-fixed.yml ps
    
    Write-Host "`n📊 Streamlit App:" -ForegroundColor Yellow
    docker-compose ps
}

function Start-AllServices {
    Write-Host "🚀 Starting all services..." -ForegroundColor Green
    
    # Start Airflow + Streamlit
    Write-Host "`n1️⃣ Starting Airflow and Streamlit..." -ForegroundColor Cyan
    docker-compose -f docker-compose-airflow.yml up -d
    
    # Start Airbyte (separate network)
    Write-Host "`n2️⃣ Starting Airbyte..." -ForegroundColor Cyan
    docker-compose -f docker-compose-airbyte-fixed.yml up -d
    
    Write-Host "`n⏳ Waiting for services to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    Show-ServiceStatus
    
    Write-Host "`n🎉 All services started!" -ForegroundColor Green
    Write-Host "`n🌐 Access Points:" -ForegroundColor Yellow
    Write-Host "   • Streamlit App:   http://localhost:8501" -ForegroundColor Cyan
    Write-Host "   • Airflow UI:      http://localhost:8080 (admin/admin)" -ForegroundColor Cyan
    Write-Host "   • Airbyte UI:      http://localhost:8000" -ForegroundColor Cyan
    Write-Host "   • MLflow UI:       http://localhost:5000" -ForegroundColor Cyan
}

function Stop-AllServices {
    Write-Host "🛑 Stopping all services..." -ForegroundColor Red
    
    docker-compose -f docker-compose-airflow.yml down
    docker-compose -f docker-compose-airbyte-fixed.yml down
    docker-compose down
    
    Write-Host "✅ All services stopped." -ForegroundColor Green
}

function Start-ServiceByName($serviceName) {
    switch ($serviceName) {
        "airflow" {
            Write-Host "🚀 Starting Airflow services..." -ForegroundColor Green
            docker-compose -f docker-compose-airflow.yml up -d
        }
        "airbyte" {
            Write-Host "🔄 Starting Airbyte services..." -ForegroundColor Green  
            docker-compose -f docker-compose-airbyte-fixed.yml up -d
        }
        "streamlit" {
            Write-Host "📊 Starting Streamlit app..." -ForegroundColor Green
            docker-compose up -d
        }
        default {
            Write-Host "❌ Unknown service: $serviceName" -ForegroundColor Red
            Write-Host "Available services: airflow, airbyte, streamlit, all" -ForegroundColor Yellow
        }
    }
}

function Show-Logs($serviceName) {
    switch ($serviceName) {
        "airflow" { docker-compose -f docker-compose-airflow.yml logs -f }
        "airbyte" { docker-compose -f docker-compose-airbyte-fixed.yml logs -f }
        "streamlit" { docker-compose logs -f }
        "all" { 
            Write-Host "📜 Showing logs for all services (Ctrl+C to exit)..." -ForegroundColor Cyan
            Start-Process powershell -ArgumentList "-Command docker-compose -f docker-compose-airflow.yml logs -f"
            Start-Process powershell -ArgumentList "-Command docker-compose -f docker-compose-airbyte-fixed.yml logs -f"
            docker-compose logs -f
        }
        default {
            Write-Host "❌ Unknown service for logs: $serviceName" -ForegroundColor Red
        }
    }
}

# Main execution logic
switch ($Action) {
    "start" {
        if ($Service -eq "all") {
            Start-AllServices
        } else {
            Start-ServiceByName $Service
        }
    }
    "stop" {
        if ($Service -eq "all") {
            Stop-AllServices  
        } else {
            Write-Host "🛑 Stopping $Service services..." -ForegroundColor Yellow
            switch ($Service) {
                "airflow" { docker-compose -f docker-compose-airflow.yml down }
                "airbyte" { docker-compose -f docker-compose-airbyte-fixed.yml down }
                "streamlit" { docker-compose down }
            }
        }
    }
    "status" {
        Show-ServiceStatus
    }
    "logs" {
        Show-Logs $Service
    }
    default {
        Write-Host "❌ Unknown action: $Action" -ForegroundColor Red
        Write-Host "`n📖 Usage Examples:" -ForegroundColor Cyan
        Write-Host "   .\manage_services.ps1 -Service all -Action start" -ForegroundColor White
        Write-Host "   .\manage_services.ps1 -Service airflow -Action start" -ForegroundColor White
        Write-Host "   .\manage_services.ps1 -Service airbyte -Action stop" -ForegroundColor White
        Write-Host "   .\manage_services.ps1 -Action status" -ForegroundColor White
        Write-Host "   .\manage_services.ps1 -Service all -Action logs" -ForegroundColor White
    }
}