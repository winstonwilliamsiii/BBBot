param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("streamlit", "api", "rhea", "altair", "bots", "tf", "classical-bots", "dogon")]
    [string]$Service,

    [string]$RepoRoot,

    [switch]$AllowLegacyFallback
)

if (-not $RepoRoot) {
    $RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}

$externalVenvRoot = Join-Path $env:USERPROFILE ".venvs\BentleyBudgetBot"

$preferredEnvByService = @{
    streamlit = ".venv-streamlit"
    api = ".venv-api"
    rhea = ".venv-rhea"
    altair = ".venv-rhea"
    bots = ".venv-bots"
    tf = ".venv-tf"
    "classical-bots" = ".venv-rhea"
    dogon = ".venv-dogon"
}

$candidates = New-Object System.Collections.Generic.List[string]

if ($preferredEnvByService.ContainsKey($Service)) {
    $envName = $preferredEnvByService[$Service]
    $candidates.Add((Join-Path $externalVenvRoot ("{0}\\Scripts\\python.exe" -f $envName)))
    $candidates.Add((Join-Path $RepoRoot ("{0}\\Scripts\\python.exe" -f $envName)))
}

# Allow classical bots to use Altair env as secondary option.
if ($Service -eq "classical-bots") {
    $candidates.Add((Join-Path $externalVenvRoot ".venv-altair\\Scripts\\python.exe"))
    $candidates.Add((Join-Path $RepoRoot ".venv-altair\\Scripts\\python.exe"))
}

# Backward compatibility if an Altair-specific venv still exists.
if ($Service -eq "altair") {
    $candidates.Add((Join-Path $externalVenvRoot ".venv-altair\\Scripts\\python.exe"))
    $candidates.Add((Join-Path $RepoRoot ".venv-altair\\Scripts\\python.exe"))
}

# Keep Dogon isolated first, then allow shared bot env.
if ($Service -eq "dogon") {
    $candidates.Add((Join-Path $externalVenvRoot ".venv-bots\\Scripts\\python.exe"))
    $candidates.Add((Join-Path $RepoRoot ".venv-bots\\Scripts\\python.exe"))
}

if ($AllowLegacyFallback.IsPresent) {
    $candidates.Add((Join-Path $RepoRoot ".venv\\Scripts\\python.exe"))
    $candidates.Add((Join-Path $RepoRoot "venv\\Scripts\\python.exe"))
}

foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
        Write-Output $candidate
        exit 0
    }
}

$searched = $candidates -join ", "
Write-Error "No Python interpreter found for service '$Service'. Checked: $searched"
exit 1