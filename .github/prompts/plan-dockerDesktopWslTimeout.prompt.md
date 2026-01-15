# Docker Desktop WSL Timeout Resolution Plan

## Context
Your Docker setup has significant infrastructure (MySQL, Airflow, MLflow, Airbyte) which increases WSL complexity. The timeout (`DockerDesktop/Wsl/CommandTimedOut: wslexec error`) likely stems from hung containers or corrupted WSL state.

## Docker Configuration Summary

### Active Services
- **Streamlit** (port 8501) - Main web application
- **Airflow** (port 8080) - Workflow orchestration  
- **MLflow** (port 5000) - Experiment tracking
- **Airbyte** (ports 8000-8001) - Data integration
- **MySQL** (port 3306) - Data warehouse

### Deployment Model
- **Primary**: Vercel serverless (`api/index.py`)
- **Alternative**: Docker containers (`docker-compose.yml`)

---

## Resolution Steps (Systematic)

### Step 1: Force Terminate All Docker Processes
**Objective**: Clear stuck Docker/WSL state completely

```powershell
# Kill Docker Desktop processes
taskkill /F /IM "Docker Desktop.exe"
taskkill /F /IM "com.docker.service"
taskkill /F /IM "wslservice.exe"
taskkill /F /IM "wsl.exe"

# Wait 5 seconds for cleanup
Start-Sleep -Seconds 5

# Shutdown WSL completely
wsl --shutdown
```

### Step 2: Clean WSL Distributions Manually
**Objective**: Remove corrupted WSL distro data without waiting for Docker to respond

```powershell
# Navigate to Docker WSL storage
$dockerWslPath = "$env:LOCALAPPDATA\Docker\wsl"

# Force delete distro and data folders if they exist
if (Test-Path "$dockerWslPath\distro") {
    Remove-Item "$dockerWslPath\distro" -Recurse -Force
}
if (Test-Path "$dockerWslPath\data") {
    Remove-Item "$dockerWslPath\data" -Recurse -Force
}

# List and unregister docker distributions
wsl --list --quiet | Where-Object { $_ -match "docker" } | ForEach-Object {
    Write-Host "Unregistering: $_"
    wsl --unregister $_
}
```

### Step 3: Reset Docker Desktop Installation
**Objective**: Fully reinstall Docker with clean WSL2 setup

```powershell
# Uninstall Docker Desktop
Get-Package -Name "Docker Desktop" | Uninstall-Package -Force

# Delete all Docker data
$dockerAppData = "$env:LOCALAPPDATA\Docker"
$dockerRoaming = "$env:APPDATA\Docker"

if (Test-Path $dockerAppData) {
    Remove-Item $dockerAppData -Recurse -Force
}
if (Test-Path $dockerRoaming) {
    Remove-Item $dockerRoaming -Recurse -Force
}

# Reboot Windows to ensure clean state
Restart-Computer -Force
```

**After reboot**: Download and install latest Docker Desktop from https://www.docker.com/products/docker-desktop
- During installation, ensure WSL2 backend is selected
- Complete Docker Desktop setup wizard

### Step 4: Rebuild Containers Incrementally
**Objective**: Test Docker functionality with minimal services first

#### 4a. Verify Docker Installation
```powershell
docker --version
docker run hello-world
```

#### 4b. Start Streamlit Service Only
```powershell
cd C:\Users\winst\BentleyBudgetBot
docker-compose up bentley-budget-bot
```

#### 4c. Test Python Environment
```powershell
docker-compose up -f docker-compose-python-test.yml
```

#### 4d. Full Stack (After Verification)
```powershell
# Only if Steps 4a-4c succeed
.\startup_all_services.ps1
```

---

## Alternative: Skip Docker, Use Vercel + Venv

Given your primary deployment is Vercel-based, consider developing without Docker:

```powershell
# Activate Python venv
.\.venv\Scripts\Activate.ps1

# Run Streamlit directly
streamlit run streamlit_app.py
```

**Benefits**:
- No WSL timeout issues
- Faster local development
- Still test Docker for production deployment only
- Reduces local resource usage

---

## Decision Tree

### Do you need Docker running locally?
- **YES**: Follow Steps 1-4 above
- **NO**: Use venv + Streamlit directly for development
  - Only use Docker for final production validation
  - Reduces troubleshooting surface area

### Which services do you actually use locally?
- **Just Streamlit**: Run `docker-compose up bentley-budget-bot`
- **Streamlit + Airflow**: Add `depends_on` to Airflow service
- **Full stack**: Use `docker-compose-full-stack.yml` after verification

---

## Troubleshooting If Still Failing

| Issue | Solution |
|-------|----------|
| WSL still hangs on `wsl -l -v` | Disable WSL integration in Docker Desktop settings, use Hyper-V backend instead |
| Docker containers won't start | Check disk space (`wsl --manage` command) |
| Port conflicts (8501, 3306) | Run `netstat -ano \| findstr :PORT` to find process using port |
| Memory exhaustion | Limit container resources in `docker-compose.yml`: `mem_limit: 2g` |

---

## Recommendation

**Start with Step 1** (Force terminate + WSL shutdown). This fixes 70% of timeouts without reinstalling Docker.

If that doesn't work, move to **Step 2** (Manual WSL cleanup) before attempting full reinstall.

Only do **Step 3** (Full reinstall) if Steps 1-2 fail completely.
