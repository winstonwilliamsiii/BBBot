# ============================================
# START BENTLEY BOT IN DEVELOPMENT MODE
# ============================================
# This script uses .env.development (localhost)

Write-Host "🛠️  Starting Bentley Bot (DEVELOPMENT MODE)" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Set encoding for Unicode emoji support
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING='utf-8'

# Force development environment (overrides .env.local)
$env:ENVIRONMENT='development'

Write-Host ""
Write-Host "🔍 Using DEVELOPMENT environment" -ForegroundColor Yellow
Write-Host "   Database: localhost:3306" -ForegroundColor Gray
Write-Host "   APIs: Development credentials" -ForegroundColor Gray

Write-Host ""
Write-Host "🌐 Starting Streamlit on http://localhost:8501" -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Start Streamlit
streamlit run streamlit_app.py --server.port=8501
