param(
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

Write-Host "Windows loopback preference helper (IPv4 over IPv6 for localhost)" -ForegroundColor Cyan
Write-Host ""

Write-Host "Current IPv6 prefix policies:" -ForegroundColor Yellow
netsh interface ipv6 show prefixpolicies
Write-Host ""

$commands = @(
    'netsh interface ipv6 set prefixpolicy ::ffff:0:0/96 60 4',
    'netsh interface ipv6 set prefixpolicy ::1/128 40 0'
)

if (-not $Apply) {
    Write-Host "Dry run only. No system settings were changed." -ForegroundColor Green
    Write-Host ""
    Write-Host "To apply changes, run PowerShell as Administrator:" -ForegroundColor Yellow
    Write-Host "  .\\scripts\\set_windows_ipv4_loopback_preference.ps1 -Apply" -ForegroundColor White
    Write-Host ""
    Write-Host "Commands that would run:" -ForegroundColor Yellow
    $commands | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
    exit 0
}

if (-not (Test-IsAdministrator)) {
    Write-Error "Administrator privileges are required. Re-run PowerShell as Administrator with -Apply."
}

Write-Host "Applying IPv4 preference for localhost resolution..." -ForegroundColor Yellow
foreach ($cmd in $commands) {
    Write-Host "Executing: $cmd" -ForegroundColor White
    Invoke-Expression $cmd
}

Write-Host "" 
Write-Host "Updated IPv6 prefix policies:" -ForegroundColor Yellow
netsh interface ipv6 show prefixpolicies
Write-Host ""
Write-Host "Completed. New connections should prefer IPv4 loopback for localhost." -ForegroundColor Green
