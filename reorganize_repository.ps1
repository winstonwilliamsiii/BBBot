# Continue past individual errors (missing paths, already-moved dirs)
$ErrorActionPreference = "Continue"

Write-Host "Starting BentleyBudgetBot reorganization..."

# === Ensure Directories Exist ===
$dirs = @(
    "Frontend/pages",
    "Frontend/frontend",
    "Frontend/vercel-frontend",
    "Backend/api",
    "Backend/services",
    "Backend/bentleybot/sql",
    "Backend/bentleybot/utils",
    "Backend/appwrite-functions",
    "Database/migrations",
    "Database/mysql_config",
    "Integrations/alpaca",
    "Integrations/plaid",
    "Integrations/binance",
    "Integrations/sdk",
    "DataPipelines/workflows/airflow",
    "DataPipelines/workflows/airbyte",
    "DataPipelines/workflows/mlflow",
    "DataPipelines/dbt_project",
    "DataPipelines/bbbot1_pipeline",
    "TestingScripts/tests",
    "TestingScripts/scripts",
    "Documentation",
    "DevOps/.github/workflows",
    "EnterpriseAgentPlatform/Agents/Orchestrator",
    "EnterpriseAgentPlatform/Tools",
    "EnterpriseAgentPlatform/Prompts",
    "EnterpriseAgentPlatform/api/routes",
    "EnterpriseAgentPlatform/api/schemas",
    "EnterpriseAgentPlatform/api/auth",
    "EnterpriseAgentPlatform/api/middleware",
    "EnterpriseAgentPlatform/governance/policies",
    "EnterpriseAgentPlatform/governance/guardrails",
    "EnterpriseAgentPlatform/governance/audit",
    "EnterpriseAgentPlatform/evals/datasets",
    "EnterpriseAgentPlatform/evals/reports",
    "MT5/experts",
    "MT5/libraries",
    "MT5/scripts",
    "MT5/config",
    "MT5/tests",
    "MT5/docs"
)

foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        Write-Host "Creating directory: $d"
        New-Item -ItemType Directory -Force -Path $d | Out-Null
    }
}

# Helper: git mv only if source exists
function Move-IfExists {
    param([string]$src, [string]$dest)
    if (Test-Path $src) {
        git mv $src $dest
        Write-Host "  Moved: $src -> $dest"
    } else {
        Write-Host "  SKIP (not found): $src"
    }
}

# Helper: git mv glob (directory contents)
function Move-GlobIfExists {
    param([string]$srcDir, [string]$destDir)
    if (Test-Path $srcDir) {
        $items = Get-ChildItem $srcDir -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne '__pycache__' }
        foreach ($item in $items) {
            $result = git mv $item.FullName "$destDir/" 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  WARN: $($result -join ' ')"
            }
        }
        Write-Host "  Moved contents: $srcDir/* -> $destDir/"
    } else {
        Write-Host "  SKIP (not found): $srcDir"
    }
}

# === Backend ===
Move-GlobIfExists "api"                 "Backend/api"
Move-GlobIfExists "services"            "Backend/services"
Move-GlobIfExists "bentleybot"          "Backend/bentleybot"
Move-GlobIfExists "appwrite-functions"  "Backend/appwrite-functions"

# === Database ===
Move-IfExists "schema.sql"                            "Database/schema.sql"
Move-IfExists "MySQL for UNIFIED BROKER Schema.sql"   "Database/unified_broker_schema.sql"
Move-GlobIfExists "migrations"   "Database/migrations"
Move-GlobIfExists "mysql_config" "Database/mysql_config"

# === Integrations ===
Move-GlobIfExists "integrations/alpaca"  "Integrations/alpaca"
Move-GlobIfExists "integrations/plaid"   "Integrations/plaid"
Move-GlobIfExists "integrations/binance" "Integrations/binance"
Move-GlobIfExists "sdk"                  "Integrations/sdk"

# === Data Pipelines ===
Move-GlobIfExists "workflows/airflow"  "DataPipelines/workflows/airflow"
Move-GlobIfExists "workflows/airbyte"  "DataPipelines/workflows/airbyte"
Move-GlobIfExists "workflows/mlflow"   "DataPipelines/workflows/mlflow"
Move-GlobIfExists "dbt_project"        "DataPipelines/dbt_project"
Move-GlobIfExists "bbbot1_pipeline"    "DataPipelines/bbbot1_pipeline"

