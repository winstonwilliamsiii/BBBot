# Create tar.gz for get_transactions_streamlit

Set-Location "c:\Users\winst\BentleyBudgetBot\appwrite-functions\get_transactions_streamlit"

Write-Host "Creating tar.gz with proper structure..." -ForegroundColor Cyan

# Create tar.gz from current directory (includes all subdirectories)
tar -czf "..\..\get_transactions_streamlit.tar.gz" `
    index.js `
    package.json `
    _shared/appwriteClient.js

Set-Location "..\.."

Write-Host "`n✅ Created: c:\Users\winst\BentleyBudgetBot\get_transactions_streamlit.tar.gz" -ForegroundColor Green

Write-Host "`nVerifying contents:" -ForegroundColor Yellow
tar -tzf get_transactions_streamlit.tar.gz

Write-Host "`n🚀 Ready to upload!" -ForegroundColor Green
