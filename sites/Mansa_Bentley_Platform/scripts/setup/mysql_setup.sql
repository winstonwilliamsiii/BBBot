-- MySQL Setup for Docker Airflow - mansa_bot Database
-- This script runs automatically when MySQL container starts

-- Create the mansa_bot database if it doesn't exist
CREATE DATABASE IF NOT EXISTS mansa_bot;
USE mansa_bot;

-- Create airflow user with necessary permissions
CREATE USER IF NOT EXISTS 'airflow'@'%' IDENTIFIED BY 'airflow';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airflow'@'%';

-- Also grant access to root user from any host (for Docker)
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'root'@'%';
FLUSH PRIVILEGES;

-- Create a sample table to verify setup (optional)
CREATE TABLE IF NOT EXISTS setup_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO setup_status (message) VALUES ('MySQL database initialized for Airflow and Bentley Bot');

-- Show current status
SELECT 'mansa_bot database is ready!' AS status;
SELECT * FROM setup_status;