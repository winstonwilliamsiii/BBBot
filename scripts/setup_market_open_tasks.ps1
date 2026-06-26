param(
    [ValidateSet("Create", "Delete", "List", "Test")]
    [string]$Action = "Create",
    [string]$TaskName = "Bentley-Market-Open-Bots",
    [string]$MorningTime = "09:20",
    [string]$IntradayTime = "12:15",
    [double]$LiquidityBuffer = 0.20,
    [double]$DryPowderDeployPct = 0.25,
    [double]$IntradayDryPowderDeployPct = 0.10,
    [double]$MinTradeCash = 50,
    [int]$MaxTrades = 1
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $repoRoot "run_market_open_bots.ps1"

if (-not (Test-Path $runner)) {
    Write-Error "Runner script not found: $runner"
    exit 1
}

$morningTaskName = "$TaskName-Morning"
$intradayTaskName = "$TaskName-Intraday"

$morningArgs = "-LiquidityBuffer $LiquidityBuffer -DryPowderDeployPct $DryPowderDeployPct -MinTradeCash $MinTradeCash -MaxTrades $MaxTrades"
$intradayArgs = "-LiquidityBuffer $LiquidityBuffer -DryPowderDeployPct $IntradayDryPowderDeployPct -MinTradeCash $MinTradeCash -MaxTrades $MaxTrades"

$morningCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$runner`" $morningArgs"
$intradayCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$runner`" $intradayArgs"

function New-MarketOpenTask {
    schtasks /create /tn $morningTaskName /tr $morningCommand /sc weekly /d MON,TUE,WED,THU,FRI /st $MorningTime /f | Out-Host
    schtasks /create /tn $intradayTaskName /tr $intradayCommand /sc weekly /d MON,TUE,WED,THU,FRI /st $IntradayTime /f | Out-Host
    Write-Host "Created/updated scheduled tasks:" -ForegroundColor Green
    Write-Host " - $morningTaskName @ $MorningTime" -ForegroundColor Green
    Write-Host " - $intradayTaskName @ $IntradayTime" -ForegroundColor Green
}

function Remove-MarketOpenTask {
    schtasks /delete /tn $morningTaskName /f | Out-Host
    schtasks /delete /tn $intradayTaskName /f | Out-Host
    Write-Host "Deleted scheduled tasks:" -ForegroundColor Yellow
    Write-Host " - $morningTaskName" -ForegroundColor Yellow
    Write-Host " - $intradayTaskName" -ForegroundColor Yellow
}

function Show-MarketOpenTask {
    Get-ScheduledTask -TaskName "$TaskName-*" -ErrorAction SilentlyContinue |
        Select-Object TaskName, State |
        Sort-Object TaskName |
        Format-Table -AutoSize

    foreach ($task in @($morningTaskName, $intradayTaskName)) {
        Get-ScheduledTaskInfo -TaskName $task -ErrorAction SilentlyContinue |
            Select-Object @{Name='TaskName';Expression={$task}}, LastRunTime, LastTaskResult, NextRunTime |
            Format-Table -AutoSize
    }
}

function Test-MarketOpenTask {
    schtasks /run /tn $morningTaskName | Out-Host
    schtasks /run /tn $intradayTaskName | Out-Host
    Start-Sleep -Seconds 8
    foreach ($task in @($morningTaskName, $intradayTaskName)) {
        Get-ScheduledTaskInfo -TaskName $task |
            Select-Object @{Name='TaskName';Expression={$task}}, LastRunTime, LastTaskResult, NextRunTime |
            Format-List
    }
}

switch ($Action) {
    "Create" { New-MarketOpenTask }
    "Delete" { Remove-MarketOpenTask }
    "List" { Show-MarketOpenTask }
    "Test" { Test-MarketOpenTask }
}
