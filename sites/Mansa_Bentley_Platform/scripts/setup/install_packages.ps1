# Package Installation Script for Bentley Budget Bot
# Run this to set up the complete development environment

Write-Host "🤖 Bentley Budget Bot - Package Installation" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Virtual environment not detected!" -ForegroundColor Yellow
    Write-Host "Recommended: Activate your virtual environment first" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        Write-Host "Exiting. Please activate your venv and try again." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "📦 Installation Options:" -ForegroundColor Green
Write-Host "  1. Full Development Environment (All packages)" -ForegroundColor White
Write-Host "  2. Streamlit Dashboard Only" -ForegroundColor White
Write-Host "  3. MLFlow Pipeline Only" -ForegroundColor White
Write-Host "  4. Vercel API Only" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Select option (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Installing Full Development Environment..." -ForegroundColor Cyan
        pip install -r requirements.txt
    }
    "2" {
        Write-Host ""
        Write-Host "Installing Streamlit Dashboard..." -ForegroundColor Cyan
        pip install -r requirements-streamlit.txt
    }
    "3" {
        Write-Host ""
        Write-Host "Installing MLFlow Pipeline..." -ForegroundColor Cyan
        pip install -r bbbot1_pipeline/requirements.txt
    }
    "4" {
        Write-Host ""
        Write-Host "Installing Vercel API..." -ForegroundColor Cyan
        pip install -r api/requirements.txt
    }
    default {
        Write-Host "Invalid option. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "✅ Installation Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan

if ($choice -eq "1" -or $choice -eq "3") {
    Write-Host "  • Test MLFlow connection:" -ForegroundColor White
    Write-Host "    python -c `"from bbbot1_pipeline.mlflow_config import validate_connection; validate_connection()`"" -ForegroundColor Gray
}

if ($choice -eq "1" -or $choice -eq "2") {
    Write-Host "  • Start Streamlit dashboard:" -ForegroundColor White
    Write-Host "    streamlit run streamlit_app.py" -ForegroundColor Gray
}

Write-Host ""
Write-Host "📚 For more information, see docs/PACKAGE_ORGANIZATION.md" -ForegroundColor Cyan
