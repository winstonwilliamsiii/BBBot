#!/usr/bin/env pwsh
# Repository Organization - Migration Helper
# This script helps update references to old file paths in your code

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Repository Organization - Migration Helper" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"

# Path mappings
$pathMappings = @{
    # Documentation
    "AIRFLOW_CREDENTIALS_GUIDE.md" = "docs/guides/AIRFLOW_CREDENTIALS_GUIDE.md"
    "AIRBYTE_CLOUD_SETUP.md" = "docs/guides/AIRBYTE_CLOUD_SETUP.md"
    "DOCKER_SERVICES_GUIDE.md" = "docs/guides/DOCKER_SERVICES_GUIDE.md"
    "SECURITY.md" = "docs/guides/SECURITY.md"
    "DEPLOYMENT.md" = "docs/guides/DEPLOYMENT.md"
    
    # Docker files
    "docker-compose-airflow.yml" = "docker/docker-compose-airflow.yml"
    "docker-compose.yml" = "docker/docker-compose.yml"
    "Dockerfile" = "docker/Dockerfile"
    "Dockerfile.airflow" = "docker/Dockerfile.airflow"
    
    # Airflow
    "./dags/" = "airflow/dags/"
    "./airflow_config/" = "airflow/config/"
    
    # Airbyte
    "airbyte-source-stocktwits" = "airbyte/sources/stocktwits"
    
    # Scripts
    "setup_airflow_credentials.ps1" = "scripts/setup/setup_airflow_credentials.ps1"
    "manage_services.ps1" = "scripts/management/manage_services.ps1"
    "setup_stocktwits_pipeline.ps1" = "scripts/setup/setup_stocktwits_pipeline.ps1"
}

Write-Host "📋 Path Mapping Reference:`n" -ForegroundColor Yellow

foreach ($old in $pathMappings.Keys | Sort-Object) {
    $new = $pathMappings[$old]
    Write-Host "  $old" -ForegroundColor Gray
    Write-Host "    → $new`n" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ Repository Organized Successfully!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "📁 New Structure:" -ForegroundColor White
Write-Host "  ├── docs/          # All documentation" -ForegroundColor Gray
Write-Host "  ├── docker/        # Docker configs" -ForegroundColor Gray
Write-Host "  ├── airflow/       # Airflow DAGs & config" -ForegroundColor Gray
Write-Host "  ├── airbyte/       # Custom sources" -ForegroundColor Gray
Write-Host "  ├── scripts/       # Setup & management" -ForegroundColor Gray
Write-Host "  ├── frontend/      # UI components" -ForegroundColor Gray
Write-Host "  └── api/           # Vercel serverless`n" -ForegroundColor Gray

Write-Host "📖 Documentation:" -ForegroundColor White
Write-Host "  • Full structure: docs/REPOSITORY_STRUCTURE.md" -ForegroundColor Cyan
Write-Host "  • Updated README: README.md`n" -ForegroundColor Cyan

Write-Host "🚀 Next Steps:" -ForegroundColor White
Write-Host "  1. Review new structure: " -ForegroundColor Gray
Write-Host "     cat docs/REPOSITORY_STRUCTURE.md`n" -ForegroundColor White
Write-Host "  2. Run services from docker/ folder:" -ForegroundColor Gray
Write-Host "     cd docker" -ForegroundColor White
Write-Host "     docker-compose -f docker-compose-airflow.yml up -d`n" -ForegroundColor White
Write-Host "  3. Update any custom scripts with new paths" -ForegroundColor Gray
Write-Host "     (Use the mapping above as reference)`n" -ForegroundColor White

Write-Host "⚠️  Important Notes:" -ForegroundColor Yellow
Write-Host "  • All docker-compose commands now run from docker/ folder" -ForegroundColor Gray
Write-Host "  • Volume paths updated to use ../ for parent directory" -ForegroundColor Gray
Write-Host "  • DAGs and Airbyte sources automatically mounted" -ForegroundColor Gray
Write-Host "  • Old folders (dags, airflow_config) have been moved`n" -ForegroundColor Gray

Write-Host "✨ Repository is now organized and ready to use!" -ForegroundColor Green
Write-Host ""
