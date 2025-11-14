-- MySQL Setup for Airflow - Using Existing Bentley_Bot Database
-- Run these commands in your MySQL client (e.g., MySQL Workbench, phpMyAdmin, or mysql CLI)

-- 1. Verify your existing database
SHOW DATABASES LIKE 'Bentley_Bot';

-- 2. Use your existing database
USE Bentley_Bot;

-- 3. Show existing schemas/tables (optional - to see what's already there)
SHOW TABLES;

-- 4. Create airflow user (optional - you can use your existing user)
-- DROP USER IF EXISTS 'airflow'@'localhost';
-- CREATE USER 'airflow'@'localhost' IDENTIFIED BY 'airflow123';

-- 5. Grant privileges to airflow user on your existing database
-- GRANT ALL PRIVILEGES ON Bentley_Bot.* TO 'airflow'@'localhost';
-- FLUSH PRIVILEGES;

-- 6. Verify database access
SELECT 'Bentley_Bot database is ready for Airflow!' AS status;

-- 7. Check if mansa_bot schema/tables exist
SHOW TABLES LIKE '%mansa%';

-- Note: Airflow will create its own tables (prefixed with 'airflow_') in this database
-- Your existing mansa_bot schema tables will remain untouched