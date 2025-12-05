# Restart Streamlit with Cache Clear
# Run this script after making styling changes

Write-Host "`n🔄 Restarting Streamlit with Fresh Cache..." -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# Step 1: Stop existing Streamlit processes
Write-Host "`n1️⃣  Stopping existing Python/Streamlit processes..." -ForegroundColor Yellow
Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "   ✅ Processes stopped" -ForegroundColor Green

# Step 2: Clear Streamlit cache
Write-Host "`n2️⃣  Clearing Streamlit cache..." -ForegroundColor Yellow
streamlit cache clear
Write-Host "   ✅ Cache cleared" -ForegroundColor Green

# Step 3: Wait a moment
Write-Host "`n⏳ Waiting 2 seconds..." -ForegroundColor DarkGray
Start-Sleep -Seconds 2

# Step 4: Start Streamlit
Write-Host "`n3️⃣  Starting Streamlit on port 8502..." -ForegroundColor Yellow
Write-Host "`n   🌐 Opening http://localhost:8502" -ForegroundColor Cyan
Write-Host "   📝 Press Ctrl+C to stop Streamlit" -ForegroundColor DarkGray
Write-Host "`n" + "=" * 60 -ForegroundColor Gray

streamlit run streamlit_app.py --server.port 8502
