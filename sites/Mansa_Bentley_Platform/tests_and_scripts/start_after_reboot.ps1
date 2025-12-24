# When You Return - Start Here
# Run this script after rebooting your laptop

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  BBBot Fresh Start After Reboot" -ForegroundColor Cyan  
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  1. Run complete diagnostics" -ForegroundColor White
Write-Host "  2. Identify any remaining issues" -ForegroundColor White
Write-Host "  3. Start Streamlit with clean state" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to begin diagnostics..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "Running full diagnostic..." -ForegroundColor Yellow
Write-Host ""

python full_diagnostic.py | Tee-Object -FilePath "diagnostic_output.txt"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Diagnostic complete! Output saved to:" -ForegroundColor Green
Write-Host "diagnostic_output.txt" -ForegroundColor White
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Would you like to start Streamlit now? (Y/N)"
$response = Read-Host

if ($response -eq 'Y' -or $response -eq 'y') {
    Write-Host ""
    Write-Host "Starting Streamlit..." -ForegroundColor Green
    Write-Host ""
    Write-Host "LOGIN CREDENTIALS:" -ForegroundColor Cyan
    Write-Host "  Username: admin" -ForegroundColor White
    Write-Host "  Password: admin123" -ForegroundColor White
    Write-Host ""
    
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:8501"
    
    streamlit run streamlit_app.py
} else {
    Write-Host ""
    Write-Host "Review diagnostic_output.txt and share with support" -ForegroundColor Yellow
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
