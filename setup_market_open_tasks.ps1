param(
    [ValidateSet("Create", "Delete", "List", "Test")]
    [string]$Action = "Create",
    [string]$TaskName = "Bentley-Market-Open-Bots",
    [string]$Time = "09:20",
    [double]$LiquidityBuffer = 0.20,
    [double]$DryPowderDeployPct = 0.25,
    [double]$MinTradeCash = 50,
    [int]$MaxTrades = 1
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $repoRoot "run_market_open_bots.ps1"

if (-not (Test-Path $runner)) {
    Write-Error "Runner script not found: $runner"
    exit 1
}

$runnerArgs = "-LiquidityBuffer $LiquidityBuffer -DryPowderDeployPct $DryPowderDeployPct -MinTradeCash $MinTradeCash -MaxTrades $MaxTrades"
$taskCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$runner`" $runnerArgs"

function New-MarketOpenTask {
    schtasks /create /tn $TaskName /tr $taskCommand /sc weekly /d MON,TUE,WED,THU,FRI /st $Time /f | Out-Host
    Write-Host "Created/updated scheduled task: $TaskName at $Time (weekdays)." -ForegroundColor Green
}

function Remove-MarketOpenTask {
    schtasks /delete /tn $TaskName /f | Out-Host
    Write-Host "Deleted scheduled task: $TaskName" -ForegroundColor Yellow
}

function Show-MarketOpenTask {
    Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue |
        Select-Object TaskName, State |
        Format-Table -AutoSize

    Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue |
        Select-Object LastRunTime, LastTaskResult, NextRunTime |
        Format-Table -AutoSize
}

function Test-MarketOpenTask {
    schtasks /run /tn $TaskName | Out-Host
    Start-Sleep -Seconds 8
    Get-ScheduledTaskInfo -TaskName $TaskName |
        Select-Object LastRunTime, LastTaskResult, NextRunTime |
        Format-List
}

switch ($Action) {
    "Create" { New-MarketOpenTask }
    "Delete" { Remove-MarketOpenTask }
    "List" { Show-MarketOpenTask }
    "Test" { Test-MarketOpenTask }
}
