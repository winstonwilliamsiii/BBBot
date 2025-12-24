-- MySQL IP Whitelist Configuration for Airbyte Cloud
-- Execute this script to grant access to Airbyte Cloud IP addresses

-- Airbyte Cloud IP Addresses (as of November 2025)
-- These IPs need access to connect to your MySQL database

-- Create dedicated airbyte user if not exists (MySQL 8.0 syntax)
CREATE USER IF NOT EXISTS 'airbyte'@'%' IDENTIFIED BY 'airbyte_secure_password_2025';

-- Grant privileges to the mansa_bot database
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, CREATE TEMPORARY TABLES, LOCK TABLES 
ON mansa_bot.* TO 'airbyte'@'%';

-- Grant privileges from specific Airbyte Cloud IP addresses
-- Note: MySQL 8.0 requires CREATE USER before GRANT
-- Network-level firewall rules are recommended for additional security

-- US Region IPs
CREATE USER IF NOT EXISTS 'airbyte'@'34.106.109.131' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.106.109.131';

CREATE USER IF NOT EXISTS 'airbyte'@'34.106.196.165' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.106.196.165';

CREATE USER IF NOT EXISTS 'airbyte'@'34.106.60.246' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.106.60.246';

CREATE USER IF NOT EXISTS 'airbyte'@'34.106.229.69' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.106.229.69';

CREATE USER IF NOT EXISTS 'airbyte'@'34.106.127.139' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.106.127.139';

CREATE USER IF NOT EXISTS 'airbyte'@'34.106.218.58' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.106.218.58';

CREATE USER IF NOT EXISTS 'airbyte'@'34.106.115.240' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.106.115.240';

CREATE USER IF NOT EXISTS 'airbyte'@'34.106.225.141' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.106.225.141';

-- EU Region IPs
CREATE USER IF NOT EXISTS 'airbyte'@'13.37.4.46' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'13.37.4.46';

CREATE USER IF NOT EXISTS 'airbyte'@'13.37.142.60' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'13.37.142.60';

CREATE USER IF NOT EXISTS 'airbyte'@'35.181.124.238' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'35.181.124.238';

-- Note: CIDR range 34.33.7.0/29 cannot be directly specified in MySQL
-- This translates to IPs: 34.33.7.0 - 34.33.7.7
-- Adding individual IPs from this range:
CREATE USER IF NOT EXISTS 'airbyte'@'34.33.7.0' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.33.7.0';

CREATE USER IF NOT EXISTS 'airbyte'@'34.33.7.1' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.33.7.1';

CREATE USER IF NOT EXISTS 'airbyte'@'34.33.7.2' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.33.7.2';

CREATE USER IF NOT EXISTS 'airbyte'@'34.33.7.3' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.33.7.3';

CREATE USER IF NOT EXISTS 'airbyte'@'34.33.7.4' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.33.7.4';

CREATE USER IF NOT EXISTS 'airbyte'@'34.33.7.5' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.33.7.5';

CREATE USER IF NOT EXISTS 'airbyte'@'34.33.7.6' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.33.7.6';

CREATE USER IF NOT EXISTS 'airbyte'@'34.33.7.7' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airbyte'@'34.33.7.7';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify grants
SELECT User, Host FROM mysql.user WHERE User = 'airbyte';

-- Display connection information for Airbyte setup
SELECT 'MySQL Connection Info for Airbyte Cloud:' as Info;
SELECT 'Host: <your-public-ip-or-domain>' as Host;
SELECT 'Port: 3307' as Port;
SELECT 'Database: mansa_bot' as Database;
SELECT 'Username: airbyte' as Username;
SELECT 'Password: airbyte_secure_password_2025' as Password;
