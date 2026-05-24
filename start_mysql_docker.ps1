# Bentley Budget Bot - Docker + MySQL startup script
# Supports Docker Desktop and Docker Engine running in WSL2.

$script:DockerMode = if ($env:BENTLEY_DOCKER_MODE) { $env:BENTLEY_DOCKER_MODE.ToLowerInvariant() } else { "auto" }
$script:WslDistro = if ($env:BENTLEY_WSL_DISTRO) { $env:BENTLEY_WSL_DISTRO } else { "Ubuntu" }
$script:UseWslDocker = $false
$script:DockerDirWin = Join-Path $PSScriptRoot "docker"
$script:DockerDirWsl = $null
$script:LastDockerExitCode = 0

Write-Host "`nBentley Bot - Starting Docker and MySQL Environment..." -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

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

function Convert-WindowsPathToWsl {
    param(
        [string]$Path
    )

    if (-not $Path) {
        return ""
    }

    $normalized = $Path -replace "\\", "/"
    if ($normalized -match "^[A-Za-z]:/") {
        $drive = $normalized.Substring(0, 1).ToLowerInvariant()
        $rest = $normalized.Substring(3)
        return "/mnt/$drive/$rest"
    }

    return $normalized
}

function Test-WslDirectory {
    param(
        [string]$Path
    )

    if (-not $Path) {
        return $false
    }

    try {
        & wsl.exe -d $script:WslDistro -- test -d $Path
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Initialize-DockerMode {
    if ($script:DockerMode -eq "wsl") {
        if (-not (Test-WslDocker)) {
            Write-Host "WSL Docker mode requested but Docker Engine is not ready inside '$($script:WslDistro)'." -ForegroundColor Red
            return $false
        }
        $script:DockerDirWsl = Convert-WindowsPathToWsl -Path $script:DockerDirWin
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
        $script:DockerDirWsl = Convert-WindowsPathToWsl -Path $script:DockerDirWin
        $script:UseWslDocker = $true
        return $true
    }

    return $false
}

function Invoke-Docker {
    param(
        [string[]]$DockerArgs,
        [switch]$SuppressErrors
    )

    $output = $null
    if ($script:UseWslDocker) {
        if ($SuppressErrors) {
            $output = & wsl.exe -d $script:WslDistro -- docker @DockerArgs 2>$null
        } else {
            $output = & wsl.exe -d $script:WslDistro -- docker @DockerArgs
        }
        $script:LastDockerExitCode = $LASTEXITCODE
        return $output
    }

    if ($SuppressErrors) {
        $output = & docker @DockerArgs 2>$null
    } else {
        $output = & docker @DockerArgs
    }
    $script:LastDockerExitCode = $LASTEXITCODE
    return $output
}

function Test-DockerRunning {
    Invoke-Docker -DockerArgs @("version", "--format", "{{.Server.Version}}") -SuppressErrors
    return ($script:LastDockerExitCode -eq 0)
}

function Start-DockerDesktop {
    Write-Host "`nStarting Docker Desktop..." -ForegroundColor Yellow

    $dockerPaths = @(
        "C:\Program Files\Docker\Docker\Docker Desktop.exe",
        "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
    )

    $dockerExe = $dockerPaths | Where-Object { Test-Path $_ } | Select-Object -First 1

    if (-not $dockerExe) {
        Write-Host "Docker Desktop not found. Please install Docker Desktop." -ForegroundColor Red
        Write-Host "   Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        return $false
    }

    Start-Process $dockerExe -WindowStyle Hidden

    $maxWaitTime = 90
    $waited = 0

    while (-not (Test-DockerRunning) -and $waited -lt $maxWaitTime) {
        Start-Sleep -Seconds 3
        $waited += 3
        Write-Host "   Waiting for Docker... ($waited/$maxWaitTime seconds)" -ForegroundColor Gray
    }

    if (Test-DockerRunning) {
        Write-Host "Docker Desktop is ready." -ForegroundColor Green
        return $true
    }

    Write-Host "Docker Desktop failed to start within $maxWaitTime seconds" -ForegroundColor Red
    return $false
}

function Repair-DockerEngine {
    if ($script:UseWslDocker) {
        Write-Host "Docker Engine is expected in WSL2 distro '$($script:WslDistro)'." -ForegroundColor Yellow
        Write-Host "   Start it in WSL (for example: sudo service docker start) and rerun." -ForegroundColor Yellow
        return $false
    }

    Write-Host "`nDocker engine appears unhealthy. Attempting self-repair..." -ForegroundColor Yellow

    $wslService = Get-Service -Name "WSLService" -ErrorAction SilentlyContinue
    if ($wslService -and $wslService.Status -ne 'Running') {
        try {
            Start-Service -Name "WSLService" -ErrorAction Stop
            Write-Host "   Started WSLService" -ForegroundColor Green
        } catch {
            Write-Host "   Could not start WSLService automatically: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

    try {
        Get-Process "Docker Desktop", "com.docker.backend" -ErrorAction SilentlyContinue | Stop-Process -Force
        Write-Host "   Restarted Docker Desktop processes" -ForegroundColor Cyan
    } catch {
        Write-Host "   Could not fully stop existing Docker processes" -ForegroundColor Yellow
    }

    if (-not (Start-DockerDesktop)) {
        return $false
    }

    return Test-DockerRunning
}

function Invoke-Compose {
    param(
        [string[]]$DockerArgs
    )

    if ($script:UseWslDocker) {
        if (-not (Test-WslDirectory -Path $script:DockerDirWsl)) {
            Write-Host "WSL compose directory not found: $($script:DockerDirWsl)" -ForegroundColor Red
            return $false
        }
        $argString = $DockerArgs -join " "
        & wsl.exe -d $script:WslDistro -- bash -lc "cd $($script:DockerDirWsl) && docker compose $argString"
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        Write-Host "docker compose failed in WSL, trying docker-compose fallback..." -ForegroundColor Yellow
        & wsl.exe -d $script:WslDistro -- bash -lc "cd $($script:DockerDirWsl) && docker-compose $argString"
        return ($LASTEXITCODE -eq 0)
    }

    & docker compose @DockerArgs 2>$null
    if ($LASTEXITCODE -eq 0) {
        return $true
    }

    & docker-compose @DockerArgs
    return ($LASTEXITCODE -eq 0)
}

function Get-MySqlContainerName {
    $all = Invoke-Docker -DockerArgs @("ps", "-a", "--format", "{{.Names}}") -SuppressErrors
    if (-not $all) {
        return $null
    }

    $preferred = @("bentley-mysql", "bentley_budget_mysql")
    foreach ($name in $preferred) {
        if ($all -contains $name) {
            return $name
        }
    }

    $matched = $all | Where-Object { $_ -match "mysql" } | Select-Object -First 1
    if ($matched) {
        return $matched
    }

    return $null
}

if (-not (Initialize-DockerMode)) {
    Write-Host "Docker CLI is unavailable from Windows and WSL modes." -ForegroundColor Red
    Write-Host "   Set BENTLEY_DOCKER_MODE=wsl and BENTLEY_WSL_DISTRO=Ubuntu after enabling Docker in WSL2." -ForegroundColor Yellow
    exit 1
}

if ($script:UseWslDocker) {
    Write-Host "Using Docker Engine in WSL2 distro '$($script:WslDistro)'" -ForegroundColor Cyan
} else {
    Write-Host "Using Docker Desktop/Windows docker context" -ForegroundColor Cyan
}

Write-Host "`nChecking Docker status..." -ForegroundColor White

if (Test-DockerRunning) {
    Write-Host "Docker is already running." -ForegroundColor Green
} else {
    Write-Host "Docker is not running or engine is unresponsive." -ForegroundColor Yellow
    if (-not (Repair-DockerEngine)) {
        Write-Host "Docker engine is still unavailable after repair attempts." -ForegroundColor Red
        Write-Host "   If using WSL mode, start Docker inside WSL then rerun this script." -ForegroundColor Yellow
        exit 1
    }
}

Set-Location $script:DockerDirWin

Write-Host "`nStarting MySQL containers..." -ForegroundColor White

$mysqlContainerName = Get-MySqlContainerName

if ($mysqlContainerName) {
    Write-Host "   Starting existing $mysqlContainerName container..." -ForegroundColor Cyan
    Invoke-Docker -DockerArgs @("start", $mysqlContainerName) | Out-Null
} else {
    Write-Host "   Creating bentley-mysql container (Airflow + Bbbot1)..." -ForegroundColor Cyan
    $composeOk = Invoke-Compose -DockerArgs @("-f", "docker-compose-airflow.yml", "up", "-d", "mysql")
    if (-not $composeOk) {
        Write-Host "Failed to create MySQL container via Docker Compose." -ForegroundColor Red
        exit 1
    }
    $mysqlContainerName = Get-MySqlContainerName
}

if ((Invoke-Docker -DockerArgs @("ps", "-a", "--format", "{{.Names}}") -SuppressErrors) -match "bentley-mysql-mlflow") {
    Write-Host "   Starting existing bentley-mysql-mlflow container..." -ForegroundColor Cyan
    Invoke-Docker -DockerArgs @("start", "bentley-mysql-mlflow") | Out-Null
} else {
    Write-Host "   MLflow MySQL not configured (run manually if needed)" -ForegroundColor Gray
}

Start-Sleep -Seconds 3

Write-Host "`nVerifying container status..." -ForegroundColor White

$runningContainers = $null
$maxVerifyAttempts = 10

for ($attempt = 1; $attempt -le $maxVerifyAttempts; $attempt++) {
    $runningContainers = Invoke-Docker -DockerArgs @("ps", "--filter", "name=mysql", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}") -SuppressErrors

    if ($env:BENTLEY_DEBUG_STARTUP -eq "1") {
        $rcCount = @($runningContainers).Count
        Write-Host "DEBUG: attempt $attempt filtered docker ps exit=$($script:LastDockerExitCode), rows=$rcCount" -ForegroundColor DarkYellow
        if ($runningContainers) {
            Write-Host "DEBUG: filtered output:" -ForegroundColor DarkYellow
            Write-Host ($runningContainers -join "`n") -ForegroundColor DarkYellow
        }
    }

    if ((@($runningContainers).Count -gt 0) -and ($script:LastDockerExitCode -eq 0)) {
        break
    }

    # Fallback: get full running list and filter mysql-like names in PowerShell.
    $allRunning = Invoke-Docker -DockerArgs @("ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}") -SuppressErrors
    if ($env:BENTLEY_DEBUG_STARTUP -eq "1") {
        $allCount = @($allRunning).Count
        Write-Host "DEBUG: attempt $attempt fallback docker ps exit=$($script:LastDockerExitCode), rows=$allCount" -ForegroundColor DarkYellow
        if ($allRunning) {
            Write-Host "DEBUG: fallback output:" -ForegroundColor DarkYellow
            Write-Host ($allRunning -join "`n") -ForegroundColor DarkYellow
        }
    }
    if ($allRunning) {
        $runningContainers = @($allRunning | Where-Object { $_ -match "NAMES|mysql" })
    }

    if (@($runningContainers).Count -gt 0) {
        break
    }

    if ($attempt -lt $maxVerifyAttempts) {
        Write-Host "   Waiting for MySQL containers to report running... ($attempt/$maxVerifyAttempts)" -ForegroundColor Gray
        Start-Sleep -Seconds 3
    }
}

if ($runningContainers) {
    Write-Host "`n$runningContainers" -ForegroundColor Green
} else {
    Write-Host "No MySQL containers are running." -ForegroundColor Red
    $allContainers = Invoke-Docker -DockerArgs @("ps", "-a", "--format", "table {{.Names}}\t{{.Status}}") -SuppressErrors
    if ($allContainers) {
        Write-Host "`nContainer snapshot:" -ForegroundColor Yellow
        Write-Host $allContainers -ForegroundColor DarkYellow
    }
    exit 1
}

Write-Host "`nTesting MySQL connection..." -ForegroundColor White

if (-not $mysqlContainerName) {
    $mysqlContainerName = Get-MySqlContainerName
}

if (-not $mysqlContainerName) {
    Write-Host "Could not resolve a MySQL container name to test." -ForegroundColor Red
    exit 1
}

Invoke-Docker -DockerArgs @("exec", $mysqlContainerName, "mysqladmin", "ping", "-uroot", "-proot") | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "MySQL is responding to connections." -ForegroundColor Green

    Write-Host "`nAvailable databases:" -ForegroundColor White
    $dbRows = Invoke-Docker -DockerArgs @("exec", $mysqlContainerName, "mysql", "-uroot", "-proot", "-e", "SHOW DATABASES;") -SuppressErrors
    foreach ($dbRow in $dbRows) {
        if (
            $dbRow -and
            $dbRow -notin @("Database", "mysql", "information_schema", "performance_schema", "sys")
        ) {
            Write-Host "   - $dbRow" -ForegroundColor Cyan
        }
    }
} else {
    Write-Host "MySQL is starting up and may need a few more seconds..." -ForegroundColor Yellow
}

Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Gray
Write-Host "MySQL environment ready." -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Gray

Write-Host "`nMySQL Workbench connection settings:" -ForegroundColor Cyan
Write-Host "   Connection Name: Demo_Bots Bentley" -ForegroundColor White
Write-Host "   Hostname: 127.0.0.1" -ForegroundColor White
Write-Host "   Port: 3307" -ForegroundColor White
Write-Host "   Username: root" -ForegroundColor White
Write-Host "   Password: root" -ForegroundColor White
Write-Host "   Default Schema: mansa_bot" -ForegroundColor White

Write-Host "`nAvailable databases:" -ForegroundColor Cyan
Write-Host "   - mansa_bot    - Main application database (Bbbot1, Tiingo, yfinance)" -ForegroundColor White
Write-Host "   - airflow      - Airflow metadata and DAG runs" -ForegroundColor White
Write-Host "   - mlflow_db    - MLflow experiments (if running)" -ForegroundColor White

Write-Host "`nQuick commands:" -ForegroundColor Cyan
Write-Host "   View logs:      docker logs bentley-mysql" -ForegroundColor Gray
Write-Host "   Stop MySQL:     docker stop bentley-mysql" -ForegroundColor Gray
Write-Host "   Restart MySQL:  docker restart bentley-mysql" -ForegroundColor Gray
Write-Host "   MySQL shell:    docker exec -it bentley-mysql mysql -uroot -proot" -ForegroundColor Gray
Write-Host "   Active name:    $mysqlContainerName" -ForegroundColor Gray

if ($script:UseWslDocker) {
    Write-Host "`nWSL mode hints:" -ForegroundColor Cyan
    Write-Host "   Export before running scripts: BENTLEY_DOCKER_MODE=wsl" -ForegroundColor Gray
    Write-Host "   Optional distro override: BENTLEY_WSL_DISTRO=Ubuntu" -ForegroundColor Gray
}

Write-Host "`n"

Set-Location $PSScriptRoot
