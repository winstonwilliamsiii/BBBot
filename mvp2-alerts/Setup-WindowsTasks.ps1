param(
    [ValidateSet("Create", "Delete", "List", "Test")]
    [string]$Action = "Create"
)

$runner = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "run_alert_once.ps1"

$schedules = @(
    @{ Name = "TradingView-Alerts-7AM"; Time = "07:00" },
    @{ Name = "TradingView-Alerts-9_40AM"; Time = "09:40" },
    @{ Name = "TradingView-Alerts-11_30AM"; Time = "11:30" },
    @{ Name = "TradingView-Alerts-3PM"; Time = "15:00" }
)

function New-AlertTasks {
    if (-not (Test-Path $runner)) {
        Write-Error "Runner script not found: $runner"
        exit 1
    }

    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runner`""

    $settings = New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
        -MultipleInstances IgnoreNew

    foreach ($schedule in $schedules) {
        $trigger = New-ScheduledTaskTrigger -Weekly `
            -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
            -At $schedule.Time

        Register-ScheduledTask `
            -TaskName $schedule.Name `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Force | Out-Null

        Write-Host "  [OK] $($schedule.Name) @ $($schedule.Time) (StartWhenAvailable=true)" -ForegroundColor Cyan
    }

    Write-Host "Created/updated alert tasks successfully." -ForegroundColor Green
}

function Remove-AlertTasks {
    foreach ($schedule in $schedules) {
        schtasks /delete /tn $schedule.Name /f | Out-Host
    }
    Write-Host "Deleted alert tasks." -ForegroundColor Yellow
}

function Show-AlertTasks {
    Get-ScheduledTask -TaskName "TradingView-Alerts-*" -ErrorAction SilentlyContinue |
        Select-Object TaskName, State |
        Sort-Object TaskName |
        Format-Table -AutoSize
}

function Test-AlertTask {
    Start-ScheduledTask -TaskName "TradingView-Alerts-7AM"
    Start-Sleep -Seconds 6
    Get-ScheduledTaskInfo -TaskName "TradingView-Alerts-7AM" |
        Select-Object LastRunTime, LastTaskResult, NextRunTime |
        Format-List
}

switch ($Action) {
    "Create" { New-AlertTasks }
    "Delete" { Remove-AlertTasks }
    "List" { Show-AlertTasks }
    "Test" { Test-AlertTask }
}