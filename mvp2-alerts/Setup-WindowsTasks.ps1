# Windows Task Scheduler Setup for TradingView Alerts
# Run as Administrator in PowerShell

param(
    [ValidateSet("Create", "Delete", "List", "Test")]
    [string]$Action = "Create"
)

# Configuration
$NODE_EXE = "C:\Program Files\nodejs\node.exe"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$ALERT_SCRIPT = Join-Path $SCRIPT_DIR "index.js"
$TASK_FOLDER = "BentleyBot"

# Schedule times (hour, minute)
$schedules = @(
    @{ name = "7AM"; hour = 7; minute = 0 },
    @{ name = "9:40AM"; hour = 9; minute = 40 },
    @{ name = "11:30AM"; hour = 11; minute = 30 },
    @{ name = "3PM"; hour = 15; minute = 0 }
)

function Test-Admin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Create-Tasks {
    Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  TradingView Alerts - Windows Task Scheduler  ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    # Validate prerequisites
    if (-not (Test-Path $NODE_EXE)) {
        Write-Host "❌ ERROR: Node.js not found at $NODE_EXE" -ForegroundColor Red
        Write-Host "   Please install Node.js from https://nodejs.org" -ForegroundColor Yellow
        exit 1
    }

    if (-not (Test-Path $ALERT_SCRIPT)) {
        Write-Host "❌ ERROR: Alert script not found at $ALERT_SCRIPT" -ForegroundColor Red
        exit 1
    }

    Write-Host "✓ Node.js: $NODE_EXE" -ForegroundColor Green
    Write-Host "✓ Alert script: $ALERT_SCRIPT" -ForegroundColor Green
    Write-Host ""

    # Create folder in Task Scheduler
    Write-Host "Creating task folder: $TASK_FOLDER" -ForegroundColor Yellow
    New-Item -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\Tree\$TASK_FOLDER" -Force -ErrorAction SilentlyContinue | Out-Null

    # Create each task
    $count = 0
    foreach ($schedule in $schedules) {
        $count++
        $taskName = "TradingView-Alerts-$($schedule.name)"
        $fullTaskName = "\$TASK_FOLDER\$taskName"
        $timeStr = "{0:D2}:{1:D2}" -f $schedule.hour, $schedule.minute

        Write-Host "[$count/4] Creating: $taskName @ $timeStr" -ForegroundColor Yellow

        # Build trigger
        $trigger = New-ScheduledTaskTrigger `
            -Daily `
            -At ([datetime]"$($schedule.hour):$($schedule.minute)") `
            -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday

        # Build action
        $action = New-ScheduledTaskAction `
            -Execute $NODE_EXE `
            -Argument "`"$ALERT_SCRIPT`"" `
            -WorkingDirectory $SCRIPT_DIR

        # Build settings
        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -RunOnlyIfNetworkAvailable

        # Build principal (run as current user)
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

        # Register task
        try {
            Register-ScheduledTask `
                -TaskName $taskName `
                -TaskPath "\$TASK_FOLDER\" `
                -Trigger $trigger `
                -Action $action `
                -Settings $settings `
                -Principal $principal `
                -Force | Out-Null

            Write-Host "  ✓ Created successfully" -ForegroundColor Green
        }
        catch {
            Write-Host "  ✗ Failed: $_" -ForegroundColor Red
        }
    }

    Write-Host ""
    Write-Host "════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "✓ Setup Complete!" -ForegroundColor Green
    Write-Host "════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📅 Scheduled for weekdays (Mon-Fri):" -ForegroundColor Cyan
    $schedules | ForEach-Object {
        Write-Host "   • $("{0:D2}:{1:D2}" -f $_.hour, $_.minute) - TradingView-Alerts-$($_.name)" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "To verify tasks:" -ForegroundColor Yellow
    Write-Host "  1. Open: taskschd.msc" -ForegroundColor White
    Write-Host "  2. Expand: Task Scheduler Library > BentleyBot" -ForegroundColor White
    Write-Host "  3. View: All 4 TradingView-Alerts-* tasks" -ForegroundColor White
    Write-Host ""
}

function Delete-Tasks {
    Write-Host "Deleting TradingView tasks..." -ForegroundColor Yellow
    foreach ($schedule in $schedules) {
        $taskName = "TradingView-Alerts-$($schedule.name)"
        try {
            Unregister-ScheduledTask -TaskName $taskName -TaskPath "\$TASK_FOLDER\" -Confirm:$false -ErrorAction SilentlyContinue
            Write-Host "  ✓ Deleted: $taskName" -ForegroundColor Green
        }
        catch {
            Write-Host "  ✗ Failed to delete: $taskName" -ForegroundColor Red
        }
    }
}

function List-Tasks {
    Write-Host "TradingView Scheduled Tasks:" -ForegroundColor Cyan
    Write-Host ""
    foreach ($schedule in $schedules) {
        $taskName = "TradingView-Alerts-$($schedule.name)"
        $task = Get-ScheduledTask -TaskName $taskName -TaskPath "\$TASK_FOLDER\" -ErrorAction SilentlyContinue
        if ($task) {
            $info = Get-ScheduledTaskInfo -Task $task
            Write-Host "  $taskName" -ForegroundColor Green
            Write-Host "    State: $($task.State)" -ForegroundColor Gray
            Write-Host "    Last Run: $($info.LastRunTime)" -ForegroundColor Gray
            Write-Host "    Last Result: $($info.LastTaskResult)" -ForegroundColor Gray
            Write-Host ""
        }
    }
}

function Test-Task {
    Write-Host "Testing first task execution..." -ForegroundColor Yellow
    $taskName = "TradingView-Alerts-7AM"
    $task = Get-ScheduledTask -TaskName $taskName -TaskPath "\$TASK_FOLDER\" -ErrorAction SilentlyContinue
    if ($task) {
        Start-ScheduledTask -InputObject $task
        Write-Host "✓ Task triggered, check Discord for alert in 30 seconds..." -ForegroundColor Green
    }
    else {
        Write-Host "✗ Task not found" -ForegroundColor Red
    }
}

# Main
if (-not (Test-Admin)) {
    Write-Host "❌ ERROR: This script requires Administrator privileges" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator" -ForegroundColor Yellow
    exit 1
}

switch ($Action.ToLower()) {
    "create" { Create-Tasks }
    "delete" { Delete-Tasks }
    "list" { List-Tasks }
    "test" { Test-Task }
    default { Create-Tasks }
}