# === Testing & Scripts ===
Move-GlobIfExists "tests"   "TestingScripts/tests"
Move-GlobIfExists "scripts" "TestingScripts/scripts"
Get-ChildItem "test_*.py" -ErrorAction SilentlyContinue | ForEach-Object {
    git mv $_.FullName "TestingScripts/$($_.Name)"
}

# === Documentation ===
Move-IfExists "PROJECT_STRUCTURE.md"         "Documentation/PROJECT_STRUCTURE.md"
Move-IfExists "UNIFIED_BROKER_SCHEMA_GUIDE.md" "Documentation/UNIFIED_BROKER_SCHEMA_GUIDE.md"
Move-IfExists "MYSQL_CONSOLIDATION_REPORT.md"  "Documentation/MYSQL_CONSOLIDATION_REPORT.md"
Move-IfExists "BROKER_SETUP_GUIDE.md"          "Documentation/BROKER_SETUP_GUIDE.md"

# === DevOps ===
Move-IfExists "docker-compose.yml"  "DevOps/docker-compose.yml"
Move-IfExists "Dockerfile"          "DevOps/Dockerfile"
Move-IfExists "railway.json"        "DevOps/railway.json"
Move-GlobIfExists ".github/workflows" "DevOps/.github/workflows"

# === Enterprise Agent Platform ===
Move-IfExists "Enterprise agent Platform" "EnterpriseAgentPlatform/"
Move-IfExists "Copilot.md"               "EnterpriseAgentPlatform/Copilot.md"
Move-IfExists ".env.example"             "EnterpriseAgentPlatform/.env.example"
Move-GlobIfExists "Agents"     "EnterpriseAgentPlatform/Agents"
Move-GlobIfExists "Tools"      "EnterpriseAgentPlatform/Tools"
Move-GlobIfExists "Prompts"    "EnterpriseAgentPlatform/Prompts"
Move-GlobIfExists "governance" "EnterpriseAgentPlatform/governance"
Move-GlobIfExists "evals"      "EnterpriseAgentPlatform/evals"

# === MT5 Module ===
Move-IfExists "QUICK_REFERENCE.txt"       "MT5/QUICK_REFERENCE.txt"
Move-IfExists "BentleyBot_GBP_JPY_EA.mq5" "MT5/experts/BentleyBot_GBP_JPY_EA.mq5"
Move-IfExists "BentleyBot_XAU_USD_EA.mq5" "MT5/experts/BentleyBot_XAU_USD_EA.mq5"
Move-IfExists "BentleyBot.mqh"            "MT5/libraries/BentleyBot.mqh"
Move-IfExists "CustomIndicators.mqh"      "MT5/libraries/CustomIndicators.mqh"
Move-IfExists "mt5_alpaca_bridge.py"      "MT5/scripts/mt5_alpaca_bridge.py"
Move-IfExists "discord_notifier.py"       "MT5/scripts/discord_notifier.py"
Move-IfExists "trading_config.json"       "MT5/config/trading_config.json"
Move-IfExists "trading_symbols.conf"      "MT5/config/trading_symbols.conf"
Move-IfExists "BACKTEST_TEMPLATE.txt"     "MT5/tests/BACKTEST_TEMPLATE.txt"
Move-IfExists "SETUP.md"                  "MT5/docs/SETUP.md"
Move-IfExists "ARCHITECTURE.md"           "MT5/docs/ARCHITECTURE.md"
Move-IfExists "API_INTEGRATION.md"        "MT5/docs/API_INTEGRATION.md"
Move-IfExists "COMPILER_API_REQUIREMENTS.md" "MT5/docs/COMPILER_API_REQUIREMENTS.md"
Move-IfExists "DEPLOYMENT.md"             "MT5/docs/DEPLOYMENT.md"
Move-IfExists "TROUBLESHOOTING.md"        "MT5/docs/TROUBLESHOOTING.md"
Move-IfExists "README_INDEX.md"           "MT5/docs/README_INDEX.md"
Move-IfExists "README_INITIAL_COMMIT.md"  "MT5/docs/README_INITIAL_COMMIT.md"

Write-Host "✅ Reorganization complete. Ready to commit."

