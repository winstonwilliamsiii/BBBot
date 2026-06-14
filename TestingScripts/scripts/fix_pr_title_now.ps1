# Quick fix for PR title - uses GitHub API
$prNumber = 35
$newTitle = "feat(trading-bot): add production-ready technical indicator trading bot"
$repo = "winstonwilliamsiii/BBBot"

Write-Host "🔧 Updating PR #$prNumber title..." -ForegroundColor Cyan
Write-Host "New title: $newTitle" -ForegroundColor Yellow
Write-Host ""

# Try to get GitHub token from git credential store
$gitCredential = "url=https://github.com" | git credential fill 2>$null
if ($gitCredential -match "password=(.+)") {
    $token = $matches[1]
    Write-Host "✓ Found GitHub credentials" -ForegroundColor Green
    
    # Make API call to update PR title
    $headers = @{
        "Authorization" = "Bearer $token"
        "Accept" = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
    }
    
    $body = @{
        title = $newTitle
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/pulls/$prNumber" `
            -Method Patch `
            -Headers $headers `
            -Body $body `
            -ContentType "application/json"
        
        Write-Host ""
        Write-Host "✅ SUCCESS! PR title updated to:" -ForegroundColor Green
        Write-Host "   $($response.title)" -ForegroundColor White
        Write-Host ""
        Write-Host "🔄 GitHub Actions will now re-run validation..." -ForegroundColor Cyan
        exit 0
    }
    catch {
        Write-Host "❌ API call failed: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "📋 Manual update required:" -ForegroundColor Yellow
        Write-Host "Title (copied to clipboard): $newTitle" -ForegroundColor White
        $newTitle | Set-Clipboard
        Start-Process "https://github.com/$repo/pull/$prNumber"
        exit 1
    }
}
else {
    Write-Host "⚠️  No GitHub credentials found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📋 Title copied to clipboard!" -ForegroundColor Green
    Write-Host "Opening PR page for manual update..." -ForegroundColor Cyan
    $newTitle | Set-Clipboard
    Start-Sleep -Seconds 2
    Start-Process "https://github.com/$repo/pull/$prNumber"
    Write-Host ""
    Write-Host "Please paste the title and click Save" -ForegroundColor Yellow
    exit 1
}
