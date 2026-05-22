# MySQL Connection Diagnostic and Repair Script
# Fixes common MySQL connection issues for Bentley Budget Bot

$script:DockerMode = if ($env:BENTLEY_DOCKER_MODE) { $env:BENTLEY_DOCKER_MODE.ToLowerInvariant() } else { "auto" }
$script:WslDistro = if ($env:BENTLEY_WSL_DISTRO) { $env:BENTLEY_WSL_DISTRO } else { "Ubuntu" }
$script:UseWslDocker = $false

Write-Host "`nMySQL Connection Diagnostic and Repair Tool" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ForegroundColor Gray

function Test-WindowsDocker {
    try {
        $null = & docker version --format '{{.Server.Version}}' 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Test-WslDocker {
    try {
        $null = & wsl.exe -d $script:WslDistro -- docker version --format '{{.Server.Version}}' 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Initialize-DockerMode {
    if ($script:DockerMode -eq "wsl") {
        if (-not (Test-WslDocker)) {
            return $false
        }
        $script:UseWslDocker = $true
        return $true
    }

    if ($script:DockerMode -eq "desktop") {
        $script:UseWslDocker = $false
        return $true
    }

    if (Test-WindowsDocker) {
        $script:UseWslDocker = $false
        return $true
    }

    if (Test-WslDocker) {
        $script:UseWslDocker = $true
        return $true
    }

    return $false
}

function Invoke-Docker {
    param(
        [string[]]$Args,
        [switch]$SuppressErrors
    )

    if ($script:UseWslDocker) {
        if ($SuppressErrors) {
            & wsl.exe -d $script:WslDistro -- docker @Args 2>$null
        } else {
            & wsl.exe -d $script:WslDistro -- docker @Args
        }
        return
    }

    if ($SuppressErrors) {
        & docker @Args 2>$null
    } else {
        & docker @Args
    }
}

function Test-DockerRunning {
    Invoke-Docker -Args @("version", "--format", "{{.Server.Version}}") -SuppressErrors
    return ($LASTEXITCODE -eq 0)
}

function Invoke-Compose {
    param(
        [string[]]$Args
    )

    if ($script:UseWslDocker) {
        & wsl.exe -d $script:WslDistro -- docker compose @Args 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        & wsl.exe -d $script:WslDistro -- docker-compose @Args
        return ($LASTEXITCODE -eq 0)
    }

    & docker compose @Args 2>$null
    if ($LASTEXITCODE -eq 0) {
        return $true
    }

    & docker-compose @Args
    return ($LASTEXITCODE -eq 0)
}

if (-not (Initialize-DockerMode)) {
    Write-Host "Docker CLI is unavailable from both Windows and WSL2 modes." -ForegroundColor Red
    Write-Host "   Set BENTLEY_DOCKER_MODE=wsl once Docker Engine is running inside WSL." -ForegroundColor Yellow
    exit 1
}

if ($script:UseWslDocker) {
    Write-Host "Docker mode: WSL2 ($($script:WslDistro))" -ForegroundColor Cyan
} else {
    Write-Host "Docker mode: Docker Desktop/Windows" -ForegroundColor Cyan
}

# Step 1: Verify Docker is running
Write-Host "Step 1: Checking Docker status..." -ForegroundColor White
if (-not (Test-DockerRunning)) {
    Write-Host "Docker is not running. Running startup helper..." -ForegroundColor Red
    & "$PSScriptRoot\start_mysql_docker.ps1"
    Start-Sleep -Seconds 5
}
Write-Host "Docker is running." -ForegroundColor Green

# Step 2: Check MySQL container status
Write-Host "`nStep 2: Checking MySQL container status..." -ForegroundColor White
$container = Invoke-Docker -Args @("ps", "--filter", "name=bentley-mysql", "--format", "{{.Names}}") -SuppressErrors

if (-not $container) {
    Write-Host "MySQL container is not running. Starting..." -ForegroundColor Red
    Set-Location "$PSScriptRoot\docker"
    $composeOk = Invoke-Compose -Args @("-f", "docker-compose-airflow.yml", "up", "-d", "mysql")
    if (-not $composeOk) {
        Write-Host "Failed to start MySQL container via Docker Compose." -ForegroundColor Red
        Set-Location $PSScriptRoot
        exit 1
    }
    Start-Sleep -Seconds 5
    Set-Location $PSScriptRoot
} else {
    Write-Host "Container 'bentley-mysql' is running." -ForegroundColor Green
}

# Step 3: Test MySQL connectivity
Write-Host "`nStep 3: Testing MySQL connectivity..." -ForegroundColor White
$pingResult = Invoke-Docker -Args @("exec", "bentley-mysql", "mysqladmin", "ping", "-uroot", "-proot") 2>&1 | Select-String "mysqld is alive"

if ($pingResult) {
    Write-Host "MySQL is responding to connections." -ForegroundColor Green
} else {
    Write-Host "MySQL is not responding. Restarting container..." -ForegroundColor Red
    Invoke-Docker -Args @("restart", "bentley-mysql") | Out-Null
    Start-Sleep -Seconds 10
}

# Step 4: Check for stale connections
Write-Host "`nStep 4: Checking for stale connections..." -ForegroundColor White
$staleConnections = Invoke-Docker -Args @("exec", "bentley-mysql", "mysql", "-uroot", "-proot", "-e", "SELECT COUNT(*) as count FROM INFORMATION_SCHEMA.PROCESSLIST WHERE COMMAND = 'Sleep' AND TIME > 3600;") 2>&1 | Select-String -Pattern "^\d+$"

if ($staleConnections -and [int]$staleConnections.Line -gt 0) {
    Write-Host "Found $($staleConnections.Line) stale connection(s) (idle > 1 hour)" -ForegroundColor Yellow
    Write-Host "   Killing stale connections..." -ForegroundColor Cyan
    
    # Get list of stale connection IDs
    $staleIds = Invoke-Docker -Args @("exec", "bentley-mysql", "mysql", "-uroot", "-proot", "-N", "-e", "SELECT ID FROM INFORMATION_SCHEMA.PROCESSLIST WHERE COMMAND = 'Sleep' AND TIME > 3600;") 2>&1 | Where-Object { $_ -match '^\d+$' }
    
    foreach ($id in $staleIds) {
        Invoke-Docker -Args @("exec", "bentley-mysql", "mysql", "-uroot", "-proot", "-e", "KILL $id;") 2>&1 | Out-Null
    }
    Write-Host "Stale connections killed." -ForegroundColor Green
} else {
    Write-Host "No stale connections found." -ForegroundColor Green
}

# Step 5: Fix config file permissions
Write-Host "`nStep 5: Fixing config file permissions..." -ForegroundColor White
Invoke-Docker -Args @("exec", "bentley-mysql", "chmod", "644", "/etc/mysql/conf.d/custom.cnf") 2>&1 | Out-Null
Write-Host "Config file permissions fixed." -ForegroundColor Green

# Step 6: Verify all databases are accessible
Write-Host "`nStep 6: Verifying database access..." -ForegroundColor White
$databases = @("bbbot1", "mansa_bot", "mlflow_db", "mansa_quant", "Bentley_Budget")

foreach ($db in $databases) {
    $result = Invoke-Docker -Args @("exec", "bentley-mysql", "mysql", "-uroot", "-proot", "-e", "USE $db; SELECT 1;") 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   $db - accessible" -ForegroundColor Green
    } else {
        Write-Host "   $db - ERROR" -ForegroundColor Red
    }
}

# Step 7: Check connection limits
Write-Host "`nStep 7: Checking connection statistics..." -ForegroundColor White
$maxUsed = Invoke-Docker -Args @("exec", "bentley-mysql", "mysql", "-uroot", "-proot", "-N", "-e", "SHOW STATUS LIKE 'Max_used_connections';") 2>&1 | Select-String -Pattern "\d+$"
$maxConn = Invoke-Docker -Args @("exec", "bentley-mysql", "mysql", "-uroot", "-proot", "-N", "-e", "SHOW VARIABLES LIKE 'max_connections';") 2>&1 | Select-String -Pattern "\d+$"

if ($maxUsed -and $maxConn) {
    $usedNum = [int]($maxUsed.Line -replace '\D', '')
    $maxNum = [int]($maxConn.Line -replace '\D', '')
    Write-Host "   Connection usage: $usedNum / $maxNum" -ForegroundColor Cyan
    $usage = $usedNum / $maxNum * 100
    
    if ($usage -gt 80) {
        Write-Host "   Connection usage is high ($([math]::Round($usage, 1))%)" -ForegroundColor Yellow
    } else {
        Write-Host "   Connection usage is healthy ($([math]::Round($usage, 1))%)" -ForegroundColor Green
    }
}

# Step 8: Display current active connections
Write-Host "`nStep 8: Current active connections..." -ForegroundColor White
$activeConnections = Invoke-Docker -Args @("exec", "bentley-mysql", "mysql", "-uroot", "-proot", "-e", "SELECT USER, DB, COUNT(*) as COUNT FROM INFORMATION_SCHEMA.PROCESSLIST WHERE COMMAND != 'Daemon' GROUP BY USER, DB;") 2>&1 | Select-String -NotMatch "Warning|password"

Write-Host $activeConnections -ForegroundColor Cyan

# Step 9: Test external connection from host
Write-Host "`nStep 9: Testing external connection (port 3307)..." -ForegroundColor White
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("127.0.0.1", 3307)
    if ($tcpClient.Connected) {
        Write-Host "Port 3307 is accessible from host." -ForegroundColor Green
        $tcpClient.Close()
    }
} catch {
    Write-Host "Cannot connect to port 3307 from host." -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
}

# Summary
Write-Host "`n" -NoNewline
Write-Host "=" * 70 -ForegroundColor Gray
Write-Host "MySQL Connection Diagnostic Complete." -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Gray

Write-Host "`nConnection Information:" -ForegroundColor Cyan
Write-Host "   Host:     127.0.0.1" -ForegroundColor White
Write-Host "   Port:     3307" -ForegroundColor White
Write-Host "   Username: root" -ForegroundColor White
Write-Host "   Password: root" -ForegroundColor White

Write-Host "`nAvailable Databases:" -ForegroundColor Cyan
Write-Host "   - bbbot1          - Equities data (Tiingo, Massive, Barchart, AlphaVantage)" -ForegroundColor White
Write-Host "   - mansa_bot       - Main application database" -ForegroundColor White
Write-Host "   - mlflow_db       - MLflow experiments and logging" -ForegroundColor White
Write-Host "   - mansa_quant     - Quantitative analysis data" -ForegroundColor White
Write-Host "   - Bentley_Budget  - Budget tracking data" -ForegroundColor White

Write-Host "`nReconnection Instructions:" -ForegroundColor Cyan
Write-Host "   1. In VS Code: Click any SQL connection in the SQLTools sidebar" -ForegroundColor Gray
Write-Host "   2. Right-click → 'Disconnect'" -ForegroundColor Gray
Write-Host "   3. Right-click → 'Connect'" -ForegroundColor Gray
Write-Host "   4. Or restart VS Code to refresh all connections" -ForegroundColor Gray

Write-Host "`nTo run this diagnostic again:" -ForegroundColor Cyan
Write-Host "   .\fix_mysql_connections.ps1" -ForegroundColor Gray

Write-Host "`n"
