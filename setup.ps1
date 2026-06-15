param(
    [switch]$SkipNode,
    [switch]$SkipPython,
    [string]$VenvPath = "venv",
    [string]$RequirementsFile = "requirements.txt"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

function Get-RequirementsHash {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return ""
    }

    return (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

if (-not $SkipNode) {
    if (Test-Path "package.json") {
        if (Test-Path "node_modules") {
            Write-Host "[setup] node_modules present; skipping npm install."
        }
        else {
            if (Test-Path "package-lock.json") {
                Write-Host "[setup] node_modules missing; installing dependencies from package-lock.json via npm install."
            }
            else {
                Write-Host "[setup] node_modules missing; installing dependencies via npm install."
            }
            npm install
        }
    }
    else {
        Write-Host "[setup] package.json not found; skipping Node.js setup."
    }
}

if (-not $SkipPython) {
    if (-not (Test-Path $RequirementsFile)) {
        Write-Host "[setup] requirements.txt not found; skipping Python dependency setup."
    }
    else {
        $venvPython = Join-Path $repoRoot "$VenvPath\Scripts\python.exe"
        if (-not (Test-Path $venvPython)) {
            Write-Host "[setup] virtual environment missing; creating $VenvPath"
            python -m venv $VenvPath
        }

        $venvPython = Join-Path $repoRoot "$VenvPath\Scripts\python.exe"
        $stampFile = Join-Path $repoRoot "$VenvPath\.requirements.sha256"
        $requirementsHash = Get-RequirementsHash -Path (Join-Path $repoRoot $RequirementsFile)
        $currentStamp = ""
        if (Test-Path $stampFile) {
            $currentStamp = (Get-Content -Path $stampFile -Raw).Trim()
        }

        if ($requirementsHash -ne "" -and $requirementsHash -eq $currentStamp) {
            Write-Host "[setup] requirements hash unchanged; skipping pip install."
        }
        else {
            Write-Host "[setup] installing Python dependencies from $RequirementsFile"
            & $venvPython -m pip install --upgrade pip
            & $venvPython -m pip install -r $RequirementsFile
            Set-Content -Path $stampFile -Value $requirementsHash -NoNewline
        }
    }
}

Write-Host "[setup] complete"