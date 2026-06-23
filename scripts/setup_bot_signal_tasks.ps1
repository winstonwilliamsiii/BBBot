param(
    [ValidateSet("Create", "Delete", "List", "Test")]
    [string]$Action = "Create",
    [string]$TaskName = "Bentley-All-Bot-Signals",
    [string]$MorningTime = "09:00",
    [string]$MiddayTime = "12:00",
    [string]$CloseTime = "15:00",
    [ValidateSet("paper", "live")]
    [string]$Mode = "paper",
    [string]$Symbol = "SPY",
    [switch]$ActiveOnly
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $repoRoot "run_bot_signal_broadcast.ps1"

if (-not (Test-Path $runner)) {
    Write-Error "Runner script not found: $runner"
    exit 1
}

$morningTaskName = "$TaskName-Morning"
$middayTaskName = "$TaskName-Midday"
$closeTaskName = "$TaskName-Close"

$activeOnlyArg = if ($ActiveOnly.IsPresent) { "-ActiveOnly" } else { "" }
$taskCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$runner`" -Mode $Mode -Symbol $Symbol $activeOnlyArg"

function New-BotSignalTasks {
    schtasks /create /tn $morningTaskName /tr $taskCommand /sc weekly /d MON,TUE,WED,THU,FRI /st $MorningTime /f | Out-Host
    schtasks /create /tn $middayTaskName /tr $taskCommand /sc weekly /d MON,TUE,WED,THU,FRI /st $MiddayTime /f | Out-Host
    schtasks /create /tn $closeTaskName /tr $taskCommand /sc weekly /d MON,TUE,WED,THU,FRI /st $CloseTime /f | Out-Host
    Write-Host "Created/updated scheduled tasks:" -ForegroundColor Green
    Write-Host " - $morningTaskName @ $MorningTime" -ForegroundColor Green
    Write-Host " - $middayTaskName @ $MiddayTime" -ForegroundColor Green
    Write-Host " - $closeTaskName @ $CloseTime" -ForegroundColor Green
}

function Remove-BotSignalTasks {
    schtasks /delete /tn $morningTaskName /f | Out-Host
    schtasks /delete /tn $middayTaskName /f | Out-Host
    schtasks /delete /tn $closeTaskName /f | Out-Host
    Write-Host "Deleted scheduled tasks:" -ForegroundColor Yellow
    Write-Host " - $morningTaskName" -ForegroundColor Yellow
    Write-Host " - $middayTaskName" -ForegroundColor Yellow
    Write-Host " - $closeTaskName" -ForegroundColor Yellow
}

function Show-BotSignalTasks {
    Get-ScheduledTask -TaskName "$TaskName-*" -ErrorAction SilentlyContinue |
        Select-Object TaskName, State |
        Sort-Object TaskName |
        Format-Table -AutoSize

    foreach ($task in @($morningTaskName, $middayTaskName, $closeTaskName)) {
        Get-ScheduledTaskInfo -TaskName $task -ErrorAction SilentlyContinue |
            Select-Object @{Name='TaskName';Expression={$task}}, LastRunTime, LastTaskResult, NextRunTime |
            Format-Table -AutoSize
    }
}

function Test-BotSignalTasks {
    schtasks /run /tn $morningTaskName | Out-Host
    schtasks /run /tn $middayTaskName | Out-Host
    schtasks /run /tn $closeTaskName | Out-Host
}

switch ($Action) {
    "Create" { New-BotSignalTasks }
    "Delete" { Remove-BotSignalTasks }
    "List" { Show-BotSignalTasks }
    "Test" { Test-BotSignalTasks }
}
