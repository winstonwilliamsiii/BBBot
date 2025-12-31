// create_alerts_table.js
// Creates the alerts_log table in MySQL

require('dotenv').config();
const mysql = require('mysql2/promise');

async function createTable() {
  console.log('🔧 Creating alerts_log table...\n');

  const dbConfig = {
    host: process.env.MYSQL_HOST || '127.0.0.1',
    port: parseInt(process.env.MYSQL_PORT || '3306'),
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || 'root',
    database: process.env.MYSQL_DATABASE || 'bbbot1'
  };

  console.log(`📡 Connecting to: ${dbConfig.host}:${dbConfig.port}/${dbConfig.database}`);

  try {
    const connection = await mysql.createConnection(dbConfig);
    console.log('✓ Connected to MySQL\n');

    const createTableSQL = `
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
    `;

    console.log('Creating table: alerts_log');
    await connection.execute(createTableSQL);
    console.log('✓ Table created successfully!\n');

    // Verify table structure
    console.log('📋 Table structure:');
    const [columns] = await connection.execute('DESCRIBE alerts_log;');
    console.table(columns);

    // Show table stats
    const [stats] = await connection.execute('SELECT COUNT(*) as record_count FROM alerts_log;');
    console.log(`\n📊 Current records: ${stats[0].record_count}`);

    await connection.end();
    console.log('\n✅ Setup complete! Ready to log alerts.');
  } catch (err) {
    console.error('\n❌ Error:', err.message);
    console.log('\n📝 Troubleshooting:');
    console.log(`   1. Verify MySQL is running on ${dbConfig.host}:${dbConfig.port}`);
    console.log(`   2. Check .env file has correct credentials`);
    console.log(`   3. Ensure database '${dbConfig.database}' exists`);
    console.log(`\n   Run this to create database first:`);
    console.log(`   mysql -h ${dbConfig.host} -P ${dbConfig.port} -u ${dbConfig.user} -e "CREATE DATABASE IF NOT EXISTS ${dbConfig.database};"`);
    process.exit(1);
  }
}

createTable();
