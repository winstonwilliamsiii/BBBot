# Setup Python 3.11 Environment for Webull Integration
# This script helps you install Python 3.11 and create a compatible environment

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Webull Integration - Python 3.11 Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check current Python version
Write-Host "Current Python version:" -ForegroundColor Yellow
python --version
Write-Host ""

Write-Host "ISSUE: Webull OpenAPI SDK requires Python 3.8-3.11" -ForegroundColor Red
Write-Host "Your current Python 3.12 is incompatible." -ForegroundColor Red
Write-Host ""

Write-Host "SOLUTIONS:" -ForegroundColor Green
Write-Host ""

Write-Host "Option 1: Install Python 3.11 from python.org" -ForegroundColor Yellow
Write-Host "-------------------------------------------" -ForegroundColor Yellow
Write-Host "1. Download Python 3.11 from: https://www.python.org/downloads/release/python-3119/"
Write-Host "2. Install it (make sure to check 'Add to PATH')"
Write-Host "3. Create new virtual environment:"
Write-Host "   py -3.11 -m venv .venv-webull"
Write-Host "   .\.venv-webull\Scripts\Activate.ps1"
Write-Host "   pip install -r requirements.txt"
Write-Host "   pip install webull-openapi-python-sdk"
Write-Host ""

Write-Host "Option 2: Use Windows Store Python 3.11" -ForegroundColor Yellow
Write-Host "-------------------------------------------" -ForegroundColor Yellow
Write-Host "1. Open Microsoft Store"
Write-Host "2. Search for 'Python 3.11'"
Write-Host "3. Install Python 3.11"
Write-Host "4. Run the commands from Option 1, step 3"
Write-Host ""

Write-Host "Option 3: Install Anaconda/Miniconda" -ForegroundColor Yellow
Write-Host "-------------------------------------------" -ForegroundColor Yellow
Write-Host "1. Download from: https://docs.anaconda.com/miniconda/"
Write-Host "2. Install Miniconda"
Write-Host "3. Create environment:"
Write-Host "   conda create -n bentley-webull python=3.11"
Write-Host "   conda activate bentley-webull"
Write-Host "   pip install -r requirements.txt"
Write-Host "   pip install webull-openapi-python-sdk"
Write-Host ""

Write-Host "Option 4: Use Docker (Quickest)" -ForegroundColor Yellow
Write-Host "-------------------------------------------" -ForegroundColor Yellow
Write-Host "1. Make sure Docker Desktop is installed and running"
Write-Host "2. Run:"
Write-Host "   docker run -it --rm -v ${PWD}:/app -w /app python:3.11 bash"
Write-Host "3. Inside container:"
Write-Host "   pip install webull-openapi-python-sdk"
Write-Host "   python test_webull_connection.py"
Write-Host ""

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Recommendation: Option 4 (Docker) is fastest for testing" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is available
Write-Host "Checking for Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker is installed: $dockerVersion" -ForegroundColor Green
        Write-Host ""
        Write-Host "QUICK START with Docker:" -ForegroundColor Cyan
        Write-Host "Run this command to test Webull integration:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "docker run -it --rm -v `"${PWD}:/app`" -w /app --env-file .env python:3.11-slim bash -c 'pip install webull-openapi-python-sdk && python test_webull_connection.py'" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "❌ Docker not found. Install from: https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Docker not found. Install from: https://www.docker.com/products/docker-desktop" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
