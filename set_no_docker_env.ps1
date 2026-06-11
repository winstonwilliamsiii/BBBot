# Force BentleyBudgetBot to use local MySQL (no Docker) for the current PowerShell session.

$env:MYSQL_HOST = "127.0.0.1"
$env:MYSQL_PORT = "3306"
$env:MYSQL_USER = "root"
$env:MYSQL_PASSWORD = "root"
$env:MYSQL_DATABASE = "mansa_bot"

$env:DB_HOST = $env:MYSQL_HOST
$env:DB_PORT = $env:MYSQL_PORT
$env:DB_USER = $env:MYSQL_USER
$env:DB_PASSWORD = $env:MYSQL_PASSWORD
$env:DB_NAME = $env:MYSQL_DATABASE

# Keep Hydra persistence on local MySQL as well.
$env:HYDRA_DATABASE_URL = "mysql+pymysql://$($env:MYSQL_USER):$($env:MYSQL_PASSWORD)@$($env:MYSQL_HOST):$($env:MYSQL_PORT)/mansa_quant"

Write-Host "No-Docker DB mode active for this shell." -ForegroundColor Green
Write-Host "MYSQL_HOST=$($env:MYSQL_HOST)" -ForegroundColor Cyan
Write-Host "MYSQL_PORT=$($env:MYSQL_PORT)" -ForegroundColor Cyan
Write-Host "MYSQL_DATABASE=$($env:MYSQL_DATABASE)" -ForegroundColor Cyan
