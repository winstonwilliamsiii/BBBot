param()

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$nodeExe = 'C:\Program Files\nodejs\node.exe'
$indexJs = Join-Path $scriptDir 'index.js'

if (-not (Test-Path $nodeExe)) {
    Write-Error "Node.js not found at $nodeExe"
}

& $nodeExe $indexJs --run-once
exit $LASTEXITCODE