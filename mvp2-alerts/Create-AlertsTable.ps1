# Create alerts_log table in MySQL
# Requires MySQL command line tools installed

$MYSQL_HOST = "127.0.0.1"
$MYSQL_PORT = "3307"
$MYSQL_USER = "root"
$MYSQL_DB = "bbbot1"

Write-Host "Creating alerts_log table..." -ForegroundColor Cyan
Write-Host ""

$sqlCommand = @"
CREATE TABLE IF NOT EXISTS alerts_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  symbol VARCHAR(20) NOT NULL,
  change_percent DECIMAL(6,2) NOT NULL,
  price DECIMAL(12,2),
  currency VARCHAR(10) DEFAULT 'USD',
  alert_type VARCHAR(50) NOT NULL,
  discord_delivered BOOLEAN DEFAULT FALSE,
  discord_error TEXT,
  sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_symbol (symbol),
  INDEX idx_sent_at (sent_at),
  INDEX idx_alert_type (alert_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"@

# Try to run with mysql command
try {
    $sqlCommand | & "mysql" -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER $MYSQL_DB 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Table created successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Verifying table..." -ForegroundColor Yellow
        & "mysql" -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER $MYSQL_DB -e "DESCRIBE alerts_log;" 2>&1
    } else {
        Write-Host "✗ Error creating table" -ForegroundColor Red
        Write-Host "Check MySQL connection: Host=$MYSQL_HOST, Port=$MYSQL_PORT, User=$MYSQL_USER, DB=$MYSQL_DB" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "✗ MySQL client not found" -ForegroundColor Red
    Write-Host "Please install MySQL command-line tools or use MySQL Workbench to run the SQL file" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternative: Open MySQL Workbench and run:" -ForegroundColor Cyan
    Write-Host "  1. File > Open SQL Script" -ForegroundColor White
    Write-Host "  2. Select: create_alerts_log_table.sql" -ForegroundColor White
    Write-Host "  3. Execute" -ForegroundColor White
}
