param(
    [ValidateSet("Create", "Delete", "List", "Test")]
    [string]$Action = "Create",
    [string]$TaskName = "Bentley-Vega",
    [string]$MorningTime = "09:30",
    [int]$MaxTrades = 1,
    [ValidateSet("buy", "sell")]
    [string]$Side = "buy",
    [ValidateSet("AUTO", "paper", "live")]
    [string]$TradingMode = "AUTO"
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $repoRoot "run_vega.ps1"

if (-not (Test-Path $runner)) {
    Write-Error "Runner script not found: $runner"
    exit 1
}

$taskCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$runner`" -MaxTrades $MaxTrades -Side $Side -TradingMode $TradingMode"

function New-VegaTask {
    schtasks /create /tn $TaskName /tr $taskCommand /sc weekly /d MON,TUE,WED,THU,FRI /st $MorningTime /f | Out-Host
    Write-Host "Created/updated Vega task: $TaskName @ $MorningTime" -ForegroundColor Green
}

function Remove-VegaTask {
    schtasks /delete /tn $TaskName /f | Out-Host
    Write-Host "Deleted Vega task: $TaskName" -ForegroundColor Yellow
}

function Show-VegaTask {
    schtasks /query /tn $TaskName /fo LIST /v | Out-Host
}

function Test-VegaTask {
    schtasks /run /tn $TaskName | Out-Host
    Start-Sleep -Seconds 8
    schtasks /query /tn $TaskName /fo LIST /v | Out-Host
}

switch ($Action) {
    "Create" { New-VegaTask }
    "Delete" { Remove-VegaTask }
    "List" { Show-VegaTask }
    "Test" { Test-VegaTask }
}