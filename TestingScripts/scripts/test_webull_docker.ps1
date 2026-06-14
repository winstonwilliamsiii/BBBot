# Quick Test Webull Integration with Docker (Python 3.11)
# This bypasses your Python 3.12 environment

Write-Host "Testing Webull Integration in Docker (Python 3.11)..." -ForegroundColor Cyan
Write-Host ""

# Run test in Docker container with Python 3.11
docker run -it --rm `
    -v "${PWD}:/app" `
    -w /app `
    --env-file .env `
    python:3.11-slim `
    bash -c @"
echo 'Installing Webull SDK...'
pip install -q webull-openapi-python-sdk requests python-dotenv
echo ''
echo 'Running connection test...'
python test_webull_connection.py
"@

Write-Host ""
Write-Host "Test complete!" -ForegroundColor Green
