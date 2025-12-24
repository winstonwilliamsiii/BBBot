# Configure Windows Firewall for Airbyte Cloud IP Whitelist
# Run this script as Administrator to allow Airbyte Cloud IPs to access MySQL on port 3307

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Airbyte MySQL IP Whitelist Configuration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Airbyte Cloud IP addresses
$airbyteIPs = @{
    # US Region
    "Airbyte-MySQL-US-1" = "34.106.109.131"
    "Airbyte-MySQL-US-2" = "34.106.196.165"
    "Airbyte-MySQL-US-3" = "34.106.60.246"
    "Airbyte-MySQL-US-4" = "34.106.229.69"
    "Airbyte-MySQL-US-5" = "34.106.127.139"
    "Airbyte-MySQL-US-6" = "34.106.218.58"
    "Airbyte-MySQL-US-7" = "34.106.115.240"
    "Airbyte-MySQL-US-8" = "34.106.225.141"
    
    # EU Region
    "Airbyte-MySQL-EU-1" = "13.37.4.46"
    "Airbyte-MySQL-EU-2" = "13.37.142.60"
    "Airbyte-MySQL-EU-3" = "35.181.124.238"
    
    # CIDR Range
    "Airbyte-MySQL-CIDR" = "34.33.7.0/29"
}

$port = 3307
$protocol = "TCP"
$successCount = 0
$failureCount = 0

Write-Host "Creating firewall rules for MySQL port $port..." -ForegroundColor Yellow
Write-Host ""

foreach ($ruleName in $airbyteIPs.Keys) {
    $ipAddress = $airbyteIPs[$ruleName]
    
    try {
        # Check if rule already exists
        $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        
        if ($existingRule) {
            Write-Host "⚠ Rule '$ruleName' already exists. Removing old rule..." -ForegroundColor Yellow
            Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction Stop
        }
        
        # Create new firewall rule
        New-NetFirewallRule `
            -DisplayName $ruleName `
            -Description "Allow Airbyte Cloud ($ipAddress) to access MySQL database" `
            -Direction Inbound `
            -RemoteAddress $ipAddress `
            -Protocol $protocol `
            -LocalPort $port `
            -Action Allow `
            -Profile Any `
            -Enabled True `
            -ErrorAction Stop | Out-Null
        
        Write-Host "✓ Created rule: $ruleName ($ipAddress)" -ForegroundColor Green
        $successCount++
        
    } catch {
        Write-Host "✗ Failed to create rule: $ruleName ($ipAddress)" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        $failureCount++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Successfully created: $successCount rules" -ForegroundColor Green
Write-Host "Failed: $failureCount rules" -ForegroundColor $(if ($failureCount -gt 0) { "Red" } else { "Green" })
Write-Host ""

# Display created rules
Write-Host "Verifying created rules..." -ForegroundColor Yellow
Write-Host ""

$createdRules = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "Airbyte-MySQL-*" }

if ($createdRules) {
    Write-Host "Active Airbyte MySQL firewall rules:" -ForegroundColor Cyan
    $createdRules | Select-Object DisplayName, Enabled, Direction, Action | Format-Table -AutoSize
} else {
    Write-Host "No Airbyte MySQL rules found!" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Restart MySQL container: docker-compose -f docker-compose-airflow.yml restart mysql" -ForegroundColor Yellow
Write-Host "2. Verify MySQL is listening on 0.0.0.0:3307" -ForegroundColor Yellow
Write-Host "3. Test connection from Airbyte Cloud using:" -ForegroundColor Yellow
Write-Host "   - Host: <your-public-ip>" -ForegroundColor Cyan
Write-Host "   - Port: 3307" -ForegroundColor Cyan
Write-Host "   - Database: mansa_bot" -ForegroundColor Cyan
Write-Host "   - Username: airbyte" -ForegroundColor Cyan
Write-Host "   - Password: airbyte_secure_password_2025" -ForegroundColor Cyan
Write-Host ""
Write-Host "To remove all rules, run:" -ForegroundColor Yellow
Write-Host "Get-NetFirewallRule | Where-Object { `$_.DisplayName -like 'Airbyte-MySQL-*' } | Remove-NetFirewallRule" -ForegroundColor Cyan
Write-Host ""
