# ============================================
# START BENTLEY BOT IN PRODUCTION MODE
# ============================================
# This script ensures production credentials are loaded

Write-Host "🚀 Starting Bentley Bot (PRODUCTION MODE)" -ForegroundColor Cyan
Write-Host ""

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$resolver = Join-Path $repoRoot "scripts\resolve_python_for_service.ps1"
$pythonExe = & $resolver -Service streamlit -RepoRoot $repoRoot -AllowLegacyFallback

# Resolve virtual environment interpreter
Write-Host "📦 Resolving Python environment..." -ForegroundColor Yellow
Write-Host "   $pythonExe" -ForegroundColor Gray

# Set encoding for Unicode emoji support
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING='utf-8'

# Verify production environment will load
Write-Host ""
Write-Host "🔍 Verifying environment..." -ForegroundColor Yellow
if (Test-Path ".env.local") {
    Write-Host "   ✅ .env.local found (production credentials)" -ForegroundColor Green
} else {
    Write-Host "   ❌ .env.local NOT found - using fallback" -ForegroundColor Red
    Write-Host "   Create .env.local with production credentials" -ForegroundColor Red
}

Write-Host ""
Write-Host "🌐 Starting Streamlit on http://localhost:8501" -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Start Streamlit
& $pythonExe -m streamlit run streamlit_app.py --server.port=8501
